from celery import shared_task
import requests
from datetime import datetime
from backend.adams_square import Jerusalem
from backend.models import TaskProgress
from square.models import Fixture, ResultDate
import time
import logging
from backend.grace_isha import analyze_data
from square.models import Match, Fixture, FootballPrediction


logger = logging.getLogger(__name__)


today_date_for_res = datetime.utcnow().strftime("%Y-%m-%d")


@shared_task
def update_matches_task():
    matches = Match.objects.filter(updated=False)
    fixtures = Fixture.objects.filter(status_short="FT")

    fixture_map = {fixture.fixture_id: fixture for fixture in fixtures}

    for match in matches:
        if match.match_id in fixture_map:
            fixture = fixture_map[match.match_id]

            football_prediction = FootballPrediction.objects.filter(match=match).first()
            if football_prediction:
                football_prediction.home_team_goals = fixture.score_fulltime_home
                football_prediction.away_team_goals = fixture.score_fulltime_away
                football_prediction.save()

            match.updated = True
            match.save()


def fetch_fixtures_res(date):
    # Set your API key here
    api_key = "996c177462abec830c211f413c3bdaa8"

    # Define the endpoint and parameters
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "v3.football.api-sports.io",
    }
    params = {"date": date}

    # Make the request
    response = requests.get(url, headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        fixtures = response.json().get("response", [])

    else:
        fixtures = []
        print(f"Error: {response.status_code}, {response.text}")

    return fixtures


def save_fixtures_to_db(res_data):
    data = res_data

    for fixture in data:
        # Check if a ResultDate exists or create it
        result_date, created = ResultDate.objects.get_or_create(
            date=datetime.fromisoformat(
                fixture["fixture"]["date"].replace("Z", "")  # Convert to datetime
            ).date()  # Only save the date part in ResultDate
        )

        fulltime_home = fixture["score"]["fulltime"].get("home", None)
        fulltime_away = fixture["score"]["fulltime"].get("away", None)

        # Create or update the Fixture record with the associated result_date
        Fixture.objects.update_or_create(
            fixture_id=fixture["fixture"]["id"],
            defaults={
                "fixture_date": datetime.fromisoformat(
                    fixture["fixture"]["date"].replace("Z", "")
                ),  # Full datetime for fixture_date
                "status_short": fixture["fixture"]["status"]["short"],
                "team_home": fixture["teams"]["home"]["name"],
                "team_away": fixture["teams"]["away"]["name"],
                "score_fulltime_home": fulltime_home,  # Can be None
                "score_fulltime_away": fulltime_away,  # Can be None
                "result_date": result_date,  # Associate fixture with result_date
            },
        )

    print("Fixtures saved or updated successfully!")


@shared_task
def run_fixtures_update():
    res_data = fetch_fixtures_res(
        today_date_for_res
    )  # Provide the correct JSON file path
    save_fixtures_to_db(res_data)


@shared_task(bind=True)
def fetch_data_for_matches(self, matches):
    """Fetches data for matches, tracks progress, and calculates successful and failed tasks."""
    total_matches = len(matches)
    if total_matches == 0:
        logger.warning("No matches to process.")
        return {"status": "No matches", "result": "No data was processed"}

    logger.info(f"Total matches to process: {total_matches}")

    success_count = 0  # Counter for successful tasks
    failure_count = 0  # Counter for failed tasks

    for idx, match in enumerate(matches):
        logger.info(f"Processing match {idx + 1} of {total_matches}")

        # Fetch data for the match
        jerusalem = Jerusalem()
        every_data = jerusalem.receive_match(match)

        # Analyze the fetched data
        result = analyze_fetched_data(every_data)

        # Update success or failure count based on the result
        if result:
            success_count += 1
        else:
            failure_count += 1

        # Calculate and update progress
        progress = (idx + 1) / total_matches * 100
        TaskProgress.objects.update_or_create(
            task_id=self.request.id,
            defaults={
                "progress": progress,
                "successful": success_count,
                "failed": failure_count,
                "total": total_matches,
            },
        )

        # Update task state with progress for frontend tracking
        self.update_state(
            state="PROGRESS",
            meta={
                "current": idx + 1,
                "total": total_matches,
                "progress": progress,
                "successful": success_count,
                "failed": failure_count,
            },
        )

        if (idx + 1) % 5 == 0:
            logger.info("Reached 10 requests, pausing for 60 seconds...")
            time.sleep(62)
    logger.info("Task completed")
    return {
        "status": "Task completed",
        "result": {
            "total_matches": total_matches,
            "successful": success_count,
            "failed": failure_count,
        },
    }


def analyze_fetched_data(every_data):
    """Analyzes a single unit of data and returns True for success, False for failure."""
    try:
        logger.info("Starting analysis for the provided data.")

        # Analyze the data using an external function
        analyzer = analyze_data()
        fin = analyzer.save_every_data(every_data)

        logger.info("Data analysis successful.")
        return fin
    except Exception as e:
        logger.error(f"Data analysis failed: {e}")
        return False
