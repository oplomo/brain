import json
import logging
import time
from square.models import Match, Sport, MatchPredictionBase, FootballPrediction
from django.utils.dateparse import parse_datetime
from django.db import IntegrityError
from .models import League, MatchDate
from datetime import datetime
from django.db import transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class analyze_data:
    def __init__(self):
        # Initialize an empty dictionary to hold the data
        self.data_store = {}
        # Fields from MatchPredictionBase

        self.match = None
        self.win_probability_team_1 = 46
        self.home_team_expected_goals = 2
        self.away_team_expected_goals = 1
        self.win_probability_team_2 = 34
        self.win_probability_draw = 20
        self.team_1_win_odds = 2.43
        self.team_2_win_odds = 3.02
        self.draw_odds = 3.22

        # Initialize variables for all fields in FootballPrediction

        # GG-related fields
        self.gg_probability = None
        self.gg_odds = None
        self.no_gg_probability = None
        self.no_gg_odds = None

        # Over/Under 1.5 Goals
        self.over_1_5_probability = None
        self.over_1_5_odds = None
        self.under_1_5_probability = None
        self.under_1_5_odds = None

        # Over/Under 2.5 Goals
        self.over_2_5_probability = None
        self.over_2_5_odds = None
        self.under_2_5_probability = None
        self.under_2_5_odds = None

        # Over/Under 3.5 Goals
        self.over_3_5_probability = None
        self.over_3_5_odds = None
        self.under_3_5_probability = None
        self.under_3_5_odds = None

        # Over/Under 4.5 Goals
        self.over_4_5_probability = None
        self.over_4_5_odds = None
        self.under_4_5_probability = None
        self.under_4_5_odds = None

        # Over/Under 5.5 Goals
        self.over_5_5_probability = None
        self.over_5_5_odds = None
        self.under_5_5_probability = None
        self.under_5_5_odds = None

        # Total Corners
        self.total_corners = None
        self.total_corners_probability = None
        self.total_corners_odds = None

        # Total Cards
        self.total_cards = None
        self.total_cards_probability = None
        self.total_cards_odds = None

        # Double Chance (DC) fields
        self.dc12_probability = None
        self.dc12_normalized_probability = None
        self.dc12_odds = None

        self.dc1x_probability = None
        self.dc1x_normalized_probability = None
        self.dc1x_odds = None

        self.dcx2_probability = None
        self.dcx2_normalized_probability = None
        self.dcx2_odds = None

        # Correct Score and Goals
        self.home_team_goals = None
        self.away_team_goals = None
        self.correct_score_odds = None

    def save_every_data(self, data):
        print("waiting for 15 minutes to see if data coection sti goes on")

        """Save the received data for further analysis."""
        self.data_store = data  # Store the data
        print("Data has been saved for analysis.")
        self.save_every_data_to_file()
        self.save_to_database()
        print(
            "WE ARE NOW SAVING INTO THE FRONTEND DATABASE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        )
        self.save_football_prediction()
        return True

    def save_to_database(self):
        try:
            match_details = self.data_store.get("match_details", {})
            weather = self.data_store.get("weather", {})
            if not match_details:
                print("No match details available to save.")
                return False

            sport, created = Sport.objects.get_or_create(name="soccer")

            match_date_str = match_details.get("match_date")
            print(f"Raw match date: {match_date_str}")
            if match_date_str:
                # Normalize "a.m." and "p.m." to "AM" and "PM"
                normalized_date_str = match_date_str.replace("a.m.", "AM").replace(
                    "p.m.", "PM"
                )

                # Handle 'midnight' and convert it to '12:00 AM' (start of the day)
                if "midnight" in normalized_date_str.lower():
                    normalized_date_str = normalized_date_str.replace(
                        "midnight", "12:00 AM"
                    )

                # Handle 'noon' and convert it to '12:00 PM' (midday)
                if "noon" in normalized_date_str.lower():
                    normalized_date_str = normalized_date_str.replace(
                        "noon", "12:00 PM"
                    )

                try:
                    # Determine format based on the presence of ':'
                    if ":" in normalized_date_str:
                        # Format includes minutes
                        match_date = datetime.strptime(
                            normalized_date_str, "%b. %d, %Y, %I:%M %p"
                        )
                    else:
                        # Format does not include minutes
                        match_date = datetime.strptime(
                            normalized_date_str, "%b. %d, %Y, %I %p"
                        )

                    print(f"Parsed match date: {match_date}")
                except ValueError as e:
                    print(f"Error parsing match date: {e}")
                    return False
            else:
                print("No match date available.")
                return False

            match_date_obj, created = MatchDate.objects.get_or_create(date=match_date)

            league, created = League.objects.get_or_create(
                league_id=match_details["league_id"]
            )

            match = Match.objects.create(
                sport=sport,
                match_id=match_details.get("match_id"),
                match_date=match_date_obj,
                venue_name=match_details.get("venue"),
                venue_city=match_details.get("city"),
                home_team=match_details.get("home_team_name"),
                home_team_logo=match_details.get("home_team_logo"),
                home_team_id=match_details.get("home_team_id"),
                away_team=match_details.get("away_team_name"),
                away_team_logo=match_details.get("away_team_logo"),
                away_team_id=match_details.get("away_team_id"),
                league=league,
                date=match_date,
                temperature=weather.get("temperature"),
                feels_like=weather.get("feels_like"),
                humidity=weather.get("humidity"),
                weather_description=weather.get("weather_description"),
                wind_speed=weather.get("wind_speed"),
                rain=weather.get("rain", 0),
            )
            self.match = match_details.get("match_id")
            print(f"Match saved successfully: {match.home_team} vs {match.away_team}")
            return True
        except IntegrityError as e:
            print(f"IntegrityError: {e}")
            return False
        except Exception as e:
            print(f"Error saving match to database: {e}")
            return False

    def save_football_prediction(self):
        try:
            match_instance = Match.objects.get(
                match_id=self.match
            )  # Assuming `self.match` is an ID
        except Match.DoesNotExist:
            print(f"Match with ID {self.match} does not exist.")
            return None
        try:
            # Start a database transaction
            with transaction.atomic():
                football_prediction, created = FootballPrediction.objects.get_or_create(
                    match=match_instance,
                    home_team_win_probability=self.win_probability_team_1,
                    away_team_win_probability=self.win_probability_team_2,
                    draw_probability=self.win_probability_draw,
                    home_team_win_odds=self.team_1_win_odds,
                    away_team_win_odds=self.team_2_win_odds,
                    draw_odds=self.draw_odds,
                    gg_probability=self.gg_probability,
                    gg_odds=self.gg_odds,
                    no_gg_probability=self.no_gg_probability,
                    no_gg_odds=self.no_gg_odds,
                    over_1_5_probability=self.over_1_5_probability,
                    over_1_5_odds=self.over_1_5_odds,
                    under_1_5_probability=self.under_1_5_probability,
                    under_1_5_odds=self.under_1_5_odds,
                    over_2_5_probability=self.over_2_5_probability,
                    over_2_5_odds=self.over_2_5_odds,
                    under_2_5_probability=self.under_2_5_probability,
                    under_2_5_odds=self.under_2_5_odds,
                    over_3_5_probability=self.over_3_5_probability,
                    over_3_5_odds=self.over_3_5_odds,
                    under_3_5_probability=self.under_3_5_probability,
                    under_3_5_odds=self.under_3_5_odds,
                    over_4_5_probability=self.over_4_5_probability,
                    over_4_5_odds=self.over_4_5_odds,
                    under_4_5_probability=self.under_4_5_probability,
                    under_4_5_odds=self.under_4_5_odds,
                    over_5_5_probability=self.over_5_5_probability,
                    over_5_5_odds=self.over_5_5_odds,
                    under_5_5_probability=self.under_5_5_probability,
                    under_5_5_odds=self.under_5_5_odds,
                    total_corners=self.total_corners,
                    total_corners_probability=self.total_corners_probability,
                    total_corners_odds=self.total_corners_odds,
                    total_cards=self.total_cards,
                    total_cards_probability=self.total_cards_probability,
                    total_cards_odds=self.total_cards_odds,
                    dc12_probability=self.dc12_probability,
                    dc12_normalized_probability=self.dc12_normalized_probability,
                    dc12_odds=self.dc12_odds,
                    dc1x_probability=self.dc1x_probability,
                    dc1x_normalized_probability=self.dc1x_normalized_probability,
                    dc1x_odds=self.dc1x_odds,
                    dcx2_probability=self.dcx2_probability,
                    dcx2_normalized_probability=self.dcx2_normalized_probability,
                    dcx2_odds=self.dcx2_odds,
                    home_team_goals=self.home_team_goals,
                    away_team_goals=self.away_team_goals,
                    correct_score_odds=self.correct_score_odds,
                )
                print(
                    "FootballPrediction saved successfully!@@@@@@@@@@@@@@@@@@@@@@@@@@@!!!!!!!!!@@@@@@@@@@@@@@@!!!!!!!!!!!!!!!!"
                )
        except Exception as e:
            print(f"An error occurred while saving the football prediction: {e}")

        print(
            "FootballPrediction saved successfully..................................|||||>>>>>>>>>>|"
        )

    def save_every_data_to_file(self):

        # filename = f"{self.home_team_name} vs {self.away_team_name} every_data.json"
        name = self.data_store["match_details"]["home_team_name"]
        filename = f"{name}.json"
        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(self.data_store, file, indent=4)
            logger.info(f"EVERY Data successfully written to {filename}")
        except Exception as e:
            logger.error(f"Error writing to file {filename}: {e}")
