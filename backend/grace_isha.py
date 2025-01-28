import json
import logging
import time
from square.models import Match, Sport
from django.utils.dateparse import parse_datetime
from django.db import IntegrityError
from .models import League, MatchDate
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class analyze_data:
    def __init__(self):
        # Initialize an empty dictionary to hold the data
        self.data_store = {}

    def save_every_data(self, data):
        print("waiting for 15 minutes to see if data coection sti goes on")

        """Save the received data for further analysis."""
        self.data_store = data  # Store the data
        print("Data has been saved for analysis.")
        self.save_every_data_to_file()
        self.save_to_database()
        return True

    def save_to_database(self):
        try:
            match_details = self.data_store.get("match_details", {})
            weather = self.data_store.get("weather", {})
            if not match_details:
                print("No match details available to save.")
                return False

            sport, created = Sport.objects.get_or_create(name="Soccer")

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
            print(f"Match saved successfully: {match.home_team} vs {match.away_team}")
            return True
        except IntegrityError as e:
            print(f"IntegrityError: {e}")
            return False
        except Exception as e:
            print(f"Error saving match to database: {e}")
            return False

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
