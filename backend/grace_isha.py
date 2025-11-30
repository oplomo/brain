import json
import logging
import time
from square.models import Match, Sport, MatchPredictionBase, FootballPrediction
from django.utils.dateparse import parse_datetime
from django.db import IntegrityError
from .models import League, MatchDate
from datetime import datetime
from django.db import transaction
import math
import numpy as np
import os
import random
from rich.console import Console
from rich.progress import track
from rich.text import Text
from termcolor import colored
import pyfiglet
from django.conf import settings


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
        self.is_premium = {}
        self.premium_part = None

        self.match = None
        self.win_probability_team_1 = None
        self.home_team_expected_goals = None
        self.away_team_expected_goals = None
        self.win_probability_team_2 = None
        self.win_probability_draw = None
        self.team_1_win_odds = None
        self.team_2_win_odds = None
        self.draw_odds = None

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

    def save_every_data(self, data):
        success = True
        self.data_store = data  # Store the data
        # try:
        #     self.save_every_data_to_file()
        # except Exception as e:
        #     print(f"Error in saving to a json file: {e}")
        try:
            self.asign_odds()
            print("Odds have been assigned")
        except Exception as e:
            print(f"Error in asign_odds: {e}")
        # Ensure both functions execute even if one fails
        try:
            odds_prediction = self.predict_based_on_odds()
        except Exception as e:
            print(f"Error in predict_based_on_odds: {e}")
            odds_prediction = None  # Assign None if the function fails

        try:
            api_prediction = self.predict_based_api_predictions()
        except Exception as e:
            print(f"Error in predict_based_api_predictions: {e}")
            api_prediction = None  # Assign None if the function fails

        try:
            self.save_to_self(odds_prediction, api_prediction)
        except Exception as e:
            print(f"Error in save_to_self: {e}")

        try:
            self.save_to_database()
        except Exception as e:
            print(f"Error in save_to_database: {e}")

        try:
            success = self.save_football_prediction()
            if success:
                print(
                    "FootballPrediction saved successfully!@@@@@@@@@@@@@@@@@@@@@@@@@@@!!!!!!!!!@@@@@@@@@@@@@@@!!!!!!!!!!!!!!!!"
                )
            return success
        except Exception as e:
            print(f"Error in save_football_prediction: {e}")
            return False

    def save_to_database(self):
        deal = False
        gold = "N/A"
        if self.is_premium:
            deal = True
            gold = self.is_premium["where"]
        try:
            match_details = self.data_store.get("match_details", {})
            weather = self.data_store.get("weather") or {}
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
                    # Handle abbreviated month names with periods (Nov., Dec., etc.)
                    normalized_date_str = normalized_date_str.replace("Jan.", "January").replace("Feb.", "February").replace("Mar.", "March").replace("Apr.", "April").replace("May.", "May").replace("Jun.", "June").replace("Jul.", "July").replace("Aug.", "August").replace("Sep.", "September").replace("Oct.", "October").replace("Nov.", "November").replace("Dec.", "December")

                    # Determine format based on the presence of ':'
                    if ":" in normalized_date_str:
                        # Format includes minutes
                        match_date = datetime.strptime(
                            normalized_date_str, "%B %d, %Y, %I:%M %p"
                        )
                    else:
                        # Format does not include minutes
                        match_date = datetime.strptime(
                            normalized_date_str, "%B %d, %Y, %I %p"
                        )

                    print(f"Parsed match date: {match_date}")
                except ValueError as e:
                    print(f"Error parsing match date: {e}")
                    # Fallback: try parsing with dateutil if available
                    try:
                        from dateutil import parser
                        match_date = parser.parse(match_date_str)
                        print(f"Fallback parsing successful: {match_date}")
                    except:
                        print("All date parsing methods failed")
                        return False
            else:
                print("No match date available.")
                return False

            match_date_obj, created = MatchDate.objects.get_or_create(date=match_date.date())

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
                is_premium=deal,
                gold_bar=gold,
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
            
            
            print(f"Match saved successfully: {match.home_team} vs {match.away_team})")
            return True
        except IntegrityError as e:
            print(f"IntegrityError: {e}")
            return False
        except Exception as e:
            print(f"Error saving match to database: {e}")
            return False
        
    def asign_odds(self):
        bookmakers = [
            "Bet365",
            "NordicBet",
            "Marathonbet",
            "William Hill",
            "10Bet",
            "Dafabet",
            "1xBet",
            "Unibet",
            "Betfair",
            "Tipico",
            "Betano",
            "SBO",
            "Pinnacle",
            "Betsson",
        ]

        try:
            s = self.data_store.get("odds") or {}
            source = {}

            # ✅ Check if the bookmaker exists in the dictionary keys
            for bookmaker in bookmakers:
                if bookmaker in s:
                    source = s[bookmaker]
                    break
            match_winner_odds = source.get("Match Winner") or []

            # Handle Match Winner Odds
            if isinstance(match_winner_odds, list) and len(match_winner_odds) >= 3:
                self.team_1_win_odds = float(match_winner_odds[0].get("odd", 0) or 0)
                self.draw_odds = float(match_winner_odds[1].get("odd", 0) or 0)
                self.team_2_win_odds = float(match_winner_odds[2].get("odd", 0) or 0)
            else:
                self.team_1_win_odds = self.draw_odds = self.team_2_win_odds = None

            # Handle Goals Over/Under Odds
            goals_odds = source.get("Goals Over/Under") or []
            target_values = {
                "Over 1.5",
                "Under 1.5",
                "Over 2.5",
                "Under 2.5",
                "Over 3.5",
                "Under 3.5",
                "Over 4.5",
                "Under 4.5",
                "Over 5.5",
                "Under 5.5",
            }
            over_under_odds = {key: None for key in target_values}

            for entry in goals_odds:
                if isinstance(entry, dict):
                    value = entry.get("value")
                    odd = entry.get("odd")
                    if value in target_values and odd is not None:
                        over_under_odds[value] = float(odd)

            self.over_1_5_odds = over_under_odds["Over 1.5"]
            self.under_1_5_odds = over_under_odds["Under 1.5"]
            self.over_2_5_odds = over_under_odds["Over 2.5"]
            self.under_2_5_odds = over_under_odds["Under 2.5"]
            self.over_3_5_odds = over_under_odds["Over 3.5"]
            self.under_3_5_odds = over_under_odds["Under 3.5"]
            self.over_4_5_odds = over_under_odds["Over 4.5"]
            self.under_4_5_odds = over_under_odds["Under 4.5"]
            self.over_5_5_odds = over_under_odds["Over 5.5"]
            self.under_5_5_odds = over_under_odds["Under 5.5"]

            # Handle Both Teams to Score Odds
            bts_odds = source.get("Both Teams Score") or []
            self.gg_odds = self.no_gg_odds = None
            for entry in bts_odds:
                if isinstance(entry, dict):
                    value = entry.get("value")
                    odd = entry.get("odd")
                    if value == "Yes" and odd is not None:
                        self.gg_odds = float(odd)
                    elif value == "No" and odd is not None:
                        self.no_gg_odds = float(odd)

            # Handle Double Chance Odds
            double_chance_odds = source.get("Double Chance") or []
            self.dc1x_odds = self.dc12_odds = self.dcx2_odds = None
            for entry in double_chance_odds:
                if isinstance(entry, dict):
                    value = entry.get("value")
                    odd = entry.get("odd")
                    if value == "Home/Draw" and odd is not None:
                        self.dc1x_odds = float(odd)
                    elif value == "Home/Away" and odd is not None:
                        self.dc12_odds = float(odd)
                    elif value == "Draw/Away" and odd is not None:
                        self.dcx2_odds = float(odd)

        except Exception as e:
            print(f"An error occurred: {e}")
            # Optionally reset all attributes to None if a critical error occurs
            self.team_1_win_odds = self.draw_odds = self.team_2_win_odds = None
            self.over_1_5_odds = self.under_1_5_odds = None
            self.over_2_5_odds = self.under_2_5_odds = None
            self.over_3_5_odds = self.under_3_5_odds = None
            self.over_4_5_odds = self.under_4_5_odds = None
            self.over_5_5_odds = self.under_5_5_odds = None
            self.gg_odds = self.no_gg_odds = None
            self.dc1x_odds = self.dc12_odds = self.dcx2_odds = None

    def save_football_prediction(self):
        try:
            match_instance = Match.objects.get(
                match_id=self.data_store.get("match_details", {}).get("match_id")
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
                    home_team_expected_goals=self.home_team_expected_goals,
                    away_team_win_probability=self.win_probability_team_2,
                    away_team_expected_goals=self.away_team_expected_goals,
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
                    # home_team_goals=self.home_team_goals,
                    # away_team_goals=self.away_team_goals,
                    # correct_score_odds=self.correct_score_odds,
                )

            return True
        except Exception as e:
            print(f"An error occurred while saving the football prediction: {e}")
            return False

    def save_every_data_to_file(self):
        # Define the folder path
        import os

        try:
            folder_name = "json_store"

            # Ensure the folder exists
            try:
                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)
            except OSError as e:
                print(f"Error creating folder '{folder_name}': {e}")

            # Generate filename
            try:
                name = self.data_store["match_details"]["home_team_name"]
                filename = f"{name}.json"
            except KeyError as e:
                print(f"Key error while accessing match details: {e}")
                filename = "default.json"  # Fallback filename
            except Exception as e:
                print(f"Unexpected error while generating filename: {e}")
                filename = "default.json"

            # Full file path inside json_store folder
            try:
                file_path = os.path.join(folder_name, filename)
            except Exception as e:
                print(f"Error creating file path: {e}")
                file_path = os.path.join(folder_name, "default.json")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(self.data_store, file, indent=4)
            logger.info(f"EVERY Data successfully written to {file_path}")
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {e}")

    def custom_round(self, number):
        """Rounds numbers: below .5 rounds down, .5 and above rounds up."""
        try:
            if not isinstance(number, (int, float)):
                raise TypeError(
                    f"Invalid type for number: {type(number)}. Expected int or float."
                )
            return math.floor(number) if number % 1 < 0.5 else math.ceil(number)
        except Exception as e:
            print(f"Error in custom_round: {e}")
            return None  # Return None if an error occurs

    def truncate(self, number, decimals=2):
        """Truncates a number to a fixed number of decimal places without rounding."""
        try:
            if not isinstance(number, (int, float)):
                raise TypeError(
                    f"Invalid type for number: {type(number)}. Expected int or float."
                )
            factor = 10**decimals
            return math.floor(number * factor) / factor
        except Exception as e:
            print(f"Error in truncate: {e}")
            return None  # Return None if an error occurs

    def calculate_goal_percentages(self, expected_goals_team1, expected_goals_team2):
        # Define thresholds

        try:
            thresholds = [1.5, 2.5, 3.5, 4.5, 5.5]

            # Calculate total expected goals
            try:
                total_expected_goals = abs(
                    self.custom_round(expected_goals_team1)
                ) + abs(self.custom_round(expected_goals_team2))
            except TypeError as e:
                print(f"Type error in calculating total expected goals: {e}")
                total_expected_goals = 0
            except AttributeError as e:
                print(f"Attribute error (possibly missing custom_round method): {e}")
                total_expected_goals = 0
            except Exception as e:
                print(f"Unexpected error in total expected goals calculation: {e}")
                total_expected_goals = 0

            # Store probabilities
            probabilities = {}

            # Map difference to probability using a function
            def exponential_mapping(diff, alpha=0.1, max_value=30):
                """Maps difference (0-20) to probability (0-100%) using exponential growth."""
                try:
                    if not isinstance(diff, (int, float)):
                        raise TypeError(
                            f"Invalid type for diff: {type(diff)}. Expected int or float."
                        )
                    if not isinstance(alpha, (int, float)):
                        raise TypeError(
                            f"Invalid type for alpha: {type(alpha)}. Expected int or float."
                        )
                    if not isinstance(max_value, (int, float)):
                        raise TypeError(
                            f"Invalid type for max_value: {type(max_value)}. Expected int or float."
                        )

                    diff = abs(diff)
                    if diff < 0:
                        return 0  # No negative values
                    if diff > max_value:
                        diff = max_value  # Cap at max_value
                    return round(100 * (1 - math.exp(-alpha * diff)), 2)
                except Exception as e:
                    print(f"Error in exponential_mapping: {e}")
                    return 0  # Return 0% if an error occurs

        except Exception as e:
            print(f"An unexpected error occurred in the main block: {e}")

        def gg_prob(expected_goals_team1, expected_goals_team2):
            home_ex = self.truncate(expected_goals_team1) - 0.5
            away_ex = self.truncate((expected_goals_team2)) - 0.5
            alpha = 0.06
            gg = {}

            # Compute probabilities using exponential mapping
            home_prob = exponential_mapping(abs(home_ex), alpha)
            away_prob = exponential_mapping(abs(away_ex), alpha)

            # Adjust probabilities based on whether values were negative
            if home_ex < 0:
                home_prob = -home_prob
            if away_ex < 0:
                away_prob = -away_prob

            # Calculate "Both Teams to Score" (BTS) and "No BTS"
            if home_prob >= 0 and away_prob >= 0:
                bts = 50 + ((home_prob + away_prob))
            else:
                bts = 50 - abs((home_prob + away_prob))

            no_bts = 100 - bts

            # Store and return rounded results
            gg["bts"] = bts
            gg["no_bts"] = no_bts

            return gg

        bts = gg_prob(expected_goals_team1, expected_goals_team2)
        # Calculate for each threshold
        for threshold in thresholds:
            diff = total_expected_goals - threshold
            if diff >= 0:
                probabilities[f"Over {threshold}"] = exponential_mapping(diff) + 50
                probabilities[f"Under {threshold}"] = (
                    100 - probabilities[f"Over {threshold}"]
                )
            else:
                probabilities[f"Over {threshold}"] = 50 - (
                    abs(exponential_mapping(diff))
                )
                probabilities[f"Under {threshold}"] = (
                    100 - probabilities[f"Over {threshold}"]
                )
        probabilities["bts"] = bts
        return probabilities

    def generate_three_way_prob(self, home_expected_g, away_expected_g):
        three_way = {}

        def custom_mapping(value):
            """Maps values and returns corresponding percentage."""
            if value <= 0:
                mapped_value = 0.49
            elif 0 < value <= 0.9:
                mapped_value = round(0.49 - (0.39 * value / 0.9), 8)
            elif 1 <= value <= 3.5:
                mapped_value = round(-0.1 - ((0.39 * (value - 1)) / (3.5 - 1)), 8)
            else:
                mapped_value = -0.49

            # Convert mapped_value to percentage
            percentage = round((51.28205128 * mapped_value) - 3.128205128, 2)
            return percentage

        def custom_round(number):
            """Rounds numbers: below .5 rounds down, .5 and above rounds up."""
            return math.floor(number) if number % 1 < 0.5 else math.ceil(number)

        def subtract_bigger_from_smaller(a, b):
            """
            Rounds 'a' and 'b' first. If they round to the same number, negate the difference.
            Otherwise, subtract the bigger from the smaller and return the absolute value.
            """
            a_rounded = custom_round(a)
            b_rounded = custom_round(b)

            if a_rounded != b_rounded:
                # Negate the difference if the rounded values are the same
                res = 1 + abs(min(a, b) - max(a, b))
            else:
                res = min(a, b) - max(a, b)

            res = abs(res)
            return res

        def calculate_percentages(h_ratio, a_ratio):
            # Step 1: Calculate H and A based on ratios
            H = h_ratio
            A = a_ratio

            # Step 2: Compute D based on some_function()
            func_value = custom_mapping(subtract_bigger_from_smaller(h_ratio, a_ratio))
            if func_value >= 0:
                D = max(H, A) + ((max(H, A) * func_value / 100) * 4)
            else:
                D = (H + A) / 2 - (abs(func_value / 100) * 4)
                if D < 0:
                    D = 0.3  # Set to 0.3 if negative

            # Step 3: Normalize so that H + D + A = 100%
            total = H + D + A
            H_percent = round((H / total) * 100)
            D_percent = round((D / total) * 100)
            A_percent = round((A / total) * 100)

            # Ensure they sum to 100
            diff = 100 - (H_percent + D_percent + A_percent)
            if diff != 0:
                # Adjust the one with the largest decimal before rounding
                decimals = {
                    "H": (H / total) * 100 - math.floor((H / total) * 100),
                    "D": (D / total) * 100 - math.floor((D / total) * 100),
                    "A": (A / total) * 100 - math.floor((A / total) * 100),
                }
                # Sort by largest decimal for adjustment
                for key, _ in sorted(
                    decimals.items(), key=lambda x: x[1], reverse=(diff > 0)
                ):
                    if diff == 0:
                        break
                    if key == "H":
                        H_percent += diff
                    elif key == "D":
                        D_percent += diff
                    else:
                        A_percent += diff
                    diff = 100 - (H_percent + D_percent + A_percent)

            # Ensure no two values are equal
            percentages = [("H", H_percent), ("D", D_percent), ("A", A_percent)]
            values = [H_percent, D_percent, A_percent]
            duplicates = True

            while duplicates:
                duplicates = False
                seen = set()
                for i in range(len(values)):
                    if values[i] in seen:
                        duplicates = True
                        # Adjust by +1 or -1 ensuring total still 100
                        adjust_index = random.choice(
                            [j for j in range(len(values)) if j != i]
                        )
                        if values[i] < 100:
                            values[i] += 1
                            values[adjust_index] -= 1
                    seen.add(values[i])
            H_percent, D_percent, A_percent = values

            return H_percent, D_percent, A_percent

        H_percent, D_percent, A_percent = calculate_percentages(
            home_expected_g, away_expected_g
        )
        three_way["home"] = H_percent
        three_way["draw"] = D_percent
        three_way["away"] = A_percent
        return three_way

    def predict_based_on_odds(self):
        expected_home_goals = []
        expected_away_goals = []

        def get_available_odds():

            bookmakers = [
                "Bet365",
                "NordicBet",
                "Marathonbet",
                "William Hill",
                "10Bet",
                "Dafabet",
                "1xBet",
                "Unibet",
                "Betfair",
                "Tipico",
                "Betano",
                "SBO",
                "Pinnacle",
                "Betsson",
            ]

            for bookmaker in bookmakers:
                odds_dict = self.data_store.get("odds", {}).get(bookmaker, {})
                if odds_dict:  # If odds are found, return them immediately
                    print(f"Odds found in {bookmaker}")
                    return odds_dict

            print("No odds found in the available bookmakers.")
            return {}  # Return empty dictionary if no odds are found

        # Example usage
        odds_dict = get_available_odds()

        def calculate_implied_probabilities(odds_dict):
            results = {}

            if not isinstance(odds_dict, dict):
                return results

            for category, bets in odds_dict.items():
                if not isinstance(bets, list):
                    continue

                implied_probs = {}
                total_implied = 0

                for bet in bets:
                    if (
                        not isinstance(bet, dict)
                        or "value" not in bet
                        or "odd" not in bet
                    ):
                        continue

                    try:
                        implied_prob = (1 / float(bet["odd"])) * 100
                        implied_probs[bet["value"]] = implied_prob
                        total_implied += implied_prob
                    except (ValueError, ZeroDivisionError, TypeError):
                        continue

                if total_implied > 0:
                    adjusted_probs = {
                        value: (prob / total_implied) * 100
                        for value, prob in implied_probs.items()
                    }
                    results[category] = adjusted_probs

            return results

        adjusted_probabilities = calculate_implied_probabilities(odds_dict)

        def custom_round(number):
            """Rounds numbers: below .5 rounds down, .5 and above rounds up."""
            return math.floor(number) if number % 1 < 0.5 else math.ceil(number)

        def find_best_threshold(results, key):
            # Extract the specified dictionary from results

            data = results.get(key, {})

            # Extract unique thresholds
            thresholds = set(float(k.split()[1]) for k in data)

            # Calculate differences and find the smallest one
            smallest_difference = float("inf")
            best_threshold = None

            for threshold in thresholds:
                over_key = f"Over {threshold}"
                under_key = f"Under {threshold}"

                if over_key in data and under_key in data:
                    difference = abs(data[over_key] - data[under_key])
                    if difference < smallest_difference:
                        smallest_difference = difference
                        best_threshold = threshold
                if threshold == None:
                    continue

            # best_threshold = custom_round(best_threshold)
            best_threshold = best_threshold

            return best_threshold

        best_threshold_Goals_Over_Under = find_best_threshold(
            adjusted_probabilities, "Goals Over/Under"
        )
        best_threshold_Total_Home = find_best_threshold(
            adjusted_probabilities, "Total - Home"
        )
        best_threshold_Total_Away = find_best_threshold(
            adjusted_probabilities, "Total - Away"
        )
        best_threshold_Corners_Over_Under = find_best_threshold(
            adjusted_probabilities, "Corners Over Under"
        )
        best_threshold_cards_Yellow_Cards_Over_Under = find_best_threshold(
            adjusted_probabilities, "Cards Over/Under"
        )

        def redistribute_draw_probability(adjusted_probabilities):
            """
            Redistributes the draw probability proportionally between Team A and Team B.

            :param probabilities: Dictionary with 'team_a', 'team_b', and 'draw' probabilities.
            :return: Adjusted probabilities with no draw value.
            """
            team_a_prob = adjusted_probabilities.get("Match Winner", {}).get("Home", 0)
            team_b_prob = adjusted_probabilities.get("Match Winner", {}).get("Away", 0)
            draw_prob = adjusted_probabilities.get("Match Winner", {}).get("Draw", 0)

            total_win_prob = team_a_prob + team_b_prob

            # Avoid division by zero in case of invalid data
            if total_win_prob == 0:
                return {"team_a": team_a_prob, "team_b": team_b_prob}

            # Distribute draw probability proportionally
            team_a_new = team_a_prob + (team_a_prob / total_win_prob) * draw_prob
            team_b_new = team_b_prob + (team_b_prob / total_win_prob) * draw_prob

            return {"team_a": round(team_a_new, 2), "team_b": round(team_b_new, 2)}

        def divide_goals(redistributed_prob, expected_goals):
            """Divides expected goals between Home and Away based on given percentages."""
            home_percentage = float(redistributed_prob.get("team_a", 50))
            away_percentage = float(redistributed_prob.get("team_b", 50))

            home_goals = (home_percentage / 100) * expected_goals
            away_goals = (away_percentage / 100) * expected_goals

            return home_goals, away_goals
            # Rounding to 2 decimal places

        redistributed_prob = redistribute_draw_probability(adjusted_probabilities)

        home_goals, away_goals = divide_goals(
            redistributed_prob, best_threshold_Goals_Over_Under
        )
        expected_home_goals.append(home_goals)

        expected_away_goals.append(away_goals)

        def sort_dict_by_values(results, key):
            """Sorts the values of a given key in descending order based on percentages and divides them into home and away goals."""
            data = results.get(key, {})

            # Sort the data by percentage in descending order
            sorted_items = sorted(data.items(), key=lambda x: float(x[1]), reverse=True)

            # Calculate the boundaries for the 3 groups
            total_items = len(sorted_items)

            # Divide into 3 groups: Top 25%, 25%-50%, 50%-66%
            top_25 = sorted_items[: int(total_items * 0.25)]
            mid_25 = sorted_items[int(total_items * 0.25) : int(total_items * 0.5)]
            top_50_66 = sorted_items[int(total_items * 0.5) : int(total_items * 0.66)]

            # Create separate lists for home and away goals for each range
            top_25_home = [item[0].split(":")[0] for item in top_25]
            top_25_away = [item[0].split(":")[1] for item in top_25]

            mid_25_home = [item[0].split(":")[0] for item in mid_25]
            mid_25_away = [item[0].split(":")[1] for item in mid_25]

            top_50_66_home = [item[0].split(":")[0] for item in top_50_66]
            top_50_66_away = [item[0].split(":")[1] for item in top_50_66]

            # Return lists in pairs (home, away) for each group
            return (
                (top_25_home, top_25_away),
                (mid_25_home, mid_25_away),
                (top_50_66_home, top_50_66_away),
            )

        # Sample dictionary

        # Sorting "Exact Score" and dividing into home/away goals
        (
            (top_25_home, top_25_away),
            (mid_25_home, mid_25_away),
            (top_50_66_home, top_50_66_away),
        ) = sort_dict_by_values(adjusted_probabilities, "Exact Score")
        top_25_home = list(map(int, top_25_home))
        top_25_away = list(map(int, top_25_away))
        mid_25_home = np.array(list(map(int, mid_25_home)))
        mid_25_away = np.array(list(map(int, top_25_away)))
        top_50_66_home = list(map(int, top_50_66_home))
        top_50_66_away = list(map(int, top_50_66_away))

        expected_home_goals = expected_home_goals + top_25_home
        expected_away_goals = expected_away_goals + top_25_away

        expected_home_goals.append(np.mean(mid_25_home))
        expected_home_goals.append(np.median(mid_25_home))
        expected_home_goals.append(best_threshold_Total_Home)
        expected_away_goals.append(np.mean(mid_25_home))
        expected_away_goals.append(np.median(mid_25_away))
        expected_away_goals.append(best_threshold_Total_Away)

        home_expected_goals = np.array(expected_home_goals)
        away_expected_goals = np.array(expected_away_goals)

        filtered_home_expected_goals = [x for x in home_expected_goals if x is not None]
        filtered_away_expected_goals = [x for x in away_expected_goals if x is not None]

        home_mean = np.mean(filtered_home_expected_goals)
        away_mean = np.mean(filtered_away_expected_goals)

        home_std_deviation = np.std(filtered_home_expected_goals)
        away_std_deviation = np.std(filtered_away_expected_goals)

        yes = float(adjusted_probabilities.get("Both Teams Score", {}).get("Yes", 0))
        no = float(adjusted_probabilities.get("Both Teams Score", {}).get("No", 0))

        # change = ((custom_round(yes) - 50) / 50) * 100
        if yes > no:
            if home_mean > away_mean:
                if away_mean < 0.5:
                    away_mean = away_mean + 0.66 * away_std_deviation
            elif home_mean < away_mean:
                if home_mean < 0.5:
                    home_mean = home_mean + 0.66 * home_std_deviation
            else:
                away_mean = away_mean + 0.66 * away_std_deviation
                home_mean = home_mean + 0.66 * home_std_deviation
        elif no > yes:
            if home_mean < away_mean:
                if home_mean > 0.5:
                    home_mean = home_mean - 0.66 * home_std_deviation
            elif home_mean > away_mean:
                if away_mean > 0.5:
                    away_mean = away_mean - 0.66 * away_std_deviation
            else:
                home_mean = home_mean - 0.66 * home_std_deviation
                away_mean = away_mean - 0.66 * away_std_deviation
        else:
            pass

        def calculate_relative_probabilities(probabilities):
            relative_probs = {}  # Store the results

            if not isinstance(probabilities, dict):
                return relative_probs

            for key, value in probabilities.items():
                if not isinstance(value, (int, float)):
                    continue

                # Find the matching Under/Over key
                if "Over" in key:
                    under_key = key.replace("Over", "Under")
                elif "Under" in key:
                    over_key = key.replace("Under", "Over")
                else:
                    continue  # Skip if it doesn't match Over/Under format

                # Ensure both Over and Under values exist and are valid numbers
                if key in probabilities and (
                    (
                        under_key in probabilities
                        and isinstance(probabilities[under_key], (int, float))
                    )
                    or (
                        over_key in probabilities
                        and isinstance(probabilities[over_key], (int, float))
                    )
                ):
                    try:
                        if "Over" in key and under_key in probabilities:
                            relative_prob = (
                                value / (value + probabilities[under_key])
                            ) * 100
                            relative_probs[key] = round(relative_prob, 2)
                            relative_probs[under_key] = round(100 - relative_prob, 2)
                    except (ZeroDivisionError, TypeError):
                        continue

            return relative_probs

        # Given probabilities
        probabilities = adjusted_probabilities.get("Goals Over/Under", {})
        corner_prob = adjusted_probabilities.get("Corners Over Under", {})
        # Compute the relative probabilities
        relative_probabilities = calculate_relative_probabilities(probabilities)

        corner_probs = calculate_relative_probabilities(corner_prob)

        odds_prediction = {}

        # Check if the variables are available (not None) and assign to the dictionary
        odds_prediction["home_final_mean"] = (
            home_mean if home_mean is not None else None
        )
        odds_prediction["away_final_mean"] = (
            away_mean if away_mean is not None else None
        )
        odds_prediction["corners"] = (
            best_threshold_Corners_Over_Under
            if best_threshold_Corners_Over_Under is not None
            else None
        )
        odds_prediction["cards"] = (
            best_threshold_cards_Yellow_Cards_Over_Under
            if best_threshold_cards_Yellow_Cards_Over_Under is not None
            else None
        )

        print(
            "HURAYYYYY!!£$%^&*()!!£$%^&*()!!£$%^&*()!!£$%^&*()!!£$%^&*() tested approved and trusted"
        )
        print("prediction_based on odds are ", odds_prediction)
        return odds_prediction

    def predict_based_api_predictions(self):
        data_store = self.data_store

        def get_goal_thresholds(data_store):
            try:
                # Extract goals from the predictions list
                goals_data = (
                    data_store.get("predictions", [{}])[0]
                    .get("predictions", {})
                    .get("goals", {})
                )

                # Convert the extracted values to float with error handling
                home_goals = (
                    float(goals_data.get("home", "0"))
                    if goals_data.get("home")
                    else 0.0
                )
                away_goals = (
                    float(goals_data.get("away", "0"))
                    if goals_data.get("away")
                    else 0.0
                )

                home_mean = abs(round(home_goals))
                away_mean = abs(round(away_goals))

                return home_mean, away_mean

            except (ValueError, TypeError, IndexError, KeyError) as e:
                print(f"Error in get_goal_thresholds: {e}")
            return 0, 0  # Default safe values

        def distribute_draw_probability(data_store):
            try:
                # Extract percentage data safely
                percent_data = (
                    data_store.get("predictions", [{}])[0]
                    .get("predictions", {})
                    .get("percent", {})
                )

                # Convert percentage strings to floats safely
                home_percent = (
                    float(percent_data.get("home", "0").strip("%"))
                    if percent_data.get("home")
                    else 0.0
                )
                draw_percent = (
                    float(percent_data.get("draw", "0").strip("%"))
                    if percent_data.get("draw")
                    else 0.0
                )
                away_percent = (
                    float(percent_data.get("away", "0").strip("%"))
                    if percent_data.get("away")
                    else 0.0
                )

                # Ensure draw probability is distributed equally
                home_share = 0.5 * draw_percent
                away_share = 0.5 * draw_percent

                # Compute final adjusted probabilities
                home_final = home_percent + home_share
                away_final = away_percent + away_share

                return home_final, away_final

            except (ValueError, TypeError, IndexError, KeyError) as e:
                print(f"Error in distribute_draw_probability: {e}")
                return 0.0, 0.0  # Default safe values

        # Get goal thresholds
        home_goals, away_goals = get_goal_thresholds(data_store)

        # Get distributed probabilities
        home_portion, away_portion = distribute_draw_probability(data_store)

        # Compute expected goals
        expected_g = (home_goals + away_goals) / 2

        # Compute weighted means with error handling
        try:
            home_mean = (home_portion / 100) * expected_g
            away_mean = (away_portion / 100) * expected_g
        except ZeroDivisionError as e:
            print(f"Error in mean calculation: {e}")
            home_mean, away_mean = 0.0, 0.0

        def convert_percentage_to_float(percentage_value):
            """
            This function converts a percentage string (e.g., "50%") to a float with two decimal places.
            """
            numeric_value = float(percentage_value.strip("%"))
            formatted_value = "{:.2f}".format(numeric_value)
            return float(formatted_value)

        def comparison_center(home_mean, away_mean, data):
            home_goal_list = []
            away_goal_list = []

            teams_data = data["predictions"][0]["teams"]
            home_team = teams_data["home"]
            away_team = teams_data["away"]

            # Extract key data for iteration
            home_last5 = home_team["last_5"]
            away_last5 = away_team["last_5"]

            # Initialize empty dictionaries
            home_last_5 = {}
            away_last_5 = {}

            home_league_data = {}
            away_league_data = {}
            # Populate the dictionaries
            for (home_key, home_value), (_, away_value) in zip(
                home_last5.items(), away_last5.items()
            ):
                home_last_5[home_key] = home_value
                away_last_5[home_key] = (
                    away_value  # Using home_key since both have the same keys
                )

            # Now extract values safely after iteration
            try:
                home_played = home_last_5["played"]
                home_form = home_last_5["form"]
                home_att = home_last_5["att"]
                home_def = home_last_5["def"]
                home_goals_for_total = home_last_5["goals"]["for"]["total"]
                home_goals_for_average = home_last_5["goals"]["for"]["average"]
                home_goals_against_total = home_last_5["goals"]["against"]["total"]
                home_goals_against_average = home_last_5["goals"]["against"]["average"]

                away_played = away_last_5["played"]
                away_form = away_last_5["form"]
                away_att = away_last_5["att"]
                away_def = away_last_5["def"]
                away_goals_for_total = away_last_5["goals"]["for"]["total"]
                away_goals_for_average = away_last_5["goals"]["for"]["average"]
                away_goals_against_total = away_last_5["goals"]["against"]["total"]
                away_goals_against_average = away_last_5["goals"]["against"]["average"]

            except KeyError as e:
                print(f"KeyError: {e} - Some key might be missing in the data!")

            def calculate_geometric_mean_for(team_goals, opponent_conceded):
                try:
                    team_goals = float(team_goals)
                    opponent_conceded = float(opponent_conceded)
                    geometric_mean = math.sqrt(team_goals * opponent_conceded)
                    return geometric_mean
                except (ValueError, TypeError, ZeroDivisionError) as e:
                    print(f"Error in calculate_geometric_mean_for: {e}")
                    return 0  # Default value to avoid breaking the program

            try:
                ratuombi = (
                    float(home_goals_for_average)
                    + float(home_goals_against_average)
                    + float(away_goals_for_average)
                    + float(away_goals_against_average)
                ) / 2
                home_to_score = calculate_geometric_mean_for(
                    home_goals_for_average, away_goals_against_average
                )
                away_to_score = calculate_geometric_mean_for(
                    home_goals_against_average, away_goals_for_average
                )
                home_goal_list.append(float(away_goals_against_average))
                away_goal_list.append(float(home_goals_against_average))
                home_goal_list.append(home_to_score)
                home_goal_list.append(home_goals_for_average)
                away_goal_list.append(away_to_score)
                away_goal_list.append(away_goals_for_average)
            except NameError as e:
                print(f"Error while calculating goals: {e}")

            def deff_att_comparison(attack_rating, defense_rating):
                try:
                    attack_rating = convert_percentage_to_float(attack_rating)
                    defense_rating = convert_percentage_to_float(defense_rating)

                    attack_contribution = 10 * (attack_rating / 100)
                    defense_contribution = -10 * (defense_rating / 100) + 10
                    expected_goals = math.sqrt(
                        attack_contribution * defense_contribution
                    )

                    return expected_goals
                except (ValueError, TypeError, ZeroDivisionError) as e:
                    print(f"Error in deff_att_comparison: {e}")
                    return 0

            try:
                home_att_deff = math.sqrt(
                    deff_att_comparison(home_att, away_def)
                )  # newnewnew
                away_att_deff = math.sqrt(
                    deff_att_comparison(away_att, home_def)
                )  # newnewnew

                home_goal_list.append(home_att_deff)
                home_goal_list.append(
                    (convert_percentage_to_float(home_form) / 100)
                    * (home_mean + away_mean)
                )
                away_goal_list.append(away_att_deff)
                away_goal_list.append(
                    (convert_percentage_to_float(away_form) / 100)
                    * (home_mean + away_mean)
                )
            except NameError as e:
                print(f"Error while appending goals: {e}")

            def process_string(input_string):
                try:
                    upper_string = input_string.upper()
                    last_five = upper_string[-6:]
                    reversed_last_five = last_five[::-1]
                    return reversed_last_five.upper()
                except AttributeError as e:
                    print(f"Error in process_string: {e}")
                    return ""

            try:
                home_league = home_team.get("league", {})
                away_league = away_team.get("league", {})

                for (home_key, home_value), (_, away_value) in zip(
                    home_league.items(), away_league.items()
                ):
                    if home_key in [
                        "form",
                        "fixtures",
                        "biggest",
                        "clean_sheet",
                        "failed_to_score",
                    ]:
                        home_league_data[home_key] = home_value
                        away_league_data[home_key] = away_value

                    elif home_key == "goals":
                        home_league_data["goals"] = {
                            "for": home_value.get("for", {}).get("average", 0),
                            "against": home_value.get("against", {}).get("average", 0),
                        }
                        away_league_data["goals"] = {
                            "for": away_value.get("for", {}).get("average", 0),
                            "against": away_value.get("against", {}).get("average", 0),
                        }
            except (AttributeError, TypeError, NameError) as e:
                print(f"Error while processing league data: {e}")

            def calculate_scores(iteration_string):
                try:
                    # Initialize counters
                    L, W, D = 0, 0, 0
                    increments = [2.4, 1.4, 1.0, 0.6, 0.4, 0.2]

                    for i, char in enumerate(iteration_string):
                        if i < len(increments):  # Prevent IndexError
                            if char == "L":
                                L += increments[i]  # Increment home wins
                            elif char == "W":
                                W += increments[i]  # Increment away wins
                            elif char == "D":
                                D += increments[i]  # Increment draws
                    return L, W, D
                except Exception as e:
                    print(f"Error in calculate_scores: {e}")
                return 0, 0, 0  # Return default values if an error occurs

            # Example usage
            home_form_dict = {}
            away_form_dict = {}

            try:
                home_form_dict["L"], home_form_dict["W"], home_form_dict["D"] = (
                    calculate_scores(process_string(home_league_data.get("form", "")))
                )
                away_form_dict["L"], away_form_dict["W"], away_form_dict["D"] = (
                    calculate_scores(process_string(away_league_data.get("form", "")))
                )
            except Exception as e:
                print(f"Error processing form data: {e}")
                home_form_dict = {"L": 0, "W": 0, "D": 0}
                away_form_dict = {"L": 0, "W": 0, "D": 0}

            def adjust_form_percentages(home_form):
                try:
                    total = sum(home_form.values()) or 1  # Avoid ZeroDivisionError
                    percentages = {
                        key: (value / total) * 100 for key, value in home_form.items()
                    }

                    if percentages.get("D", 0) == 100:
                        percentages["D"] = 60
                        remaining = 40
                        other_keys = [key for key in home_form if key != "D"]
                        for key in other_keys:
                            percentages[key] = remaining / len(other_keys)
                    elif (
                        percentages.get("L", 0) == 100 or percentages.get("W", 0) == 100
                    ):
                        max_key = max(percentages, key=percentages.get)
                        if max_key != "D":
                            percentages[max_key] = 80
                            percentages["D"] = 12
                            remaining = 8
                            other_keys = [
                                key for key in home_form if key not in (max_key, "D")
                            ]
                            for key in other_keys:
                                percentages[key] = remaining / len(other_keys)

                    draw_percentage = percentages.pop("D", 0)
                    lw_total = (
                        percentages.get("L", 0) + percentages.get("W", 0) or 1
                    )  # Prevent ZeroDivisionError
                    percentages["L"] += (percentages["L"] / lw_total) * draw_percentage
                    percentages["W"] += (percentages["W"] / lw_total) * draw_percentage
                    return percentages
                except Exception as e:
                    print(f"Error in adjust_form_percentages: {e}")
                    return {"L": 0, "W": 0, "D": 0}

            home_form_adjusted_percentages = adjust_form_percentages(home_form_dict)
            away_form_adjusted_percentages = adjust_form_percentages(away_form_dict)

            try:
                home_form_win_rate = (
                    home_form_adjusted_percentages.get("W", 0)
                    + away_form_adjusted_percentages.get("L", 0)
                ) / 2
                away_form_win_rate = (
                    away_form_adjusted_percentages.get("W", 0)
                    + home_form_adjusted_percentages.get("L", 0)
                ) / 2

                home_goal_list.append(
                    (
                        (home_form_win_rate / 100)
                        * (
                            ((float(home_goals_for_average) + home_mean) / 2)
                            + ((float(away_goals_for_average) + away_mean) / 2)
                        )
                    )
                )
                away_goal_list.append(
                    (
                        (away_form_win_rate / 100)
                        * (
                            ((float(away_goals_for_average) + away_mean) / 2)
                            + ((float(home_goals_for_average) + home_mean) / 2)
                        )
                    )
                )

            except Exception as e:
                print(f"Error calculating goal lists: {e}")

            try:
                home_prctn_win = (
                    (
                        home_league_data["fixtures"]["wins"]["home"]
                        / home_league_data["fixtures"]["played"]["home"]
                    )
                    * 100
                    if home_league_data["fixtures"]["played"]["home"]
                    else 0
                )
            except (KeyError, ZeroDivisionError, TypeError):
                home_prctn_win = 0

            try:
                away_prctn_win = (
                    (
                        away_league_data["fixtures"]["wins"]["away"]
                        / away_league_data["fixtures"]["played"]["away"]
                    )
                    * 100
                    if away_league_data["fixtures"]["played"]["away"]
                    else 0
                )
            except (KeyError, ZeroDivisionError, TypeError):
                away_prctn_win = 0

            home_prcet_list = []
            away_prcet_list = []

            home_prcet_list.append(home_prctn_win)
            away_prcet_list.append(away_prctn_win)

            try:
                home_goal_list.append(home_league_data["goals"]["for"]["home"])
                home_goal_list.append(home_league_data["goals"]["for"]["total"])
            except KeyError:
                home_goal_list.extend([0, 0])

            try:
                away_goal_list.append(away_league_data["goals"]["for"]["away"])
                away_goal_list.append(away_league_data["goals"]["for"]["total"])
            except KeyError:
                away_goal_list.extend([0, 0])

            def calculate_total_cards(cards):
                try:
                    yellow_totals = [
                        value["total"]
                        for value in cards.get("yellow", {}).values()
                        if isinstance(value, dict) and value.get("total") is not None
                    ]
                    red_totals = [
                        value["total"]
                        for value in cards.get("red", {}).values()
                        if isinstance(value, dict) and value.get("total") is not None
                    ]

                    average_yellow = (
                        sum(yellow_totals) / len(yellow_totals) if yellow_totals else 0
                    )
                    average_red = sum(red_totals) / len(red_totals) if red_totals else 0
                    return average_yellow + average_red
                except (TypeError, AttributeError, ZeroDivisionError):
                    return 0

            try:
                total_expected_card = (
                    (
                        (
                            calculate_total_cards(
                                data_store["predictions"][0]["teams"]["home"]["league"][
                                    "cards"
                                ]
                            )
                            + calculate_total_cards(
                                data_store["predictions"][0]["teams"]["away"]["league"][
                                    "cards"
                                ]
                            )
                        )
                        - 2
                    )
                    if calculate_total_cards(
                        data_store["predictions"][0]["teams"]["home"]["league"]["cards"]
                    )
                    else 0
                )
            except (KeyError, ZeroDivisionError, TypeError, IndexError):
                total_expected_card = 0

            def calculate_average_comparison_percentage(comparison):
                home_total = 0
                away_total = 0
                count = 0

                try:
                    for key, value in comparison.items():
                        home_percentage = (
                            float(value["home"].strip("%")) if value["home"] else 0
                        )
                        away_percentage = (
                            float(value["away"].strip("%")) if value["away"] else 0
                        )
                        home_total += home_percentage
                        away_total += away_percentage
                        count += 1
                    return (home_total / count if count else 0), (
                        away_total / count if count else 0
                    )
                except (KeyError, ValueError, TypeError):
                    return 0, 0

            try:
                home_comp, away_comp = calculate_average_comparison_percentage(
                    data_store["predictions"][0]["comparison"]
                )
            except (KeyError, IndexError, TypeError):
                home_comp, away_comp = 0, 0

            print("total_expected_card -", total_expected_card)
            home_goal_list.append(
                (home_comp / 100) * (home_mean + away_mean)
            )  # newnewnew
            away_goal_list.append(
                (away_comp / 100) * (home_mean + away_mean)
            )  # newnewnew
            try:
                home_float_data = [float(x) for x in home_goal_list]
                home_final_mean = np.mean(home_float_data) if home_float_data else 0
            except (ValueError, TypeError):
                home_final_mean = 0

            try:
                away_float_data = [float(x) for x in away_goal_list]
                away_final_mean = np.mean(away_float_data) if away_float_data else 0
            except (ValueError, TypeError):
                away_final_mean = 0

            home_goals_for_average = float(home_goals_for_average)
            away_goals_for_average = float(away_goals_for_average)

            def weighted_mean(a, b, w1=1, w2=1):
                return (a * w1 + b * w2) / (w1 + w2)

            try:
                if home_final_mean > away_final_mean:
                    if home_final_mean < home_goals_for_average:
                        # home_final_mean = (home_final_mean + home_goals_for_average) / 2
                        home_final_mean = weighted_mean(
                            home_final_mean, home_goals_for_average, 1, 2
                        )
                    else:
                        home_final_mean = home_final_mean
                    if away_final_mean > away_goals_for_average:
                        # away_final_mean = (away_final_mean + away_goals_for_average) / 2
                        away_final_mean = weighted_mean(
                            away_final_mean, away_goals_for_average, 1, 2
                        )
                    else:
                        away_for_arg = away_goals_for_average / 2
                        # away_final_mean = (away_final_mean + away_for_arg) / 2
                        away_final_mean = (away_final_mean, away_for_arg, 2, 1)

                if away_final_mean > home_final_mean:
                    if away_final_mean < away_goals_for_average:
                        # away_final_mean = (away_final_mean + away_goals_for_average) / 2
                        away_final_mean = weighted_mean(
                            away_final_mean, away_goals_for_average, 1, 2
                        )
                    else:
                        away_final_mean = away_final_mean
                    if home_final_mean > home_goals_for_average:
                        # home_final_mean = (home_final_mean + home_goals_for_average) / 2
                        home_final_mean = weighted_mean(
                            home_final_mean, home_goals_for_average, 1, 2
                        )
                    else:
                        home_for_arg = home_goals_for_average / 2
                        # home_final_mean = (home_final_mean + home_for_arg) / 2
                        home_final_mean = weighted_mean(
                            home_final_mean, home_for_arg, 2, 1
                        )

            except (ValueError, TypeError):
                pass

            def to_float(value):
                """Convert NumPy array (if applicable) to float"""
                if isinstance(value, np.ndarray):
                    return float(value[0])  # Convert first element of array to float
                elif isinstance(value, tuple):
                    return float(value[0])  # Extract first element if it's a tuple
                return float(value)

            # Apply conversion
            home_final_mean = to_float(home_final_mean)
            away_final_mean = to_float(away_final_mean)

            print("ratuombi though is ", ratuombi)
            neat_ratuombi = None
            if ratuombi > 4:
                ratuombi = 4
            if ratuombi > 2.5:
                neat_ratuombi = ratuombi
            if neat_ratuombi:
                home_final_mean = (home_final_mean * neat_ratuombi) / 3.33
                away_final_mean = (away_final_mean * neat_ratuombi) / 3.33
            else:
                home_final_mean = home_final_mean
                away_final_mean = away_final_mean

            print("API-PREDICTIONS \n")
            api_prediction = {}

            # Check if the variables are available (not None) and assign to the dictionary
            api_prediction["home_final_mean"] = (
                home_final_mean if home_final_mean is not None else None
            )
            api_prediction["ratuombi"] = ratuombi
            api_prediction["away_final_mean"] = (
                away_final_mean if away_final_mean is not None else None
            )
            api_prediction["corners"] = (
                None  # You already assigned None explicitly for corners
            )
            api_prediction["cards"] = (
                total_expected_card if total_expected_card is not None else None
            )
            api_prediction["home_avg_g"] = (
                float(home_goals_for_average)
                if home_goals_for_average is not None
                else None
            )
            api_prediction["away_avg_g"] = (
                float(away_goals_for_average)
                if away_goals_for_average is not None
                else None
            )
            print("prediction_based_on_api", api_prediction)
            return api_prediction

        try:
            api_prediction = comparison_center(home_mean, away_mean, data_store)
        except Exception as e:
            print("Error in comparison_center:", str(e))
        return api_prediction

    def save_to_self(self, *args):
        def custom_round(number):
            """Rounds numbers: below .5 rounds down, .5 and above rounds up."""
            return math.floor(number) if number % 1 < 0.5 else math.ceil(number)

        def truncate(number, decimals=2):
            """Truncates a number to a fixed number of decimal places without rounding."""
            factor = 10**decimals
            return math.floor(number * factor) / factor

        odds_prediction = args[0] if len(args) > 0 else None
        if odds_prediction:
            print("yeeeeeee,oddsssssssssssssssss")
        api_predictions = args[1] if len(args) > 1 else None
        if api_predictions:
            print("yesssssss apiiiiiiiiiiiiiiii")
        if odds_prediction and api_predictions:

            def premium_three_way(
                home_mean_odd,
                away_mean_odd,
                home_odd,
                away_odd,
                draw_odd,
                home_mean_api,
                away_mean_api,
                home_avg_g_api,
                away_avg_g_api,
                ratuombi,
            ):
                def to_float(value):
                    """Convert NumPy array (if applicable) to float"""
                    if isinstance(value, np.ndarray):
                        return float(
                            value[0]
                        )  # Convert first element of array to float
                    elif isinstance(value, tuple):
                        return float(value[0])  # Extract first element if it's a tuple
                    return float(value)

                home_mean_odd = to_float(home_mean_odd)
                away_mean_odd = to_float(away_mean_odd)
                home_odd = to_float(home_odd)
                away_odd = to_float(away_odd)
                draw_odd = to_float(draw_odd)
                home_mean_api = to_float(home_mean_api)
                away_mean_api = to_float(away_mean_api)
                home_avg_g_api = to_float(home_avg_g_api)
                away_avg_g_api = to_float(away_avg_g_api)
                home_diff = home_mean_odd - away_mean_odd
                away_diff = away_mean_odd - home_mean_odd
                home_round = custom_round(home_mean_odd)
                away_round = custom_round(away_mean_odd)

                if (
                    (
                        home_diff > 0.5
                        and away_mean_odd < 0.6
                        and home_mean_odd > 0.6
                        and (home_round != away_round)
                        and (
                            (
                                (home_odd > 1.7 and home_odd < 1.95)
                                and (draw_odd > 3.55 and draw_odd < 3.97)
                                and (away_odd > draw_odd)
                                and (away_odd - draw_odd < 0.4)
                                and (ratuombi < 2.5)
                            )
                            or (
                                ((home_odd > 1.4) and (draw_odd > 4.0))
                                and (away_odd > 4.0)
                                and (away_odd > draw_odd)
                                and (home_odd > 1.4 and home_odd < 1.6)
                            )
                        )
                    )
                    or (
                        away_diff > 0.5
                        and home_mean_odd < 0.6
                        and away_mean_odd > 0.6
                        and (home_round != away_round)
                        and (
                            (
                                (away_odd > 1.7 and away_odd < 1.9)
                                and (draw_odd > 3.55 and draw_odd < 3.97)
                                and (home_odd > draw_odd)
                                and (home_odd - draw_odd < 0.4)
                                and (ratuombi < 2.5)
                            )
                            or (
                                ((away_odd > 1.4) and (draw_odd > 4.0))
                                and (home_odd > 4.0)
                                and (home_odd > draw_odd)
                                and (away_odd > 1.4 and away_odd < 1.6)
                            )
                        )
                    )
                    or (
                        (
                            (home_mean_odd > away_mean_odd)
                            and (home_mean_api > away_mean_api)
                        )
                        and ((home_avg_g_api - away_avg_g_api) > 1.2)
                        and (away_avg_g_api < 1.5)
                        and (home_round != away_round)
                        and ((draw_odd >= home_odd) and (draw_odd <= away_odd))
                        and (home_odd > 1.4)
                        and (ratuombi < 2.7)
                    )
                    or (
                        (
                            (away_mean_odd > home_mean_odd)
                            and (away_mean_api > home_mean_api)
                        )
                        and ((away_avg_g_api - home_avg_g_api) > 1.2)
                        and (home_avg_g_api < 1.5)
                        and (home_round != away_round)
                        and ((draw_odd >= away_odd) and (draw_odd <= home_odd))
                        and (away_odd > 1.4)
                        and (ratuombi < 2.7)
                    )
                ):
                    return True
                else:
                    return False

            try:
                is_premium_three = premium_three_way(
                    odds_prediction["home_final_mean"],
                    odds_prediction["away_final_mean"],
                    self.team_1_win_odds,
                    self.team_2_win_odds,
                    self.draw_odds,
                    api_predictions["home_final_mean"],
                    api_predictions["away_final_mean"],
                    api_predictions["home_avg_g"],
                    api_predictions["away_avg_g"],
                    api_predictions["ratuombi"],
                )
            except KeyError as e:
                print(f"KeyError: Missing key {e} in odds_prediction.")
            except TypeError as e:
                print(f"TypeError: Invalid type in premium_three_way call - {e}.")
            except Exception as e:
                print(f"Unexpected error in premium_three_way: {e}")
                is_premium_three = None

            if is_premium_three:
                self.is_premium["where"] = "three_way"

            def is_premium_bts(
                home_mean_odd,
                away_mean_odd,
                home_odd,
                draw_odd,
                away_odd,
                gg_odd,
                no_gg_odd,
                home_mean_api,
                away_mean_api,
                home_avg_g_api,
                away_avg_g_api,
                ratuombi,
            ):
                try:
                    # Attempt to convert each odd to float, defaulting to 0.0 if None
                    home_odd = float(home_odd) if home_odd is not None else 0.0
                    draw_odd = float(draw_odd) if draw_odd is not None else 0.0
                    away_odd = float(away_odd) if away_odd is not None else 0.0
                    gg_odd = float(gg_odd) if gg_odd is not None else 0.0
                    no_gg_odd = float(no_gg_odd) if no_gg_odd is not None else 0.0

                except ValueError as e:
                    # Handles cases like strings that can't convert to float
                    print(f"ValueError: Invalid input for conversion to float -> {e}")
                    return None
                except TypeError as e:
                    # Handles unexpected type issues
                    print(f"TypeError: Incorrect type provided -> {e}")
                    return None
                except Exception as e:
                    # Catches any other unforeseen errors
                    print(f"An unexpected error occurred: {e}")
                # Condition 1: Both home and away > 0.75, draw_odd is lowest, gg_odd > no_gg_odd and > 1.5
                condition_one = (
                    home_mean_odd > 0.7
                    and away_mean_odd > 0.7
                    and (
                        ((abs(draw_odd - home_odd)) < 1.5)
                        or ((abs(draw_odd - away_odd)) < 1.5)
                    )
                    and (1.5 < gg_odd < 2)
                    and ((home_mean_odd + away_mean_odd) > 2.5)
                    and (abs(home_mean_odd - away_mean_odd) <= 1.0)
                    and (abs(home_odd - away_odd) < 2.5)
                    and ratuombi > 2.4
                )
                condition_v = (
                    home_mean_odd < 0.5
                    and away_mean_odd < 0.5
                    and ratuombi > 3.0
                    and home_avg_g_api < 2
                    and away_avg_g_api < 2
                    and (draw_odd > 2.65 and draw_odd < 3.4)
                    and away_odd < home_odd
                    and (gg_odd > no_gg_odd and gg_odd < 2.10 and gg_odd > 1.4)
                )
                condition_three = (
                    ((home_avg_g_api > 2.0) and (away_avg_g_api > 2.0))
                    and ((draw_odd > home_odd) and (draw_odd > away_odd))
                    and ((home_mean_odd + home_mean_api) / 2 > 0.65)
                    and ((away_mean_odd + away_mean_api) / 2 > 0.65)
                    and (ratuombi > 3.1)
                    and gg_odd > 1.4
                )

                condition_four = (
                    ((home_avg_g_api < 2.0) and (away_avg_g_api < 1.60))
                    and not ((draw_odd > home_odd) and (draw_odd > away_odd))
                    and ((home_mean_odd + home_mean_api) / 2 < 0.6)
                    and ((away_mean_odd + away_mean_api) / 2 < 0.6)
                    and ratuombi < 2.3
                )

                # Condition 2: Either home or away < 0.35, draw_odd not lowest, gg_odd < no_gg_odd and no_gg_odd > 1.5
                condition_two = (
                    (home_mean_odd < 0.3 or away_mean_odd < 0.3)
                    and not (draw_odd > home_odd and draw_odd > away_odd)
                    and (1.5 < no_gg_odd < 2)
                    and ((home_mean_odd + away_mean_odd) < 1.0)
                    and (abs(home_mean_odd - away_mean_odd) >= 1.5)
                    and (abs(home_odd - away_odd) > 2.5)
                )

                return (
                    condition_one
                    or condition_v
                    or condition_two
                    or condition_three
                    or condition_four
                )

            try:
                is_premium_gg = is_premium_bts(
                    odds_prediction["home_final_mean"],
                    odds_prediction["away_final_mean"],
                    self.team_1_win_odds,
                    self.draw_odds,
                    self.team_2_win_odds,
                    self.gg_odds,
                    self.no_gg_odds,
                    api_predictions["home_final_mean"],
                    api_predictions["away_final_mean"],
                    api_predictions["home_avg_g"],
                    api_predictions["away_avg_g"],
                    api_predictions["ratuombi"],
                )
            except KeyError as e:
                print(f"KeyError: Missing key {e} in odds_prediction.")
            except TypeError as e:
                print(f"TypeError: Invalid type used in is_premium_bts call - {e}.")
            except Exception as e:
                print(f"Unexpected error: {e}")
                is_premium_gg = None

            if is_premium_gg:
                self.is_premium["where"] = "gg"

            def is_premium_o25(
                home_mean_odd,
                away_mean_odd,
                home_odd,
                draw_odd,
                away_odd,
                over_odd,
                under_odd,
                home_mean_api,
                away_mean_api,
                home_avg_g_api,
                away_avg_g_api,
                ratuombi,
            ):
                addition = home_mean_odd + away_mean_odd
                home_odd = float(home_odd)
                draw_odd = float(draw_odd)
                away_odd = float(away_odd)
                over_odd = float(over_odd)
                under_odd = float(under_odd)
                # Condition 1: addition - 2.5 > 0.6, draw_odd is lowest, over_odd > under_odd and over_odd > 1.5
                condition_one = (
                    (addition - 2.5) > 0.4
                    and draw_odd > home_odd
                    and draw_odd > away_odd
                    and (abs(over_odd - under_odd) < 0.45)
                    and over_odd > 1.4
                    and ((home_mean_api > 1.4) or (away_mean_api > 1.4))
                )

                condition_three = (
                    ratuombi > 3.2
                    and (
                        ((home_avg_g_api + away_avg_g_api) > 3.5)
                        or ((home_avg_g_api > 2.3) or (away_avg_g_api > 2.3))
                    )
                    and over_odd > 1.4
                    and (abs(over_odd - under_odd) < 0.45)
                )
                condition_four = (
                    ratuombi < 2.3
                    and (
                        ((home_avg_g_api + away_avg_g_api) < 2.0)
                        or ((home_avg_g_api < 0.4) or (away_avg_g_api < 0.4))
                    )
                    and not (draw_odd > home_odd and draw_odd > away_odd)
                    and under_odd > 1.4
                )
                # Condition 2: 2.5 - addition > 0.8, draw_odd not lowest, under_odd > over_odd and under_odd > 1.5
                condition_two = (
                    (2.5 - addition) > 0.8
                    and not (draw_odd > home_odd and draw_odd > away_odd)
                    and under_odd > 1.5
                    and ((home_mean_api < 0.25) or (away_mean_api < 0.25))
                    and ((home_avg_g_api + away_avg_g_api) < 2.0)
                )

                return (
                    condition_one or condition_two or condition_three or condition_four
                )

            try:
                is_premium_ou25 = is_premium_o25(
                    odds_prediction["home_final_mean"],
                    odds_prediction["away_final_mean"],
                    self.team_1_win_odds,
                    self.draw_odds,
                    self.team_2_win_odds,
                    self.over_2_5_odds,
                    self.under_2_5_odds,
                    api_predictions["home_final_mean"],
                    api_predictions["away_final_mean"],
                    api_predictions["home_avg_g"],
                    api_predictions["away_avg_g"],
                    api_predictions["ratuombi"],
                )
            except KeyError as e:
                print(f"KeyError: Missing key {e} in odds_prediction.")
            except TypeError as e:
                print(f"TypeError: Invalid type used in is_premium_o25 call - {e}.")
            except Exception as e:
                print(f"Unexpected error: {e}")
                is_premium_ou25 - None

            if is_premium_ou25:
                self.is_premium["where"] = "ov"
            if self.is_premium:
                console = Console()
                banner = pyfiglet.figlet_format(
                    "GOD JUST \t\t GAVE US\t\t SOME GOLD HERE"
                )
                console.print(f"[bold red]{banner}[/bold red]")

        weather_man = []
        weather_impact = {
            "Clear sky": {
                "effect": "Ideal conditions, high visibility, good ball control",
                "goal_change": +2,
            },
            "Few clouds": {
                "effect": "Minimal effect, slightly cooler conditions",
                "goal_change": +2,
            },
            "Scattered clouds": {
                "effect": "Little effect, normal play",
                "goal_change": +2,
            },
            "Broken clouds": {
                "effect": "Slightly reduced visibility, minor impact",
                "goal_change": +0,
            },
            "Overcast clouds": {
                "effect": "Dull lighting, minor reduction in visibility",
                "goal_change": -1,
            },
            "Light rain": {
                "effect": "Slightly slippery pitch, minor passing difficulty",
                "goal_change": +5,
            },
            "Moderate rain": {
                "effect": "Slower ball movement, harder dribbling",
                "goal_change": +3,
            },
            "Heavy rain": {
                "effect": "Very slippery, reduced passing accuracy",
                "goal_change": -10,
            },
            "Very heavy rain": {
                "effect": "Severely reduced visibility, unpredictable ball movement",
                "goal_change": -15,
            },
            "Extreme rain": {
                "effect": "Possible match disruption, hard to control ball",
                "goal_change": -20,
            },
            "Freezing rain": {
                "effect": "Ice on pitch, dangerous conditions",
                "goal_change": -25,
            },
            "Light snow": {
                "effect": "Slightly reduced visibility, slow ball movement",
                "goal_change": +7,
            },
            "Moderate snow": {
                "effect": "Ball movement affected, harder dribbling",
                "goal_change": +3,
            },
            "Heavy snow": {
                "effect": "Severely reduced visibility, pitch covered",
                "goal_change": -10,
            },
            "Sleet": {
                "effect": "Icy surface, extremely difficult play",
                "goal_change": -25,
            },
            "Freezing drizzle": {"effect": "Dangerous icy surface", "goal_change": -30},
            "Thunderstorm": {
                "effect": "Strong winds, possible match stoppage",
                "goal_change": -15,
            },
            "Light thunderstorm": {
                "effect": "High winds, difficult passing",
                "goal_change": -10,
            },
            "Heavy thunderstorm": {
                "effect": "Unsafe conditions, match delays likely",
                "goal_change": -25,
            },
            "Ragged thunderstorm": {
                "effect": "Severe storm, game interruptions",
                "goal_change": -30,
            },
            "Mist": {
                "effect": "Reduced visibility, harder long passes",
                "goal_change": -5,
            },
            "Fog": {
                "effect": "Very low visibility, difficult gameplay",
                "goal_change": -15,
            },
            "Haze": {"effect": "Moderate visibility reduction", "goal_change": -5},
            "Smoke": {
                "effect": "Breathing difficulty, reduced endurance",
                "goal_change": -10,
            },
            "Dust": {
                "effect": "Airborne particles, very poor visibility",
                "goal_change": -15,
            },
            "Sand": {
                "effect": "Severe visibility issues, difficulty breathing",
                "goal_change": -20,
            },
            "Ash": {"effect": "Toxic air, unsafe to play", "goal_change": -30},
            "Squalls": {
                "effect": "Very strong winds, unpredictable ball movement",
                "goal_change": -20,
            },
            "Tornado": {
                "effect": "Extreme danger, game cancellation",
                "goal_change": -50,
            },
        }
        humidity_impact = {
            "extremely_low": {
                "range": (0, 15),
                "effects_on_players": "Severe dehydration risk, fatigue increases rapidly, higher injury probability",
                "effects_on_ball": "Moves very fast, little air resistance",
                "goal_impact": -8,  # Fewer goals expected
            },
            "very_low": {
                "range": (16, 30),
                "effects_on_players": "Moderate dehydration risk, slight fatigue increase",
                "effects_on_ball": "Moves faster than normal",
                "goal_impact": -5,
            },
            "low": {
                "range": (31, 45),
                "effects_on_players": "Minimal impact, good endurance conditions",
                "effects_on_ball": "Normal movement",
                "goal_impact": +0,  # Neutral
            },
            "moderate": {
                "range": (46, 60),
                "effects_on_players": "Optimal endurance, best oxygen intake",
                "effects_on_ball": "Better ball control",
                "goal_impact": 3,  # More goals expected
            },
            "high": {
                "range": (61, 75),
                "effects_on_players": "Increased sweating, reduced stamina, longer recovery time",
                "effects_on_ball": "Slightly heavier due to moisture",
                "goal_impact": -5,
            },
            "very_high": {
                "range": (76, 90),
                "effects_on_players": "Severe fatigue, overheating, slower movement",
                "effects_on_ball": "Ball absorbs moisture, heavier & slower",
                "goal_impact": -8,
            },
            "extremely_high": {
                "range": (91, 100),
                "effects_on_players": "Extreme exhaustion, risk of heat stroke, players struggle to perform",
                "effects_on_ball": "Becomes significantly heavier, slower pace of game",
                "goal_impact": -10,  # Significantly fewer goals expected
            },
        }
        feels_like_impact = {
            "extremely_cold": {
                "range": (-30, -23),
                "effects_on_players": "Severe risk of hypothermia, frostbite, slow movement, high injury risk",
                "effects_on_ball": "Ball becomes stiff and less responsive",
                "goal_impact": -15,  # Significantly fewer goals expected
            },
            "somehow_very_cold": {
                "range": (-22, -11),
                "effects_on_players": "Muscle stiffness, reduced flexibility, slower play",
                "effects_on_ball": "Less bounce, harder to control",
                "goal_impact": -11,
            },
            "very_cold": {
                "range": (-11, 0),
                "effects_on_players": "Muscle stiffness, reduced flexibility, slower play",
                "effects_on_ball": "Less bounce, harder to control",
                "goal_impact": -8,
            },
            "shiver": {
                "range": (0.1, 4.5),
                "effects_on_players": "Slightly reduced mobility, but generally good conditions",
                "effects_on_ball": "Normal behavior, slightly harder surface",
                "goal_impact": -5,
            },
            "cold": {
                "range": (4.6, 10),
                "effects_on_players": "Slightly reduced mobility, but generally good conditions",
                "effects_on_ball": "Normal behavior, slightly harder surface",
                "goal_impact": -3,
            },
            "somehow_mild": {
                "range": (10.1, 22),
                "effects_on_players": "Optimal playing conditions, players perform at their best",
                "effects_on_ball": "Best ball control and movement",
                "goal_impact": 1,  # More goals expected
            },
            "mild": {
                "range": (22.1, 30),
                "effects_on_players": "Optimal playing conditions, players perform at their best",
                "effects_on_ball": "Best ball control and movement",
                "goal_impact": 3,  # More goals expected
            },
            "warm": {
                "range": (31, 45),
                "effects_on_players": "Increased sweating, moderate fatigue, reduced stamina",
                "effects_on_ball": "Ball moves slightly faster",
                "goal_impact": -3,
            },
            "very_hot": {
                "range": (46, 60),
                "effects_on_players": "Severe exhaustion, overheating, dehydration risk",
                "effects_on_ball": "Ball moves faster but play slows down due to fatigue",
                "goal_impact": -8,
            },
            "extremely_hot": {
                "range": (61, 100),
                "effects_on_players": "Dangerous heat levels, risk of heat stroke, extreme fatigue",
                "effects_on_ball": "Game slows down significantly due to extreme conditions",
                "goal_impact": -10,  # Significantly fewer goals expected
            },
        }

        wind_speed_impact_mps = {
            "calm": {
                "range": (0, 4),
                "effects_on_players": "No significant impact on stamina or balance.",
                "effects_on_ball": "Minimal effect on ball trajectory.",
                "goal_impact": +0,  # Neutral effect on goal count.
            },
            "light breeze": {
                "range": (5, 8),
                "effects_on_players": "Slight cooling effect, minor impact on passes.",
                "effects_on_ball": "Small deviation in long passes and shots.",
                "goal_impact": 2,  # Slightly more goals possible due to easier conditions.
            },
            "moderate wind": {
                "range": (9, 12),
                "effects_on_players": "May affect balance slightly, increased fatigue over time.",
                "effects_on_ball": "Noticeable deviation in high passes and long shots.",
                "goal_impact": -3,  # Slightly fewer goals due to ball unpredictability.
            },
            "strong wind": {
                "range": (13, 17),
                "effects_on_players": "Players struggle to maintain balance, increased fatigue.",
                "effects_on_ball": "Difficult to control high passes, shots affected by wind.",
                "goal_impact": -6,  # Fewer goals expected due to difficulty in control.
            },
            "very strong wind": {
                "range": (18, 21),
                "effects_on_players": "Players may struggle to move against the wind.",
                "effects_on_ball": "Significant impact on ball movement, unpredictable bounces.",
                "goal_impact": -8,
            },
            "stormy conditions": {
                "range": (22, 26),
                "effects_on_players": "Difficult to sprint, increased risk of falling.",
                "effects_on_ball": "Severe impact on ball control, game quality reduced.",
                "goal_impact": -10,  # Very few goals expected.
            },
            "extreme storm": {
                "range": (27, 42),
                "effects_on_players": "Game may be postponed due to safety risks.",
                "effects_on_ball": "Ball movement highly erratic, unplayable conditions.",
                "goal_impact": -15,  # Almost no goals expected.
            },
        }
        weather_fine = None
        if self.data_store.get("weather", {}):
            weather_data = self.data_store["weather"]

            feels_like = custom_round(float(weather_data.get("feels_like", 0.0)))
            humidity = custom_round(float(weather_data.get("humidity", 50)))
            weather_description = weather_data.get("weather_description", "Clear sky")
            wind_speed = custom_round(float(weather_data.get("wind_speed", 1)))

            def get_goal_impact(value, source):
                """Finds the goal impact based on the given value and predefined source ranges"""
                for condition, details in source.items():
                    min_val, max_val = details["range"]
                    if min_val <= value <= max_val:
                        return details["goal_impact"]
                return 0  # Return 0 if not found

            # Get goal impact values
            feels_like_impact_value = get_goal_impact(feels_like, feels_like_impact)
            humidity_impact_value = get_goal_impact(humidity, humidity_impact)
            wind_speed_impact_value = get_goal_impact(wind_speed, wind_speed_impact_mps)

            # Weather description impact
            weather_description_impact = weather_impact.get(
                weather_description, {}
            ).get("goal_change", 0.2)

            # Store values
            weather_man = [
                feels_like_impact_value,
                humidity_impact_value,
                wind_speed_impact_value,
                weather_description_impact,
            ]
            print("the vaue of weather man is ", weather_man)
            print("the sum of weather man is", sum(weather_man))
            weather_fine = 0.50 * (sum(weather_man) / 10)

        else:
            print("\t\t\t\t\t\t We don't have weather info for this game")

        list_of_prediction_dicts = []
        for v in args:
            if isinstance(v, dict):  # Only append if v is a dictionary
                list_of_prediction_dicts.append(v)
            else:
                print(f"Warning: Skipping invalid entry (not a dict): {v}")

        list_of_home_mean = []
        list_of_away_mean = []
        list_of_corners = []
        list_of_cards = []

        for prediction in list_of_prediction_dicts:
            if prediction is not None and isinstance(prediction, dict):
                for key, value in prediction.items():
                    if key == "home_final_mean" and isinstance(value, (int, float)):
                        list_of_home_mean.append(value)
                    elif key == "away_final_mean" and isinstance(value, (int, float)):
                        list_of_away_mean.append(value)
                    elif key == "corners" and isinstance(value, (int, float)):
                        list_of_corners.append(value)
                    elif key == "cards" and isinstance(value, (int, float)):
                        list_of_cards.append(value)
            else:
                print(f"Warning: Skipping invalid prediction entry: {prediction}")

        def safe_mean(data_list):
            cleaned_list = [
                x for x in data_list if isinstance(x, (int, float))
            ]  # Remove invalid values
            return (
                np.mean(cleaned_list) if cleaned_list else 0
            )  # Avoid division by zero

        # Compute means safely
        home_mean = safe_mean(list_of_home_mean)
        away_mean = safe_mean(list_of_away_mean)
        corners_mean = safe_mean(list_of_corners)
        cards_mean = safe_mean(list_of_cards)
        if not odds_prediction and api_predictions:
            if home_mean > away_mean:
                home_mean = home_mean + (0.38*home_mean)
                away_mean = away_mean - (0.38*away_mean)
            if away_mean >home_mean:
                away_mean = away_mean +(0.38*away_mean)
                home_mean = home_mean-(0.38*home_mean)
            
        if weather_fine is not None:
            home_mean += weather_fine
            away_mean += weather_fine
        else:
            home_mean += 0
            away_mean += 0

        home_mean = truncate(home_mean, 1)
        away_mean = truncate(away_mean, 1)
        if home_mean < 0:
            home_mean = 0.2
        if away_mean < 0:
            away_mean = 0.2
      
        if home_mean is not None and away_mean is not None:
            threeway = self.generate_three_way_prob(home_mean, away_mean)
            over_under = self.calculate_goal_percentages(home_mean, away_mean)
        else:
            print("Error: 'home_mean' and 'away_mean' must be provided.")

        self.gg_probability = self.custom_round(
            over_under.get("bts", {}).get("bts", "N/A")
        )
        self.no_gg_probability = self.custom_round(
            over_under.get("bts", {}).get("no_bts", "N/A")
        )

        self.over_1_5_probability = self.custom_round(over_under.get("Over 1.5", "N/A"))
        self.under_1_5_probability = self.custom_round(
            over_under.get("Under 1.5", "N/A")
        )

        self.over_2_5_probability = self.custom_round(over_under.get("Over 2.5", "N/A"))
        self.under_2_5_probability = self.custom_round(
            over_under.get("Under 2.5", "N/A")
        )

        self.over_3_5_probability = self.custom_round(over_under.get("Over 3.5", "N/A"))
        self.under_3_5_probability = self.custom_round(
            over_under.get("Under 3.5", "N/A")
        )

        self.over_4_5_probability = self.custom_round(over_under.get("Over 4.5", "N/A"))
        self.under_4_5_probability = self.custom_round(
            over_under.get("Under 4.5", "N/A")
        )

        self.over_5_5_probability = self.custom_round(over_under.get("Over 5.5", "N/A"))
        self.under_5_5_probability = self.custom_round(
            over_under.get("Under 5.5", "N/A")
        )

        if corners_mean > 13:
            corners_mean = 13
        if corners_mean < 3:
            corners_mean = 3
        if cards_mean > 2:
            cards_mean = 5
        if cards_mean < 2:
            cards_mean = 2

        self.total_corners = corners_mean

        self.total_corners_probability = random.randint(51, 64)

        self.total_cards = cards_mean
        self.total_cards_probability = random.randint(51, 64)

        self.home_team_expected_goals = abs(self.custom_round(home_mean))
        self.away_team_expected_goals = abs(self.custom_round(away_mean))

        print(
            "\t\t\t\t home_mean----", home_mean, ">>>>>", away_mean, "------ away_mean"
        )
        print("\n" + "=" * 80)
        print("🚀🔬 **ADVANCED PREDICTIVE ANALYSIS IN PROGRESS... STAND BACK!** 🔬🚀")
        print("-" * 80)
        print(
            f"📊📡 HIGH-PRECISION MATCH SIMULATION RESULTS 📡📊\n"
            f"⚽ {self.data_store['match_details']['home_team_name']} ⚔️"
            f" {round(self.home_team_expected_goals, 3)} 🔥 : 🔥"
            f" {round(self.away_team_expected_goals, 3)} ⚔️ {self.data_store['match_details']['away_team_name']} ⚽"
        )
        print("-" * 80)
        print("💾💡 **DATA CRUNCHING COMPLETE! RESULTS READY FOR DEEP INSIGHTS!** 💡💾")
        print("=" * 80 + "\n")

        self.win_probability_team_1 = threeway.get("home")
        self.win_probability_team_2 = threeway.get("away")
        self.win_probability_draw = threeway.get("draw")

        def double_chance_prob(home_win_prob, draw_prob, away_win_prob):
            home_or_draw = home_win_prob + draw_prob
            home_or_away = home_win_prob + away_win_prob
            draw_or_away = draw_prob + away_win_prob

            # Calculate the total sum for normalization
            total = home_or_draw + home_or_away + draw_or_away

            # Normalize probabilities
            home_or_draw_normalized = (home_or_draw / total) * 100
            home_or_away_normalized = (home_or_away / total) * 100
            draw_or_away_normalized = (draw_or_away / total) * 100

            return {
                "Home or Draw": home_or_draw_normalized,
                "Home or Away": home_or_away_normalized,
                "Draw or Away": draw_or_away_normalized,
            }

        double_chance = double_chance_prob(
            threeway.get("home"), threeway.get("draw"), threeway.get("away")
        )
        self.dc1x_probability = double_chance.get("Home or Draw", "N/A")
        self.dcx2_probability = double_chance.get("Home or Away", "N/A")
        self.dc12_probability = double_chance.get("Home or Away", "N/A")
