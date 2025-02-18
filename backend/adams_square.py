import requests
from datetime import datetime, timedelta
from dateutil import parser
import pprint
import numpy as np
import time
import json
import logging
from .grace_isha import analyze_data


# Set up basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Jerusalem:
    # Static variables for the API keys
    WEATHER_API_KEY = "1795372653d0553aa30f7e6be0c9d7d5"
    FOOTBALL_API_KEY = "996c177462abec830c211f413c3bdaa8"
    ODDS_API_URL = "https://v3.football.api-sports.io/odds"
    BASE_URL = "https://v3.football.api-sports.io/"
    HEADERS = {
        "x-rapidapi-key": "996c177462abec830c211f413c3bdaa8",
        "x-rapidapi-host": "v3.football.api-sports.io",
    }

    def __init__(self):
        # Instance variables to store match data
        self.match_id = None
        self.date = None
        self.venue = None
        self.city = None
        self.league_id = None
        self.home_team_name = None
        self.away_team_name = None
        self.home_team_logo = None
        self.away_team_logo = None
        self.home_team_id = None
        self.away_team_id = None
        self.weather = None  # Will store the weather data
        self.weather_error = None  # Will store any weather errors
        self.odds = None  # Will store the match odds data
        self.odds_error = None  # Will store any odds errors

        self.avg_goals_stats = {}
        self.avg_goals_error = None  # Error message for average goals
        self.last_five_home_fixtures = None
        self.last_five_away_fixtures = None
        self.home_team_player_ratings_sesason = {}
        self.away_team_player_ratings_sesason = {}
        self.h2h = None
        self.head_to_head_statistics_with_home_at_home_and_away_at_away = []
        self.home_run = []
        self.away_run = []
        self.home_stats_dict = None
        self.away_stats_dict = None
        self.fixtures_data = {}
        self.statistics_response = None
        self.fixture_response = None
        self.predictions = {}
        self.every_data = {}
        self.mutual = {
            "away": {
                "guest_vs_home": {
                    "match": {"guest_name": {}, "home_name": {}},
                    "guest_data": {},
                    "guest_ratings": {},
                    "home_data": {},
                    "home_ratings": {},
                },
                "guest_vs_away": {
                    "match": {"guest_name": {}, "away_name": {}},
                    "guest_data": {},
                    "guest_ratings": {},
                    "away_data": {},
                    "away_ratings": {},
                },
            },
            "home": {
                "home_vs_guest": {
                    "match": {"home_name": {}, "guest_name": {}},
                    "home_data": {},
                    "home_ratings": {},
                    "guest_data": {},
                    "guest_ratings": {},
                },
                "away_vs_guest": {
                    "match": {"away_name": {}, "guest_name": {}},
                    "away_data": {},
                    "away_ratings": {},
                    "guest_data": {},
                    "guest_ratings": {},
                },
            },
        }

    def fetch_forecast(self, city, target_time_utc):
        """
        Fetch the weather forecast for a given city at a specific time using OpenWeatherMap API
        """
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={Jerusalem.WEATHER_API_KEY}"

        # Parse the target time from UTC string
        try:
            if "noon" in target_time_utc.lower():
                # Set target time to noon (12:00 PM)
                target_time_utc = target_time_utc.replace("noon", "12:00 PM")
            elif "midnight" in target_time_utc.lower():
                # Set target time to midnight (12:00 AM)
                target_time_utc = target_time_utc.replace("midnight", "12:00 AM")

            # Parse the target time from UTC string
            target_time = parser.parse(target_time_utc)
            logger.info(f"Target time parsed successfully: {target_time}")
        except ValueError as e:
            logger.error(f"Error parsing date: {e}")
            return None

        # Fetch weather data from API
        try:
            logger.info(f"Fetching forecast data for city: {city}")
            response = requests.get(url)
            response.raise_for_status()  # Raise error if the response code isn't 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve forecast for {city}: {e}")
            return None

        # Parse the API response
        data = response.json()

        if "list" not in data:
            logger.error(f"Unexpected response format for {city}. 'list' key missing.")
            return None

        closest_forecast = None
        smallest_diff = timedelta.max

        # Find the forecast closest to the target time
        for forecast in data["list"]:
            try:
                forecast_time = parser.parse(forecast["dt_txt"])
                time_diff = abs(forecast_time - target_time)

                if time_diff < smallest_diff:
                    smallest_diff = time_diff
                    closest_forecast = forecast
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid forecast entry: {e}")
                continue

        if closest_forecast:
            logger.info(
                f"Found closest forecast for {city} at {closest_forecast['dt_txt']}"
            )
        else:
            logger.warning(f"No valid forecast found for {city} at the specified time.")

        return closest_forecast

    def get_match_prediction(self, fixture_id):

        base_url = "https://v3.football.api-sports.io/predictions"

        # Set up the headers with your API key
        headers = self.HEADERS

        # Define the parameters for the request
        params = {"fixture": fixture_id}

        try:
            # Make the API request
            response = requests.get(base_url, headers=headers, params=params)

            # Check if the request was successful
            response.raise_for_status()  # Will raise an HTTPError if the status code is not 200
            data = response.json()

            # Check if predictions are in the response
            predictions = data.get("response", [])
            if predictions:
                return predictions
            else:
                return {"error": "No predictions available for this fixture."}

        except requests.exceptions.HTTPError as http_err:
            return {
                "error": f"HTTP error occurred: {http_err}"
            }  # HTTP error (e.g., 404, 500)
        except requests.exceptions.RequestException as req_err:
            return {
                "error": f"Request error occurred: {req_err}"
            }  # Any other error with the request
        except Exception as err:
            return {
                "error": f"An unexpected error occurred: {err}"
            }  # Catch other unexpected errors

    def fetch_match_odds(self, match_id):
        """
        Fetch match odds using the football API for the given match ID.
        """
        url = Jerusalem.ODDS_API_URL
        headers = self.HEADERS
        params = {"fixture": match_id}
        bookmakers_priority = [
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
        target_bet_names = [
            "Match Winner",
            "Home/Away",
            "Goals Over/Under",
            "Goals Over/Under First Half",
            "Goals Over/Under - Second Half",
            "Both Teams Score",
            "Win to Nil - Home",
            "Win to Nil - Away",
            "Exact Score",
            "Correct Score - First Half",
            "Correct Score - Second Half",
            "Double Chance",
            "First Half Winner",
            "Total - Home",
            "Total - Away",
            "Both Teams Score - First Half",
            "Both Teams To Score - Second Half",
            "Corners Over Under",
            "Cards Over/Under",
        ]

        try:
            logger.info(f"Fetching match odds for match ID: {match_id}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve match odds for match {match_id}: {e}")
            self.odds_error = "Odds data not available"
            return None

        try:
            data = response.json()
            if not data.get("response"):
                logger.warning(f"No odds data found for match ID {match_id}")
                self.odds_error = "No odds data found"
                return None

            for bookmaker in bookmakers_priority:
                for entry in data["response"][0]["bookmakers"]:
                    if entry["name"] == bookmaker:
                        odds_comparison = {bookmaker: {}}
                        for bet in entry["bets"]:
                            if bet["name"] in target_bet_names:
                                odds_comparison[bookmaker][bet["name"]] = bet["values"]

                        if odds_comparison[bookmaker]:
                            print(f"Odds found from {bookmaker}")
                            logger.info(
                                f"Match odds for match ID {match_id} found from {bookmaker}"
                            )
                            return odds_comparison

            logger.warning(
                f"No odds data found for match ID {match_id} from any source"
            )
            self.odds_error = "No odds available from any source"
            return None

        except Exception as e:
            logger.error(
                f"Error processing match odds data for match ID {match_id}: {e}"
            )
            self.odds_error = "Error processing odds data"
            return None

    # def fetch_average_goals_per_match(self, league_id):
    #     """
    #     Fetches the last `last` matches for the specified league and calculates the average goals per match.
    #     Stores the results in `self.avg_goals` or error in `self.avg_goals_error`.
    #     """
    #     statistics_url = "https://v3.football.api-sports.io/fixtures"
    #     headers = {
    #         "x-rapidapi-host": "v3.football.api-sports.io",
    #         "x-rapidapi-key": "996c177462abec830c211f413c3bdaa8",
    #     }
    #     params = {"league": league_id, "season": 2022}

    #     try:
    #         response = requests.get(statistics_url, headers=headers, params=params)
    #         response.raise_for_status()
    #         match_data = response.json().get("response", [])

    #         if not match_data:
    #             self.avg_goals = None
    #             self.avg_goals_error = "No match data available for the league."
    #             return

    #         goals_per_match = []
    #         for match in match_data:
    #             score_data = match.get("score", {}).get("fulltime", {})
    #             home_goals = score_data.get("home")
    #             away_goals = score_data.get("away")

    #             if home_goals is not None and away_goals is not None:
    #                 goals_per_match.append(home_goals + away_goals)

    #         if goals_per_match:
    #             self.avg_goals = round(np.mean(goals_per_match), 3)
    #             self.avg_goals_error = None
    #         else:
    #             self.avg_goals = None
    #             self.avg_goals_error = "No valid scores found in match data."

    #     except requests.exceptions.RequestException as e:
    #         self.avg_goals = None
    #         self.avg_goals_error = f"Failed to fetch data: {e}"

    def fetch_average_goals_per_match(self, league_id):
        """
        Fetches match data for the specified league and calculates average, standard deviation,
        and median goals per match. Stores results or error messages in instance variables.
        """
        statistics_url = "https://v3.football.api-sports.io/fixtures"
        headers = self.HEADERS
        params = {"league": league_id, "season": 2022}

        try:
            logger.info(f"Fetching match data for league ID: {league_id}")
            response = requests.get(statistics_url, headers=headers, params=params)
            response.raise_for_status()  # Raise error for non-200 response
            match_data = response.json().get("response", [])

            if not match_data:
                logger.warning(f"No match data found for league ID {league_id}")
                self.avg_goals_error = "No match data available for the league."
                return

            goals_per_match = []
            for match in match_data:
                score_data = match.get("score", {}).get("fulltime", {})
                home_goals = score_data.get("home")
                away_goals = score_data.get("away")

                if home_goals is not None and away_goals is not None:
                    goals_per_match.append(home_goals + away_goals)

            if goals_per_match:
                avg_goals = round(np.mean(goals_per_match), 3)
                std_dev_goals = round(np.std(goals_per_match), 3)
                median_goals = round(np.median(goals_per_match), 3)
                self.avg_goals_error = None
                logger.info(
                    f"Statistics for league {league_id}:\n"
                    f"Average goals per match: {avg_goals}\n"
                    f"Standard deviation: {std_dev_goals}\n"
                    f"Median goals per match: {median_goals}"
                )
            else:
                avg_goals = std_dev_goals = median_goals = None
                self.avg_goals_error = "No valid scores found in match data."
                logger.warning(f"No valid scores found for league ID {league_id}")

        except requests.exceptions.RequestException as e:
            avg_goals = std_dev_goals = median_goals = None
            self.avg_goals_error = f"Failed to fetch data: {e}"
            logger.error(f"Failed to fetch match data for league {league_id}: {e}")
        return {
            "avg_goals": avg_goals,
            "std_dev_goals": std_dev_goals,
            "median_goals": median_goals,
        }

    # def get_players_data_by_position(self, team_id):
    #     url = f"{self.BASE_URL}/players"

    #     headers = self.HEADERS

    #     params = {"team": team_id, "season": 2021}

    #     # Make the API request
    #     response = requests.get(url, headers=headers, params=params)

    #     # Check if the request was successful
    #     if response.status_code == 200:
    #         data = response.json()
    #         players = data.get("response", [])
    #         position_classification = {}

    #         if not players:
    #             print("No player data found.")
    #         else:
    #             for player_data in players:
    #                 player_info = player_data.get("player", {})
    #                 statistics = player_data.get("statistics", [])

    #                 # Extract basic player information
    #                 player_id = player_info.get("id", "N/A")
    #                 name = player_info.get("name", "N/A")
    #                 age = player_info.get("age", "N/A")
    #                 height = player_info.get("height", "N/A")
    #                 weight = player_info.get("weight", "N/A")

    #                 # Extract statistics only for league_id 179
    #                 for stat in statistics:
    #                     league = stat.get("league", {})
    #                     if league.get("id") == int(self.league_id):
    #                         games = stat.get("games", {})
    #                         position = games.get("position", "Unknown")

    #                         player_entry = {
    #                             "Player ID": player_id,
    #                             "Name": name,
    #                             "Age": age,
    #                             "Height": height,
    #                             "Weight": weight,
    #                             "Games": games,
    #                             "Statistics": {
    #                                 "Shots": stat.get("shots", {}),
    #                                 "Goals": stat.get("goals", {}),
    #                                 "Passes": stat.get("passes", {}),
    #                                 "Tackles": stat.get("tackles", {}),
    #                                 "Dribbles": stat.get("dribbles", {}),
    #                                 "Fouls": stat.get("fouls", {}),
    #                                 "Cards": stat.get("cards", {}),
    #                             },
    #                         }

    #                         if position not in position_classification:
    #                             position_classification[position] = []
    #                         position_classification[position].append(player_entry)
    #         return position_classification

    #     else:
    #         print(f"Error: {response.status_code}, {response.text}")
    #         return None

    def get_players_data_by_position(self, team_id):
        url = f"{self.BASE_URL}/players"
        headers = self.HEADERS
        params = {"team": team_id, "season": 2021}

        try:
            print(f"Fetching player data for team ID: {team_id}")
            response = requests.get(url, headers=headers, params=params)
            # response.raise_for_status()  # Raise an exception for HTTP errors
        except requests.RequestException as e:
            print(f"Error fetching player data: {str(e)}")
            return None

        try:
            data = response.json()
            players = data.get("response", [])
            position_classification = {}

            if not players:
                print("No player data found.")
            else:
                print(f"Processing {len(players)} players' data.")
                for player_data in players:
                    player_info = player_data.get("player", {})
                    statistics = player_data.get("statistics", [])

                    player_id = player_info.get("id", "N/A")
                    name = player_info.get("name", "N/A")
                    age = player_info.get("age", "N/A")
                    height = player_info.get("height", "N/A")
                    weight = player_info.get("weight", "N/A")

                    for stat in statistics:
                        league = stat.get("league", {})
                        if league.get("id") == int(self.league_id):
                            games = stat.get("games", {})
                            position = games.get("position", "Unknown")

                            player_entry = {
                                "Player ID": player_id,
                                "Name": name,
                                "Age": age,
                                "Height": height,
                                "Weight": weight,
                                "Games": games,
                                "Statistics": {
                                    "Shots": stat.get("shots", {}),
                                    "Goals": stat.get("goals", {}),
                                    "Passes": stat.get("passes", {}),
                                    "Tackles": stat.get("tackles", {}),
                                    "Dribbles": stat.get("dribbles", {}),
                                    "Fouls": stat.get("fouls", {}),
                                    "Cards": stat.get("cards", {}),
                                },
                            }

                            if position not in position_classification:
                                position_classification[position] = []
                            position_classification[position].append(player_entry)

            print(f"Successfully classified players by position.")
            return position_classification

        except ValueError as ve:
            print(f"JSON decoding error: {str(ve)}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return None

    # def fetch_fixture_players_data(self, fixture_id, team_id):
    #     print("\n\n\n\n caing thisnfunction with the fowing params", dicta)

    #     base_url = f"{self.BASE_URL}/fixtures/players"
    #     headers = self.HEADERS
    #     params = {"fixture": fixture_id}

    #     try:
    #         response = requests.get(base_url, headers=headers, params=params)
    #         if response.status_code == 200:
    #             data = response.json()
    #             info = data.get("response", [])
    #             position_classification = {}

    #             if not info:
    #                 print("No player data found.")
    #             else:
    #                 for team in info:
    #                     team_info = team.get("team", {})
    #                     if team_info["id"] == team_id:
    #                         for player_data in team.get("players", []):
    #                             player_info = player_data.get("player", {})
    #                             statistics = player_data.get("statistics", [])
    #                             player_id = player_info.get("id", "N/A")
    #                             name = player_info.get("name", "N/A")
    #                             for stat in statistics:
    #                                 games = stat.get("games", {})
    #                                 position = games.get("position", "Unknown")
    #                                 player_entry = {
    #                                     "Player ID": player_id,
    #                                     "Name": name,
    #                                     "Games": games,
    #                                     "Statistics": {
    #                                         "Shots": stat.get("shots", {}),
    #                                         "Goals": stat.get("goals", {}),
    #                                         "Passes": stat.get("passes", {}),
    #                                         "Tackles": stat.get("tackles", {}),
    #                                         "Dribbles": stat.get("dribbles", {}),
    #                                         "Fouls": stat.get("fouls", {}),
    #                                         "Cards": stat.get("cards", {}),
    #                                     },
    #                                 }
    #                                 if position not in position_classification:
    #                                     position_classification[position] = []
    #                                 position_classification[position].append(
    #                                     player_entry
    #                                 )

    #             return position_classification
    #         else:
    #             print(f"Error: {response.status_code}")
    #             return None
    #     except requests.RequestException as e:
    #         print(f"Request failed:")
    #         return None

    def fetch_fixture_players_data(self, fixture_id, team_id):

        base_url = f"{self.BASE_URL}/fixtures/players"
        headers = self.HEADERS
        params = {"fixture": fixture_id}

        try:
            print(
                f"Fetching player data for fixture ID: {fixture_id} and team ID: {team_id}"
            )
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
        except requests.RequestException as e:
            print(f"Request failed: {str(e)}")
            return None

        try:
            data = response.json()
            info = data.get("response", [])
            position_classification = {}

            if not info:
                print("No player data found for the specified fixture.")
            else:
                print(f"Processing data for {len(info)} team(s).")
                for team in info:
                    team_info = team.get("team", {})
                    if team_info.get("id") == team_id:
                        print(f"Processing data for team ID: {team_id}")
                        for player_data in team.get("players", []):
                            player_info = player_data.get("player", {})
                            statistics = player_data.get("statistics", [])
                            player_id = player_info.get("id", "N/A")
                            name = player_info.get("name", "N/A")

                            for stat in statistics:
                                games = stat.get("games", {})
                                position = games.get("position", "Unknown")

                                player_entry = {
                                    "Player ID": player_id,
                                    "Name": name,
                                    "Games": games,
                                    "Statistics": {
                                        "Shots": stat.get("shots", {}),
                                        "Goals": stat.get("goals", {}),
                                        "Passes": stat.get("passes", {}),
                                        "Tackles": stat.get("tackles", {}),
                                        "Dribbles": stat.get("dribbles", {}),
                                        "Fouls": stat.get("fouls", {}),
                                        "Cards": stat.get("cards", {}),
                                    },
                                }

                                if position not in position_classification:
                                    position_classification[position] = []
                                position_classification[position].append(player_entry)
                print("Player data successfully classified by position.")
            return position_classification
        except ValueError as ve:
            print(f"JSON decoding error: {str(ve)}")
            return None
        except KeyError as ke:
            print(f"Missing expected key: {str(ke)}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return None

    # def fetch_head_to_head_statistics(self, team1_id, team2_id):
    #     """
    #     Fetch and return head-to-head fixture statistics and details for two teams incuding the rattings for the payers.
    #     this maes 10 requests
    #     """
    #     base_url = f"{self.BASE_URL}/fixtures/headtohead"
    #     headers = self.HEADERS
    #     params = {"h2h": f"{team1_id}-{team2_id}"}

    #     response = requests.get(base_url, headers=headers, params=params)

    #     if response.status_code == 200:
    #         data = response.json()
    #         sliced_data = dict(list(data.items())[1:])  # Skipping the first item
    #         fixtures = data.get("response", [])
    #         sorted_data = sorted(
    #             fixtures, key=lambda x: parser.parse(x["fixture"]["date"]), reverse=True
    #         )
    #         fixtures = sorted_data[:4]
    #         results = []

    #         for fixture in fixtures:
    #             fixture_id = fixture["fixture"]["id"]
    #             league_id = fixture["league"]["id"]
    #             league_name = fixture["league"]["name"]
    #             home_team = fixture["teams"]["home"]
    #             away_team = fixture["teams"]["away"]
    #             goals = fixture["goals"]
    #             date = fixture["fixture"]["date"]

    #             stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    #             stats_response = requests.get(stats_url, headers=headers)

    #             if stats_response.status_code == 200:
    #                 stats_data = stats_response.json()
    #                 sliced_stats = dict(
    #                     list(stats_data.items())[1:]
    #                 )  # Skipping metadata
    #                 statistics = [
    #                     {
    #                         "team": {
    #                             "name": stat["team"]["name"],
    #                             "id": stat["team"]["id"],
    #                         },
    #                         "statistics": stat["statistics"],
    #                         "player_perfomance": self.fetch_fixture_players_data(
    #                             fixture_id, stat["team"]["id"]
    #                         ),
    #                     }
    #                     for stat in stats_data.get("response", [])
    #                 ]
    #             else:
    #                 print("issue ies here")
    #                 statistics = []

    #             results.append(
    #                 {
    #                     "fixture_id": fixture_id,
    #                     "date": date,
    #                     "league": {"id": league_id, "name": league_name},
    #                     "home_team": {"id": home_team["id"], "name": home_team["name"]},
    #                     "away_team": {"id": away_team["id"], "name": away_team["name"]},
    #                     "goals": goals,
    #                     "statistics": statistics,
    #                 }
    #             )

    #         return {"fixtures": results}
    #     else:
    #         print("there is something wrong somewhere")
    #         return {"error": f"Error: {response.status_code}, {response.text}"}

    def fetch_head_to_head_statistics(self, team1_id, team2_id):
        """
        Fetch and return head-to-head fixture statistics and details for two teams, including player ratings.
        This makes multiple requests to the API.
        """
        print(f"Fetching head-to-head statistics for teams {team1_id} vs {team2_id}.")

        base_url = f"{self.BASE_URL}/fixtures/headtohead"
        headers = self.HEADERS
        params = {"h2h": f"{team1_id}-{team2_id}"}

        # Counter for API requests
        api_request_count = 0

        try:
            # First API request
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            api_request_count += 1  # Increment counter

            data = response.json()
            fixtures = data.get("response", [])
            sorted_data = sorted(
                fixtures, key=lambda x: parser.parse(x["fixture"]["date"]), reverse=True
            )
            fixtures = sorted_data[:4]
            results = []

            for fixture in fixtures:
                fixture_id = fixture["fixture"]["id"]
                league_id = fixture["league"]["id"]
                league_name = fixture["league"]["name"]
                home_team = fixture["teams"]["home"]
                away_team = fixture["teams"]["away"]
                goals = fixture["goals"]
                date = fixture["fixture"]["date"]

                # Fixture statistics request
                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
                try:
                    stats_response = requests.get(stats_url, headers=headers)
                    stats_response.raise_for_status()
                    api_request_count += 1  # Increment counter

                    # Check limit and pause if needed
                    if api_request_count == 8:
                        print(
                            "API limit approaching. first pause in the fetch_head_to_head_statistics def ,Pausing for a while..."
                        )
                        time.sleep(60)  # MUST RETURN

                except requests.RequestException as e:
                    print(
                        f"Failed to fetch statistics for fixture {fixture_id}: {str(e)}"
                    )
                    statistics = []
                else:
                    stats_data = stats_response.json()
                    statistics = [
                        {
                            "team": {
                                "name": stat["team"]["name"],
                                "id": stat["team"]["id"],
                            },
                            "statistics": stat["statistics"],
                            "player_performance": self.fetch_fixture_players_data(
                                fixture_id, stat["team"]["id"]
                            ),
                        }
                        for stat in stats_data.get("response", [])
                    ]

                    # Increment counter for player performance requests
                    for stat in stats_data.get("response", []):
                        api_request_count += 1
                        if api_request_count == 8:
                            print(
                                "API limit approaching. Pausing for a while. second 2nd pause, not so neccesary thoug, when seeing payer ratings in h2h data carry 5..."
                            )
                            time.sleep(
                                60
                            )  # MUST RETURN  # Pause for 60 seconds before continuing

                results.append(
                    {
                        "fixture_id": fixture_id,
                        "date": date,
                        "league": {"id": league_id, "name": league_name},
                        "home_team": {"id": home_team["id"], "name": home_team["name"]},
                        "away_team": {"id": away_team["id"], "name": away_team["name"]},
                        "goals": goals,
                        "statistics": statistics,
                    }
                )

            print(
                f"Successfully processed head-to-head data for {len(results)} fixtures."
            )
            return {"fixtures": results}

        except requests.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": f"Failed to fetch head-to-head data: {str(e)}"}
        except (ValueError, KeyError) as e:
            print(f"Data processing error: {str(e)}")
            return {"error": f"Data processing error: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}

    # def fetch_head_to_head_statistics_with_home_at_home_and_away_at_away(
    #     self, home_team_id, away_team_id, league_id
    # ):
    #     """
    #     Fetch and return head-to-head statistics between two football teams using the API-Sports service.

    #     Returns:
    #         list: A list of dictionaries containing fixture details and their statistics.
    #     """
    #     base_url = f"{self.BASE_URL}/fixtures/headtohead"
    #     headers = self.HEADERS
    #     params = {"h2h": f"{home_team_id}-{away_team_id}"}

    #     response = requests.get(base_url, headers=headers, params=params)
    #     if response.status_code == 200:
    #         data = response.json()
    #         fixtures = data.get("response", [])

    #         # Sort fixtures by date from most recent to oldest
    #         sorted_data = sorted(
    #             fixtures, key=lambda x: parser.parse(x["fixture"]["date"]), reverse=True
    #         )

    #         data_list = []
    #         number_of_games = 0
    #         for fixture in sorted_data:  # Limit iteration to 5 times
    #             if number_of_games >= 5:
    #                 break
    #             if (
    #                 fixture["teams"]["home"]["id"] == int(home_team_id)
    #                 and fixture["teams"]["away"]["id"] == int(away_team_id)
    #                 and fixture["league"]["id"] == int(league_id)
    #             ):
    #                 fixture_id = fixture["fixture"]["id"]

    #                 stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    #                 stats_response = requests.get(stats_url, headers=headers)

    #                 if stats_response.status_code == 200:
    #                     stats_data = stats_response.json().get("response", [])
    #                     fixture_summary = {
    #                         "fixture": fixture,
    #                         "fixture_id": fixture_id,
    #                         "date": fixture["fixture"]["date"],
    #                         "league": fixture["league"]["name"],
    #                         "statistics": stats_data,
    #                     }

    #                     data_list.append(fixture_summary)
    #                     number_of_games += 1
    #                 else:
    #                     print(
    #                         f"Error fetching statistics: {stats_response.status_code}, {stats_response.text}"
    #                     )
    #         return data_list
    #     else:
    #         print(f"Error: {response.status_code}, {response.text}")
    #         None

    def fetch_head_to_head_statistics_with_home_at_home_and_away_at_away(
        self, home_team_id, away_team_id, league_id
    ):
        """
        Fetch and return head-to-head statistics between two football teams using the API-Sports service.

        Args:
            home_team_id (int): ID of the home team.
            away_team_id (int): ID of the away team.
            league_id (int): ID of the league for filtering.

        Returns:
            list: A list of dictionaries containing fixture details and their statistics.
        """
        print(
            f"Fetching head-to-head data for home team {home_team_id} and away team {away_team_id} in league {league_id}."
        )

        base_url = f"{self.BASE_URL}/fixtures/headtohead"
        headers = self.HEADERS
        params = {"h2h": f"{home_team_id}-{away_team_id}"}

        try:
            response = requests.get(base_url, headers=headers, params=params)
            print(
                "we are pausing for the 3rd time,before h2h with h at h and a at a carry 5"
            )
            time.sleep(60)  # MUST RETURN
            response.raise_for_status()  # Raise an error for bad status codes
        except requests.RequestException as e:
            print(f"Failed to fetch head-to-head data: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}

        try:
            data = response.json()
            fixtures = data.get("response", [])
            print(
                f"Retrieved {len(fixtures)} fixtures. Filtering and processing data..."
            )

            # Sort fixtures by date, from most recent to oldest
            sorted_data = sorted(
                fixtures, key=lambda x: parser.parse(x["fixture"]["date"]), reverse=True
            )

            data_list = []
            number_of_games = 0
            for fixture in sorted_data:
                if number_of_games >= 5:
                    break
                if (
                    fixture["teams"]["home"]["id"] == int(home_team_id)
                    and fixture["teams"]["away"]["id"] == int(away_team_id)
                    and fixture["league"]["id"] == int(league_id)
                ):
                    fixture_id = fixture["fixture"]["id"]
                    stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"

                    try:
                        stats_response = requests.get(stats_url, headers=headers)
                        stats_response.raise_for_status()
                    except requests.RequestException as e:
                        print(
                            f"Failed to fetch statistics for fixture {fixture_id}: {str(e)}"
                        )
                        continue

                    stats_data = stats_response.json().get("response", [])
                    fixture_summary = {
                        "fixture": fixture,
                        "fixture_id": fixture_id,
                        "date": fixture["fixture"]["date"],
                        "league": fixture["league"]["name"],
                        "statistics": stats_data,
                    }

                    data_list.append(fixture_summary)
                    number_of_games += 1
                    print(f"Added fixture {fixture_id} to results.")

            print(f"Processed {number_of_games} fixtures for head-to-head statistics.")
            return data_list
        except (ValueError, KeyError) as e:
            print(f"Data processing error: {str(e)}")
            return {"error": f"Data processing error: {str(e)}"}

    # def home_run_and_away_run(self, team_id, is_home=True):
    #     """
    #     Fetch past fixtures (home or away) for a specific team and return relevant data.

    #     Returns:
    #         list: A list of dictionaries containing fixture and statistics information.
    #     """
    #     base_url = f"{self.BASE_URL}/fixtures"
    #     headers = self.HEADERS
    #     params = {"team": team_id, "season": 2023}

    #     response = requests.get(base_url, headers=headers, params=params)
    #     fixture_count = 4
    #     league_id = self.league_id
    #     if response.status_code == 200:
    #         data = response.json()
    #         fixtures = data.get("response", [])

    #         # Filter fixtures based on the is_home parameter
    #         filtered_fixtures = [
    #             fixture
    #             for fixture in fixtures
    #             if (
    #                 (is_home and fixture["teams"]["home"]["id"] == int(team_id))
    #                 or (not is_home and fixture["teams"]["away"]["id"] == int(team_id))
    #             )
    #             and fixture["league"]["id"] == int(league_id)
    #         ]

    #         # Sort fixtures by date (assuming "fixture.date" is in ISO format) and select the last ones
    #         filtered_fixtures = sorted(
    #             filtered_fixtures, key=lambda x: x["fixture"]["date"], reverse=True
    #         )[:fixture_count]

    #         results = []
    #         for fixture in filtered_fixtures:
    #             fixture_id = fixture["fixture"]["id"]
    #             fixture_data = {
    #                 "fixture": fixture,
    #             }

    #             # Fetch statistics for the fixture
    #             stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    #             stats_response = requests.get(stats_url, headers=headers)

    #             if stats_response.status_code == 200:
    #                 stats_data = stats_response.json()
    #                 fixture_data["Statistics"] = [
    #                     {
    #                         "Team": stat.get("team", {}).get("name", "N/A"),
    #                         "Statistics": stat.get("statistics", []),
    #                     }
    #                     for stat in stats_data.get("response", [])
    #                 ]
    #             else:
    #                 fixture_data["Statistics Error"] = (
    #                     f"Error: {stats_response.status_code}, {stats_response.text}"
    #                 )

    #             results.append(fixture_data)

    #         return results
    #     else:
    #         return {"Error": f"Error: {response.status_code}, {response.text}"}

    def home_run_and_away_run(self, team_id, is_home=True):
        """
        Fetch past fixtures (home or away) for a specific team and return relevant data.

        Args:
            team_id (int): The ID of the team to fetch fixtures for.
            is_home (bool): Flag indicating whether to fetch home or away fixtures. Default is True (home).

        Returns:
            list: A list of dictionaries containing fixture and statistics information, or an error message.
        """
        print(f"Fetching {'home' if is_home else 'away'} fixtures for team {team_id}.")

        base_url = f"{self.BASE_URL}/fixtures"
        headers = self.HEADERS
        params = {"team": team_id, "season": 2023}
        fixture_count = 4
        league_id = self.league_id

        try:
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch fixtures: {str(e)}")
            return {"Error": f"Request failed: {str(e)}"}

        try:
            data = response.json()
            fixtures = data.get("response", [])
            print(
                f"Retrieved {len(fixtures)} fixtures for team {team_id}. Filtering data..."
            )

            # Filter based on home/away and league_id
            filtered_fixtures = [
                fixture
                for fixture in fixtures
                if (
                    (is_home and fixture["teams"]["home"]["id"] == int(team_id))
                    or (not is_home and fixture["teams"]["away"]["id"] == int(team_id))
                )
                and fixture["league"]["id"] == int(league_id)
            ]

            # Sort by date and limit the number of results
            filtered_fixtures = sorted(
                filtered_fixtures, key=lambda x: x["fixture"]["date"], reverse=True
            )[:fixture_count]

            results = []
            for fixture in filtered_fixtures:
                fixture_id = fixture["fixture"]["id"]
                fixture_data = {"fixture": fixture}

                # Fetch statistics for each fixture
                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
                try:
                    stats_response = requests.get(stats_url, headers=headers)
                    stats_response.raise_for_status()
                    stats_data = stats_response.json()
                    fixture_data["Statistics"] = [
                        {
                            "Team": stat.get("team", {}).get("name", "N/A"),
                            "Statistics": stat.get("statistics", []),
                        }
                        for stat in stats_data.get("response", [])
                    ]
                except requests.RequestException as e:
                    fixture_data["Statistics Error"] = (
                        f"Failed to fetch statistics for fixture {fixture_id}: {str(e)}"
                    )
                    print(f"Statistics fetch error for fixture {fixture_id}: {str(e)}")

                results.append(fixture_data)

            print(f"Processed {len(results)} fixtures for team {team_id}.")
            return results
        except (ValueError, KeyError) as e:
            print(f"Data processing error: {str(e)}")
            return {"Error": f"Data processing error: {str(e)}"}

    # def get_last_five_fixtures(self, team_id):
    #     """Fetches the last five fixtures for a given team ID."""
    # url = f"{self.BASE_URL}/fixtures"
    # params = {"team": team_id, "season": 2021}
    # response = requests.get(url, headers=self.HEADERS, params=params)
    # self.fixture_response = response.json()
    # return response.json()

    # def get_fixture_statistics(self, fixture_id):
    #     """Fetches statistics for a specific fixture ID."""
    #     url = f"{self.BASE_URL}/fixtures/statistics"
    #     params = {"fixture": fixture_id}
    #     response = requests.get(url, headers=self.HEADERS, params=params)
    #     self.statistics_response = response.json()
    #     return response.json()

    def get_last_five_fixtures(self, team_id):
        """Fetches the last five fixtures for a given team ID."""
        url = f"{self.BASE_URL}/fixtures"
        params = {"team": team_id, "season": 2021}

        try:
            response = requests.get(url, headers=self.HEADERS, params=params)
            response.raise_for_status()  # Check for HTTP errors
            self.fixture_response = response.json()  # Parse JSON response
            return response.json()

        except (
            requests.exceptions.RequestException
        ) as e:  # Handle request errors (network, timeouts, etc.)
            print(f"Error fetching fixtures for team ID {team_id}: {str(e)}")
            return {}  # Return empty dict in case of error

        except ValueError as e:  # Handle errors in decoding JSON
            print(f"Error decoding JSON response: {str(e)}")
            return {}  # Return empty dict in case of error

    def get_fixture_statistics(self, fixture_id):
        """
        Fetches statistics for a specific fixture ID.

        Args:
            fixture_id (int): The ID of the fixture.

        Returns:
            dict: A dictionary containing the statistics data or an error message.
        """
        url = f"{self.BASE_URL}/fixtures/statistics"
        params = {"fixture": fixture_id}

        try:
            response = requests.get(url, headers=self.HEADERS, params=params)
            response.raise_for_status()
            data = response.json()
            self.statistics_response = data.get("response", [])
            return {"statistics": self.statistics_response}
        except requests.RequestException as e:
            print(f"Error fetching statistics for fixture {fixture_id}: {str(e)}")
            return {"Error": f"Request failed: {str(e)}"}

    # def fetch_data_for_team(self, team_id, is_home=True):
    #     """Fetches last five fixtures and their statistics for a team."""
    #     number_of_games = 5
    #     fixtures = self.get_last_five_fixtures(team_id)
    #     stats_dict = {}
    #     # print("ets chec if fitters is empty", fixtures)# debugging statement
    #     game_count = 0

    #     if fixtures.get("response"):
    #         if is_home:
    #             self.last_five_home_fixtures = fixtures
    #         else:
    #             self.last_five_away_fixtures = fixtures
    #         # while number_of_games >=0:

    #         for fixture in fixtures["response"]:
    #             if game_count >= number_of_games:
    #                 break

    #             fixture_id = fixture["fixture"]["id"]
    #             statistics = self.get_fixture_statistics(fixture_id)

    #             # Store fixture details and statistics
    #             stats_dict[fixture_id] = {
    #                 "fixture_details": fixture,
    #                 "statistics": statistics,
    #             }
    #             game_count += 1
    #     else:
    #         pprint.pprint(f"No fixtures found for team ID {team_id}.")
    #         if is_home:
    #             self.last_five_home_fixtures = None
    #         else:
    #             self.last_five_away_fixtures = None

    #     return stats_dict

    def fetch_data_for_team(self, team_id, is_home=True):
        """
        Fetches the last five fixtures and their statistics for a specific team.

        Args:
            team_id (int): The ID of the team.
            is_home (bool): True for home fixtures, False for away fixtures.

        Returns:
            dict: A dictionary mapping fixture IDs to fixture details and statistics.
        """
        number_of_games = 5
        fixtures = self.get_last_five_fixtures(team_id)
        stats_dict = {}
        game_count = 0

        if fixtures.get("response"):
            if is_home:
                self.last_five_home_fixtures = fixtures
            else:
                self.last_five_away_fixtures = fixtures
            print("the 5th pause to aoid api imit carry 2.......")
            time.sleep(60)  # MUST RETURN
            for fixture in fixtures["response"]:
                if game_count >= number_of_games:
                    break

                fixture_id = fixture["fixture"]["id"]
                statistics = self.get_fixture_statistics(fixture_id)

                # Store fixture details and statistics
                stats_dict[fixture_id] = {
                    "fixture_details": fixture,
                    "statistics": statistics,
                }
                game_count += 1
        else:
            print(f"No fixtures found for team ID {team_id}.")
            if is_home:
                self.last_five_home_fixtures = None
            else:
                self.last_five_away_fixtures = None

        return stats_dict

    # def statistics_extraction(self):
    #     fixtures = self.last_five_home_fixtures
    #     # print(
    #     #     "this is the dadadadadadadadadadadadadadadadadadadadadadadata type",
    #     #     fixtures,
    #     # )# debugging statement

    #     if fixtures.get("response"):
    #         for fixture in fixtures["response"]:
    #             fixture_id = fixture["fixture"]["id"]
    #             if fixture_id in self.home_stats_dict:
    #                 statistics = self.home_stats_dict[fixture_id]

    #                 self.fixtures_data[fixture_id] = (
    #                     statistics  # Store each fixture's stats
    #                 )

    #                 # print(f"Fixture ID: {fixture_id}")# debugging statement

    #     else:
    #         print("No fixtures found for the team.")

    #     return self.fixtures_data

    def statistics_extraction(self):
        """
        Extracts and stores statistics for the last five home fixtures.

        Returns:
            dict: A dictionary mapping fixture IDs to their statistics.
        """
        fixtures = self.last_five_home_fixtures
        if not fixtures or not fixtures.get("response"):
            print("No fixtures£££££££££££££££££ found for the team.")
            return {}
        if fixtures:
            print("&&&&&&&&&&&&&&& yes fixtures are avaiabe")
        else:
            print("&&&&&&&&&&&&&&&&&&&& no fixture my friend")
        if fixtures.get("response"):
            print("&&&&&&&&&&&&&&& yes fixtures.get(response) are avaiabe")

            for fixture in fixtures["response"]:
                fixture_id = fixture["fixture"]["id"]
                if fixture_id in self.home_stats_dict:
                    print(
                        "this are the home stat dicts&&&&&&",
                        self.home_stats_dict.keys(),
                    )
                    print("&&&&&& just registered a fix", fixture_id)
                    statistics = self.home_stats_dict[fixture_id]  # introduced
                    self.fixtures_data[fixture_id] = (
                        statistics  # Store each fixture's stats
                    )

        else:
            print("&&&&&&&&&&&&&&&&&&&& no fixtures.get(response) my friend")

        return self.fixtures_data

    # def extract_teams_info_from_fixtures(self, fixtures_data):
    #     extracted_info = {}
    #     # print("this is fixdata", fixtures_data)# debugging statement
    #     if fixtures_data:
    #         for fixture_id, fixture_data in fixtures_data.items():
    #             statistics = fixture_data.get(
    #                 "statistics", {}
    #             )  # different from bu print but wors,tiyo
    #             response = statistics.get("response", [])

    #             fixture_info = {"Fixture ID": fixture_id, "Teams": {}}
    #             # print(
    #             #     "\n \n £££££££££££££££££££££££££££££££££££££££this is response",
    #             #     response,
    #             #     "and its ength is ",
    #             #     len(response),
    #             # )# debugging statement
    #             if len(response) >= 2:
    #                 home_team = response[0].get("team", {})
    #                 away_team = response[1].get("team", {})

    #                 fixture_info["Teams"]["Home Team"] = {
    #                     "Team Name": home_team.get("name", "Unknown"),
    #                     "Team ID": home_team.get("id", "Unknown"),
    #                 }
    #                 fixture_info["Teams"]["Away Team"] = {
    #                     "Team Name": away_team.get("name", "Unknown"),
    #                     "Team ID": away_team.get("id", "Unknown"),
    #                 }
    #             else:
    #                 print(
    #                     "\n \n omera@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ not greater than 2"
    #                 )

    #             extracted_info[fixture_id] = fixture_info
    #             # print(
    #             #     "------------\\\\\\\\\\\\\\\\----------------the state of extracted info",
    #             #     extracted_info,
    #             # )# debugging statement

    #         return extracted_info
    #     else:
    #         print("the function extract_teams_info_from_fixtures is haing some prob")
    #         return None

    def extract_teams_info_from_fixtures(self, fixtures_data):
        """
        Extracts team information (home and away teams) from fixture data.

        Args:
            fixtures_data (dict): A dictionary containing fixture details, including statistics.

        Returns:
            dict: A dictionary with fixture IDs as keys and team information as values.
        """
        extracted_info = {}

        if not fixtures_data:
            print("No fixture data available.")
            return None
        else:
            print("&&&&&&&&&&&&&&& oh yes fix data is avaiabe")
            print("this is the data source:", fixture_data)
            for fixture_id, fixture_data in fixtures_data.items():
                statistics = fixture_data.get("statistics", {})
                if statistics:
                    print("&&&&&&&&& the statts are avaiabe too")
                else:
                    print("no stats my dear &&&&&&&&&&")
                response = statistics.get("response", [])
                if response:
                    print("&&&&&&&&&&&&&& the response for this ia avaiabe")
                else:
                    print("&&&&&&&&&&&&&&&&&& no response to show")

                fixture_info = {"Fixture ID": fixture_id, "Teams": {}}

                if len(response) >= 2:
                    home_team = response[0].get("team", {})
                    away_team = response[1].get("team", {})

                    fixture_info["Teams"]["Home Team"] = {
                        "Team Name": home_team.get("name", "Unknown"),
                        "Team ID": home_team.get("id", "Unknown"),
                    }
                    fixture_info["Teams"]["Away Team"] = {
                        "Team Name": away_team.get("name", "Unknown"),
                        "Team ID": away_team.get("id", "Unknown"),
                    }

                else:
                    print(f"Fixture {fixture_id} does not have enough team data.")

                extracted_info[fixture_id] = fixture_info

        return extracted_info

    # def get_first_away_and_home_fixtures(self, fixtures, team_name):
    #     first_away = None
    #     first_home = None
    #     # print("yawa this are the fixtures", fixtures)# debugging statement
    #     # print("this var reached and here they the team name-->\n", team_name)# debugging statement
    #     for fixture_id, fixture in fixtures.items():
    #         away_team = fixture["Teams"]["Away Team"]
    #         home_team = fixture["Teams"]["Home Team"]
    #         # print(
    #         #     "upto here things are great we have away_team--> \n",
    #         #     away_team,
    #         #     "\n and home_team -->",
    #         #     home_team,
    #         # )# debugging statement

    #         if away_team["Team Name"] == team_name and first_away is None:
    #             first_away = {
    #                 "Fixture ID": fixture_id,
    #                 "Opponent Team ID": home_team["Team ID"],
    #                 "Opponent Team Name": home_team["Team Name"],
    #             }

    #         if home_team["Team Name"] == team_name and first_home is None:
    #             first_home = {
    #                 "Fixture ID": fixture_id,
    #                 "Opponent Team ID": away_team["Team ID"],
    #                 "Opponent Team Name": away_team["Team Name"],
    #             }

    #         if first_away and first_home:
    #             break

    #     return first_away, first_home

    def get_first_away_and_home_fixtures(self, fixtures, team_name):
        first_away = None
        first_home = None

        if not fixtures:
            logging.error("No fixtures provided.")
            print("nooooooooo fixtures&&&&&&&&&&&&&&")
            return None, None
        else:
            print(
                "yes££££££££££££££££££££££££££££ fixures provided and the  home team is ",
                team_name,
            )
            # Loop through fixtures to find the first home and away games for the team
            for fixture_id, fixture in fixtures.items():
                print(
                    "fixture&&&&&&&&&&&&&&& items has this, trancuated to 2",
                )

                away_team = fixture.get("Teams", {}).get("Away Team", {})
                home_team = fixture.get("Teams", {}).get("Home Team", {})

                if not away_team or not home_team:
                    logging.warning(
                        f"Missing team information in fixture ID {fixture_id}."
                    )
                    print(
                        f"Missing&&&&&&&&&& team information in fixture ID {fixture_id}."
                    )
                    continue

                # Check if the team is the away team
                if away_team.get("Team Name") == team_name and first_away is None:
                    first_away = {
                        "Fixture ID": fixture_id,
                        "Opponent Team ID": home_team.get("Team ID"),
                        "Opponent Team Name": home_team.get("Team Name"),
                    }

                # Check if the team is the home team
                if home_team.get("Team Name") == team_name and first_home is None:
                    first_home = {
                        "Fixture ID": fixture_id,
                        "Opponent Team ID": away_team.get("Team ID"),
                        "Opponent Team Name": away_team.get("Team Name"),
                    }

                # If both first away and home games are found, break the loop
                if first_away and first_home:
                    print(
                        "this is first awayyy££££££££££££££££££££££££££",
                        first_away,
                        "\n",
                        type(first_away),
                        "\n first home",
                        first_home,
                        type(first_home),
                    )
                    break

        if not first_away:
            logging.warning(
                f"First away fixture not found for team£££££££££££££££££££ {team_name}."
            )
        if not first_home:
            logging.warning(
                f"First home fixture not found for teamEEEEEEEEEEEEEEEEEEEEE {team_name}."
            )

        return first_away, first_home

    # def teams_info(self):
    #     fix_d = self.statistics_extraction()
    #     # print("\n \n \n \nis this team info empty?", fix_d)
    #     teams_info = self.extract_teams_info_from_fixtures(fix_d)
    #     return teams_info

    # def team_name(self):
    #     return self.home_team_name

    # def first_away(self):
    #     tim = self.get_first_away_and_home_fixtures(self.teams_info(), self.team_name())
    #     # print("this what var tim has", tim)# debugging statement
    #     first_away = tim[0]
    #     return first_away

    # def first_home(self):
    #     tim = self.get_first_away_and_home_fixtures(self.teams_info(), self.team_name())
    #     first_home = tim[1]
    #     return first_home

    def teams_info(self):
        """Fetches the team info by extracting it from fixtures data."""
        fix_d = self.statistics_extraction()  # Get fixture data
        if not fix_d:
            logging.error("No fixture data available££££££££££££££££££££££££.")
            return None
        else:
            print("&&&&&&&&&&&yes, extracted fix_d")
        teams_info = self.extract_teams_info_from_fixtures(fix_d)
        if not teams_info:
            logging.error(
                "Failed££££££££££££££££££ to extract team information from fixtures."
            )
            print("Failed&&&&&&&&&&&&&&& to extract team information from fixtures.")
        else:
            print("&&&&&&&&&&&yes, extracted team_info")
        return teams_info

    def team_name(self):
        """Returns the home team name."""
        return self.home_team_name

    def first_away(self):
        """Fetches the first away fixture and returns it."""
        try:
            tim = self.get_first_away_and_home_fixtures(
                self.teams_info(), self.team_name()
            )
            if tim and tim[0]:
                return tim[0]
            else:
                logging.warning(
                    f"First away fixture not found for team {self.team_name()}."
                )
                print(
                    f"First away&&&&&&&&&&&&&&&&& fixture not found for team {self.team_name()}."
                )
                return None
        except Exception as e:
            logging.error(f"Error occurred while fetching first away fixture: {e}")
            return None

    def first_home(self):
        """Fetches the first home fixture and returns it."""
        try:
            teams_info = self.teams_info()
            team_name = self.team_name()
            logging.debug(f"Teams Info£££££££££££££££££££££££££££: {teams_info}")
            logging.debug(f"Team Name££££££££££££££££££££££££££££: {team_name}")
            tim = self.get_first_away_and_home_fixtures(
                self.teams_info(), self.team_name()
            )
            if tim and tim[1]:
                return tim[1]
            else:
                logging.warning(
                    f"First home fixture not found for team {self.team_name()}."
                )
                return None
        except Exception as e:
            logging.error(f"Error occurred while fetching first home fixture: {e}")
            return None

    # def save_statistics(self, first_away, first_home, constant_team_id):

    #     # Fetch statistics for First Away Fixture
    #     # away_fixture_stats = get_fixture_statistics(first_away["Fixture ID"])
    #     print(
    #         "the first away reached this function and here it is--->",
    #         first_away,
    #         "\n then this is the first home---->",
    #         first_home,
    #         "\n constant id is ",
    #         constant_team_id,
    #         type(constant_team_id),
    #     )  # debugging statement
    #     constant_team_id = int(constant_team_id)
    #     # first away mean the target team was away whereas first home means the target team was home
    #     if self.fixtures_data[first_away["Fixture ID"]]:
    #         teams = self.fixtures_data[first_away["Fixture ID"]]["statistics"][
    #             "response"
    #         ]
    #         # print(
    #         #     "for now this is the teams,,,,,,,,,,,,,,,,,,,,,,,,,,,",
    #         #     json.dumps(teams, indent=4),
    #         # )# debugging statement
    #         for team in teams:
    #             team_id = team["team"]["id"]
    #             team_name = team["team"]["name"]
    #             print(
    #                 "||||||||||||||||||||||||||||||||||||||,this is team_name for now",
    #                 team_name,
    #             )
    #             stats = team["statistics"]

    #             if (
    #                 team_id == constant_team_id
    #             ):  # Stats for the constant team (e.g., Napoli)
    #                 # print(
    #                 #     "::::::::::::::::::::::::::::::::::::::::::::: data for const"
    #                 # )# debugging statement
    #                 dictna = {
    #                     "team_id": team_id,
    #                     "team_name": team_name,
    #                     "fixture_data": self.fixtures_data[first_away["Fixture ID"]][
    #                         "fixture_details"
    #                     ]["fixture"]["id"],
    #                 }
    #                 self.mutual["away"]["guest_vs_home"]["home_data"] = stats
    #                 self.mutual["away"]["guest_vs_home"]["home_ratings"] = (
    #                     self.fetch_fixture_players_data(

    #                         self.fixtures_data[first_away["Fixture ID"]][
    #                             "fixture_details"
    #                         ]["fixture"]["id"],
    #                         team_id,
    #                     )
    #                 )

    #                 self.mutual["away"]["guest_vs_home"]["match"][
    #                     "home_name"
    #                 ] = f"home team name+++++---- {team_name}"
    #             elif (
    #                 team_id == first_away["Opponent Team ID"]
    #             ):  # Stats for the opponent
    #                 dictna = {
    #                     "team_id": team_id,
    #                     "team_name": team_name,
    #                     "fixture_data": self.fixtures_data[first_away["Fixture ID"]][
    #                         "fixture_details"
    #                     ]["fixture"]["id"],
    #                 }

    #                 self.mutual["away"]["guest_vs_home"]["guest_data"] = stats
    #                 self.mutual["away"]["guest_vs_home"]["guest_ratings"] = (
    #                     self.fetch_fixture_players_data(

    #                         self.fixtures_data[first_away["Fixture ID"]][
    #                             "fixture_details"
    #                         ]["fixture"]["id"],
    #                         team_id,
    #                     )
    #                 )
    #                 self.mutual["away"]["guest_vs_home"]["match"][
    #                     "guest_name"
    #                 ] = f"guest team name+++++++---- {team_name}"

    #     else:
    #         print(
    #             f"-/-/-/--/--//--/-/-//-/-/-/---/-/-/- fixture data here \n NO FIXURES DATA"
    #         )

    #     # Fetch statistics for First Home Fixture
    #     # home_fixture_stats = get_fixture_statistics(first_home["Fixture ID"])
    #     if self.fixtures_data[first_home["Fixture ID"]]:
    #         teams = self.fixtures_data[first_home["Fixture ID"]]["statistics"][
    #             "response"
    #         ]

    #         for team in teams:
    #             team_id = team["team"]["id"]
    #             team_name = team["team"]["name"]
    #             stats = team["statistics"]
    #             print(
    #                 "||||||||||||||||||||||||||||||||||||||,this is team_name for now number 2",
    #                 team_name,
    #             )
    #             if (
    #                 team_id == constant_team_id
    #             ):  # Stats for the constant team (e.g., Napoli)
    #                 dictna = {
    #                     "team_id": team_id,
    #                     "team_name": team_name,
    #                     "fixture_data": self.fixtures_data[first_home["Fixture ID"]][
    #                         "fixture_details"
    #                     ]["fixture"]["id"],
    #                 }

    #                 self.mutual["home"]["home_vs_guest"]["home_data"] = stats
    #                 self.mutual["home"]["home_vs_guest"]["home_ratings"] = (
    #                     self.fetch_fixture_players_data(

    #                         self.fixtures_data[first_home["Fixture ID"]][
    #                             "fixture_details"
    #                         ]["fixture"]["id"],
    #                         team_id,
    #                     )
    #                 )
    #                 self.mutual["home"]["home_vs_guest"]["match"][
    #                     "home_name"
    #                 ] = f"home team name+++++---- {team_name}"

    #             elif (
    #                 team_id == first_home["Opponent Team ID"]
    #             ):  # Stats for the opponent
    #                 dictna = {
    #                     "team_id": team_id,
    #                     "team_name": team_name,
    #                     "fixture_data": self.fixtures_data[first_home["Fixture ID"]][
    #                         "fixture_details"
    #                     ]["fixture"]["id"],
    #                 }

    #                 self.mutual["home"]["home_vs_guest"]["guest_data"] = stats
    #                 self.mutual["home"]["home_vs_guest"]["guest_ratings"] = (
    #                     self.fetch_fixture_players_data(

    #                         self.fixtures_data[first_home["Fixture ID"]][
    #                             "fixture_details"
    #                         ]["fixture"]["id"],
    #                         team_id,
    #                     )
    #                 )
    #                 self.mutual["home"]["home_vs_guest"]["match"][
    #                     "guest_name"
    #                 ] = f"guest team name+++++++---- {team_name}"

    #     return self.mutual

    def save_statistics(self, first_away, first_home, constant_team_id):
        try:
            # Fetch statistics for First Away Fixture
            logging.info(
                "The first away reached this function and here it is --> %s", first_away
            )
            logging.info("Then this is the first home --> %s", first_home)
            logging.info(
                "Constant ID is %s, Type: %s", constant_team_id, type(constant_team_id)
            )

            constant_team_id = int(constant_team_id)

            # Fetch data for first away
            if self.fixtures_data[first_away["Fixture ID"]]:
                teams = self.fixtures_data[first_away["Fixture ID"]]["statistics"][
                    "response"
                ]
                for team in teams:
                    team_id = team["team"]["id"]
                    team_name = team["team"]["name"]
                    logging.info("Team Name for Away Fixture: %s", team_name)
                    stats = team["statistics"]

                    if team_id == constant_team_id:
                        dictna = {
                            "team_id": team_id,
                            "team_name": team_name,
                            "fixture_data": self.fixtures_data[
                                first_away["Fixture ID"]
                            ]["fixture_details"]["fixture"]["id"],
                        }
                        self.mutual["away"]["guest_vs_home"]["home_data"] = stats
                        self.mutual["away"]["guest_vs_home"]["home_ratings"] = (
                            self.fetch_fixture_players_data(
                                self.fixtures_data[first_away["Fixture ID"]][
                                    "fixture_details"
                                ]["fixture"]["id"],
                                team_id,
                            )
                        )
                        self.mutual["away"]["guest_vs_home"]["match"][
                            "home_name"
                        ] = f"home team name+++++---- {team_name}"
                    elif team_id == first_away["Opponent Team ID"]:
                        dictna = {
                            "team_id": team_id,
                            "team_name": team_name,
                            "fixture_data": self.fixtures_data[
                                first_away["Fixture ID"]
                            ]["fixture_details"]["fixture"]["id"],
                        }
                        self.mutual["away"]["guest_vs_home"]["guest_data"] = stats
                        self.mutual["away"]["guest_vs_home"]["guest_ratings"] = (
                            self.fetch_fixture_players_data(
                                self.fixtures_data[first_away["Fixture ID"]][
                                    "fixture_details"
                                ]["fixture"]["id"],
                                team_id,
                            )
                        )
                        self.mutual["away"]["guest_vs_home"]["match"][
                            "guest_name"
                        ] = f"guest team name+++++++---- {team_name}"
            else:
                logging.warning(
                    "No fixture data found for away fixture with ID: %s",
                    first_away["Fixture ID"],
                )

            # Fetch statistics for First Home Fixture
            if self.fixtures_data[first_home["Fixture ID"]]:
                teams = self.fixtures_data[first_home["Fixture ID"]]["statistics"][
                    "response"
                ]
                for team in teams:
                    team_id = team["team"]["id"]
                    team_name = team["team"]["name"]
                    stats = team["statistics"]
                    logging.info("Team Name for Home Fixture: %s", team_name)

                    if team_id == constant_team_id:
                        dictna = {
                            "team_id": team_id,
                            "team_name": team_name,
                            "fixture_data": self.fixtures_data[
                                first_home["Fixture ID"]
                            ]["fixture_details"]["fixture"]["id"],
                        }
                        self.mutual["home"]["home_vs_guest"]["home_data"] = stats
                        self.mutual["home"]["home_vs_guest"]["home_ratings"] = (
                            self.fetch_fixture_players_data(
                                self.fixtures_data[first_home["Fixture ID"]][
                                    "fixture_details"
                                ]["fixture"]["id"],
                                team_id,
                            )
                        )
                        self.mutual["home"]["home_vs_guest"]["match"][
                            "home_name"
                        ] = f"home team name+++++---- {team_name}"
                    elif team_id == first_home["Opponent Team ID"]:
                        dictna = {
                            "team_id": team_id,
                            "team_name": team_name,
                            "fixture_data": self.fixtures_data[
                                first_home["Fixture ID"]
                            ]["fixture_details"]["fixture"]["id"],
                        }
                        self.mutual["home"]["home_vs_guest"]["guest_data"] = stats
                        self.mutual["home"]["home_vs_guest"]["guest_ratings"] = (
                            self.fetch_fixture_players_data(
                                self.fixtures_data[first_home["Fixture ID"]][
                                    "fixture_details"
                                ]["fixture"]["id"],
                                team_id,
                            )
                        )
                        self.mutual["home"]["home_vs_guest"]["match"][
                            "guest_name"
                        ] = f"guest team name+++++++---- {team_name}"
            else:
                logging.warning(
                    "No fixture data found for home fixture with ID: %s",
                    first_home["Fixture ID"],
                )

        except Exception as e:
            logging.error("An error occurred while saving statistics: %s", str(e))

        return self.mutual

    def h_team_id(self):
        return self.home_team_id

    # def unown_mutual(self):
    #     mutual = self.save_statistics(self.first_away, self.first_home, self.h_team_id)
    #     return mutual

    # def fetch_h2h_data(self, h2h_combination):
    #     """
    #     Fetches the most recent past head-to-head fixture data for the given combination of teams.

    #     Args:
    #         h2h_combination (str): The team combination in "team1,team2" format.

    #     Returns:
    #         dict or None: The most recent past fixture data or None if no data is found.
    #     """
    #     url = f"{self.BASE_URL}/fixtures/headtohead"
    #     params = {"h2h": h2h_combination}
    #     try:
    #         response = requests.get(url, headers=headers, params=params)
    #         if response.status_code == 200:
    #             data = response.json()
    #             fixtures = data.get("response", [])

    #             if not fixtures:
    #                 logger.info("No fixtures found for the given combination.")
    #                 return None

    #             # Filter for past fixtures only
    #             now = datetime.now(datetime.now().astimezone().tzinfo)
    #             past_fixtures = [
    #                 fixture
    #                 for fixture in fixtures
    #                 if datetime.strptime(
    #                     fixture["fixture"]["date"], "%Y-%m-%dT%H:%M:%S%z"
    #                 )
    #                 <= now
    #             ]

    #             if not past_fixtures:
    #                 logger.info("No past fixtures found for the given combination.")
    #                 return None

    #             # Sort past fixtures by date (most recent first)
    #             past_fixtures.sort(
    #                 key=lambda x: datetime.strptime(
    #                     x["fixture"]["date"], "%Y-%m-%dT%H:%M:%S%z"
    #                 ),
    #                 reverse=True,
    #             )

    #             logger.info(f"Most recent past fixture: {past_fixtures[0]}")
    #             return past_fixtures[0]  # Return the most recent past fixture
    #         else:
    #             logger.error(f"Error fetching H2H data: {response.status_code}")
    #             return None
    #     except Exception as e:
    #         logger.exception(f"An error occurred: {e}")
    #         return None

    def fetch_h2h_data(self, h2h_combination):
        """
        Fetches the most recent past head-to-head fixture data for the given combination of teams.

        Args:
            h2h_combination (str): The team combination in "team1,team2" format.

        Returns:
            dict or None: The most recent past fixture data or None if no data is found.
        """
        url = f"{self.BASE_URL}/fixtures/headtohead"
        params = {"h2h": h2h_combination}
        try:
            response = requests.get(url, headers=self.HEADERS, params=params)
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("response", [])

                if not fixtures:
                    logger.info("No fixtures found for the given combination.")
                    return None

                # Filter for past fixtures only
                now = datetime.now().astimezone()  # Ensures timezone correctness
                past_fixtures = [
                    fixture
                    for fixture in fixtures
                    if datetime.strptime(
                        fixture["fixture"]["date"], "%Y-%m-%dT%H:%M:%S%z"
                    )
                    <= now
                ]

                if not past_fixtures:
                    logger.info("No past fixtures found for the given combination.")
                    return None

                # Sort past fixtures by date (most recent first)
                past_fixtures.sort(
                    key=lambda x: datetime.strptime(
                        x["fixture"]["date"], "%Y-%m-%dT%H:%M:%S%z"
                    ),
                    reverse=True,
                )

                logger.info(f"Most recent past fixture: {past_fixtures[0]}")
                return past_fixtures[0]  # Return the most recent past fixture
            else:
                logger.error(
                    f"Error fetching H2H data: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.exception("An error occurred while fetching H2H data.")
            return None

    # def populate_mutual(
    #     self,
    #     first_away_id,
    #     first_home_id,
    #     constant_team_id=None,
    #     constant_team_name=None,
    # ):
    #     # Fetch H2H for first_away_id
    #     constant_team_id = self.away_team_id
    #     constant_team_name = self.away_team_name

    #     h2h_away_combination = f"{first_away_id}-{constant_team_id}"
    #     latest_fixture_away = self.fetch_h2h_data(h2h_away_combination)
    #     if latest_fixture_away:
    #         fixture_id_away = latest_fixture_away["fixture"]["id"]
    #         stats_away = self.get_fixture_statistics(fixture_id_away)
    #         for stat in stats_away["response"]:
    #             team_id = stat["team"]["id"]
    #             team_name = stat["team"]["name"]
    #             stats = stat["statistics"]
    #             print(
    #                 "||||||||||||||||||||||||||||||||||||||,this is team_name for now number 3",
    #                 team_name,
    #             )
    #             if team_id == int(
    #                 constant_team_id
    #             ):  # Stats for the constant team (e.g., Napoli)
    #                 dictna = {
    #                     "team_id": team_id,
    #                     "team_name": team_name,
    #                     "fixture_data": fixture_id_away,
    #                 }

    #                 self.mutual["away"]["guest_vs_away"]["away_data"] = stats
    #                 self.mutual["away"]["guest_vs_away"]["away_ratings"] = (
    #                     self.fetch_fixture_players_data(
    #                         fixture_id_away, team_id
    #                     )
    #                 )

    #                 self.mutual["away"]["guest_vs_away"]["match"][
    #                     "away_name"
    #                 ] = f"away team name+++++---- {team_name}"
    #             elif team_id == first_away_id:  # Stats for the opponent
    #                 dictna = {
    #                     "team_id": team_id,
    #                     "team_name": team_name,
    #                     "fixture_data": fixture_id_away,
    #                 }

    #                 self.mutual["away"]["guest_vs_away"]["guest_data"] = stats
    #                 self.mutual["away"]["guest_vs_away"]["guest_ratings"] = (
    #                     self.fetch_fixture_players_data(
    #                         fixture_id_away, team_id
    #                     )
    #                 )
    #                 self.mutual["away"]["guest_vs_away"]["match"][
    #                     "guest_name"
    #                 ] = f"guest team name+++++++---- {team_name}"

    #     # Fetch H2H for first_home_id
    #     h2h_home_combination = f"{constant_team_id}-{first_home_id}"
    #     latest_fixture_home = self.fetch_h2h_data(h2h_home_combination)
    #     if latest_fixture_home:
    #         # print(
    #         #     "yes we have the data ////////////////////////////////////////////////////////////////////////"
    #         # )# debugging statement
    #         fixture_id_home = latest_fixture_home["fixture"]["id"]
    #         stats_home = self.get_fixture_statistics(fixture_id_home)
    #         for stat in stats_home["response"]:
    #             team_id = stat["team"]["id"]
    #             team_name = stat["team"]["name"]
    #             stats = stat["statistics"]
    #             print(
    #                 "||||||||||||||||||||||||||||||||||||||,this is team_name for now number 4",
    #                 team_name,
    #             )
    #             if team_id == int(
    #                 constant_team_id
    #             ):  # Stats for the constant team (e.g., Napoli)
    #                 dictna = {
    #                     "team_id": team_id,
    #                     "team_name": team_name,
    #                     "fixture_data": latest_fixture_home["fixture"]["id"],
    #                 }

    #                 self.mutual["home"]["away_vs_guest"]["away_data"] = stats
    #                 self.mutual["home"]["away_vs_guest"]["away_ratings"] = (
    #                     self.fetch_fixture_players_data(
    #                         latest_fixture_home["fixture"]["id"], team_id
    #                     )
    #                 )
    #                 self.mutual["home"]["away_vs_guest"]["match"][
    #                     "away_name"
    #                 ] = f"away team name+++++---- {team_name}"
    #             elif team_id == first_home_id:  # Stats for the opponent
    #                 dictna = {
    #                     "team_id": team_id,
    #                     "team_name": team_name,
    #                     "fixture_data": latest_fixture_home["fixture"]["id"],
    #                 }

    #                 self.mutual["home"]["away_vs_guest"]["guest_data"] = stats
    #                 self.mutual["home"]["away_vs_guest"]["guest_ratings"] = (
    #                     self.fetch_fixture_players_data(
    #                         latest_fixture_home["fixture"]["id"], team_id
    #                     )
    #                 )
    #                 self.mutual["home"]["away_vs_guest"]["match"][
    #                     "guest_name"
    #                 ] = f"guest team name+++++++---- {team_name}"
    #     else:
    #         print(
    #             "NO NO NO we  DONT have the data ////////////////////////////////////////////////////////////////////////"
    #         )
    #     return self.mutual

    def populate_mutual(
        self,
        first_away_id,
        first_home_id,
        constant_team_id=None,
        constant_team_name=None,
    ):
        try:
            # Fetch H2H for first_away_id
            constant_team_id = self.away_team_id
            constant_team_name = self.away_team_name

            h2h_away_combination = f"{first_away_id}-{constant_team_id}"
            latest_fixture_away = self.fetch_h2h_data(h2h_away_combination)

            if latest_fixture_away:
                fixture_id_away = latest_fixture_away["fixture"]["id"]
                stats_away = self.get_fixture_statistics(fixture_id_away)

                for stat in stats_away.get("response", []):
                    try:
                        team_id = stat["team"]["id"]
                        team_name = stat["team"]["name"]
                        stats = stat["statistics"]
                        logger.info(f"Processing away fixture for team: {team_name}")

                        if team_id == int(
                            constant_team_id
                        ):  # Stats for the constant team
                            self.mutual["away"]["guest_vs_away"]["away_data"] = stats
                            self.mutual["away"]["guest_vs_away"]["away_ratings"] = (
                                self.fetch_fixture_players_data(
                                    fixture_id_away, team_id
                                )
                            )
                            self.mutual["away"]["guest_vs_away"]["match"][
                                "away_name"
                            ] = f"away team name+++++---- {team_name}"
                        elif team_id == first_away_id:  # Stats for the opponent
                            self.mutual["away"]["guest_vs_away"]["guest_data"] = stats
                            self.mutual["away"]["guest_vs_away"]["guest_ratings"] = (
                                self.fetch_fixture_players_data(
                                    fixture_id_away, team_id
                                )
                            )
                            self.mutual["away"]["guest_vs_away"]["match"][
                                "guest_name"
                            ] = f"guest team name+++++++---- {team_name}"

                    except KeyError as e:
                        logger.error(
                            f"Missing expected data in away fixture stats: {e}"
                        )
                        continue  # Skip to next iteration on error
            print(
                "pausing for the 6th time fot the api free tier respect,,carryyy 0...................dince this is the ast pause, we have used ony 3................."
            )
            time.sleep(60)  # MUST RETURN
            # Fetch H2H for first_home_id
            h2h_home_combination = f"{constant_team_id}-{first_home_id}"
            latest_fixture_home = self.fetch_h2h_data(h2h_home_combination)

            if latest_fixture_home:
                fixture_id_home = latest_fixture_home["fixture"]["id"]
                stats_home = self.get_fixture_statistics(fixture_id_home)

                for stat in stats_home.get("response", []):
                    try:
                        team_id = stat["team"]["id"]
                        team_name = stat["team"]["name"]
                        stats = stat["statistics"]
                        logger.info(f"Processing home fixture for team: {team_name}")

                        if team_id == int(
                            constant_team_id
                        ):  # Stats for the constant team
                            self.mutual["home"]["away_vs_guest"]["away_data"] = stats
                            self.mutual["home"]["away_vs_guest"]["away_ratings"] = (
                                self.fetch_fixture_players_data(
                                    fixture_id_home, team_id
                                )
                            )
                            self.mutual["home"]["away_vs_guest"]["match"][
                                "away_name"
                            ] = f"away team name+++++---- {team_name}"
                        elif team_id == first_home_id:  # Stats for the opponent
                            self.mutual["home"]["away_vs_guest"]["guest_data"] = stats
                            self.mutual["home"]["away_vs_guest"]["guest_ratings"] = (
                                self.fetch_fixture_players_data(
                                    fixture_id_home, team_id
                                )
                            )
                            self.mutual["home"]["away_vs_guest"]["match"][
                                "guest_name"
                            ] = f"guest team name+++++++---- {team_name}"

                    except KeyError as e:
                        logger.error(
                            f"Missing expected data in home fixture stats: {e}"
                        )
                        continue  # Skip to next iteration on error

            else:
                logger.error("No fixture data found for home fixture.")

            return self.mutual

        except Exception as e:
            logger.exception(f"An error occurred while populating mutual data: {e}")
            return self.mutual

    # def first_away_id(self):
    #     first_away_id = self.first_away()
    #     first_away_id = first_away_id["Opponent Team ID"]  # Replace with actual ID
    #     return first_away_id

    # def first_home_id(self):
    #     first_home_id = self.first_home()
    #     first_home_id = first_home_id["Opponent Team ID"]  # Replace with actual ID
    #     return first_home_id

    def first_away_id(self):
        try:
            first_away_id = self.first_away()
            first_away_id = first_away_id.get(
                "Opponent Team ID", None
            )  # Safely access the ID
            if first_away_id is None:
                logger.error("Opponent Team ID for away team not found.")
            return first_away_id
        except Exception as e:
            logger.exception(f"Error fetching first away team ID: {e}")
            return None

    def first_home_id(self):
        try:
            first_home_id = self.first_home()
            first_home_id = first_home_id.get(
                "Opponent Team ID", None
            )  # Safely access the ID
            if first_home_id is None:
                logger.error("Opponent Team ID for home team not found.")
            return first_home_id
        except AttributeError as e:
            logger.exception(
                "AttributeError: An issue with accessing properties or methods occurred."
            )
        except TypeError as e:
            logger.exception(
                "TypeError: Likely caused by incorrect type handling or method calls."
            )
        except Exception as e:
            logger.exception(f"Unhandled error fetching first home team ID: {e}")
        return None

    #     def receive_match(self, match_data):
    #         """
    #         This method receives match data and stores it in instance variables
    #         """
    #         self.match_id = match_data.get("id")
    #         self.date = match_data.get("date")
    #         self.venue = match_data.get("venue")
    #         self.city = match_data.get("venue_city")
    #         self.league_id = match_data.get("league")
    #         self.home_team_name = match_data.get("home_team_name")
    #         self.away_team_name = match_data.get("away_team_name")
    #         self.home_team_logo = match_data.get("home_team_logo")
    #         self.away_team_logo = match_data.get("away_team_logo")
    #         self.home_team_id = match_data.get("home_team_id")
    #         self.away_team_id = match_data.get("away_team_id")

    #         # Fetch and store weather data
    #         forecast = self.fetch_forecast(self.city, self.date)
    #         if forecast:
    #             temperature_kelvin = forecast["main"]["temp"]
    #             temperature_celsius = temperature_kelvin - 273.15
    #             feels_like_kelvin = forecast["main"]["feels_like"]
    #             feels_like_celsius = feels_like_kelvin - 273.15
    #             humidity = forecast["main"]["humidity"]
    #             weather_description = forecast["weather"][0]["description"]
    #             wind_speed = forecast["wind"]["speed"]
    #             rain = forecast.get("rain", {}).get("3h", 0)

    #             self.weather = {
    #                 "temperature": round(temperature_celsius, 2),
    #                 "feels_like": round(feels_like_celsius, 2),
    #                 "humidity": humidity,
    #                 "weather_description": weather_description.capitalize(),
    #                 "wind_speed": wind_speed,
    #                 "rain": rain,
    #             }
    #         else:
    #             self.weather = None
    #             self.weather_error = "Weather data not available."

    #         # Fetch and store match odds
    #         odds = self.fetch_match_odds(self.match_id)
    #         # odds = None
    #         if odds:
    #             self.odds = odds
    #         else:
    #             self.odds = None

    #         avg_goals = self.fetch_average_goals_per_match(league_id=self.league_id)
    #         # avg_goals = None
    #         if avg_goals:
    #             self.avg_goals = avg_goals
    #         else:
    #             avg_goals = None

    #         h2h_data = self.fetch_head_to_head_statistics(
    #             self.home_team_id, self.away_team_id
    #         )
    #         # h2h_data = None
    #         if h2h_data:
    #             self.h2h = h2h_data

    #         head_to_head_statistics_with_home_at_home_and_away_at_away = (
    #             self.fetch_head_to_head_statistics_with_home_at_home_and_away_at_away(
    #                 self.home_team_id, self.away_team_id, self.league_id
    #             )
    #         )

    #         # head_to_head_statistics_with_home_at_home_and_away_at_away = None
    #         if head_to_head_statistics_with_home_at_home_and_away_at_away:
    #             self.head_to_head_statistics_with_home_at_home_and_away_at_away = (
    #                 head_to_head_statistics_with_home_at_home_and_away_at_away
    #             )

    #         print("trying to avoid api request imit")
    #         time.sleep(60)

    #         home_run = self.home_run_and_away_run(self.home_team_id, True)
    #         if home_run:
    #             self.home_run = home_run
    #         away_run = self.home_run_and_away_run(self.away_team_id, False)
    #         if away_run:
    #             self.away_run = away_run

    #         print(
    #             "immited to 4 games,waiting for a minitue as we fetch home run and away run"
    #         )
    #         time.sleep(60)
    #         home_team_player_ratings_sesason = self.get_players_data_by_position(
    #             self.home_team_id
    #         )
    #         if home_team_player_ratings_sesason:
    #             self.home_team_player_ratings_sesason = home_team_player_ratings_sesason

    #         away_team_player_ratings_sesason = self.get_players_data_by_position(
    #             self.away_team_id
    #         )
    #         if away_team_player_ratings_sesason:
    #             self.away_team_player_ratings_sesason = away_team_player_ratings_sesason

    #         # print("Fetching data for the home team...")

    #         home_stats_dict = self.fetch_data_for_team(self.home_team_id, is_home=True)
    #         # home_stats_dict = None
    #         if home_stats_dict:
    #             self.home_stats_dict = home_stats_dict
    #             # print(
    #             #     "this is the nature of the home start dict 444444444444444444444444444444 ",
    #             #     self.home_stats_dict,
    #             # )# debugging statement
    #         else:
    #             self.home_stats_dict = None

    #         print("Waiting for one minute before fetching data for the away team...")
    #         time.sleep(
    #             60
    #         )  # **************************************************************************************************************************
    #         print("Fetching data for the away team...")
    #         away_stats_dict = self.fetch_data_for_team(self.away_team_id, is_home=False)
    #         # away_stats_dict = None
    #         if away_stats_dict:
    #             self.away_stats_dict = away_stats_dict

    #         else:
    #             self.away_stats_dict = None

    #         self.save_statistics(self.first_away(), self.first_home(), self.h_team_id())
    #         time.sleep(60)
    #         self.populate_mutual(self.first_away_id(), self.first_home_id())
    #         self.every_data = {
    #     "fixture": f"{self.home_team_name} vs {self.away_team_name}",
    #     "match_id": self.match_id,
    #     "match_date": self.date,
    #     "venue": self.venue,
    #     "city": self.city,
    #     "league_id": self.league_id,
    #     "home_team_name": self.home_team_name,
    #     "away_team_name": self.away_team_name,
    #     "home_team_logo": self.home_team_logo,
    #     "away_team_logo": self.away_team_logo,
    #     "home_team_id": self.home_team_id,
    #     "away_team_id": self.away_team_id,
    #     "weather": self.weather,
    #     "odds": self.odds,
    #     "average_league_goals": self.avg_goals,
    #     "head_to_head_data": self.h2h,
    #     "head_to_head_statistics_with_home_at_home_and_away_at_away": self.head_to_head_statistics_with_home_at_home_and_away_at_away,
    #     "home_run": self.home_run,
    #     "away_run": self.away_run,
    #     "home_team_player_ratings_sesason": self.home_team_player_ratings_sesason,
    #     "away_team_player_ratings_sesason": self.away_team_player_ratings_sesason,
    #     "home_last_five_fixture_and_stats": self.home_stats_dict,
    #     "away_last_five_fixture_and_stats": self.away_stats_dict,
    #     "mutual": self.mutual,
    # }
    #         self.save_every_data_to_file()
    #         self.print_match_details()

    def receive_match(self, match_data):
        """
        This method receives match data and stores it in instance variables.
        """
        try:
            # Basic match data assignment
            self.match_id = match_data.get("id")
            self.date = match_data.get("date")
            self.venue = match_data.get("venue_name")
            self.city = match_data.get("venue_city")
            self.league_id = match_data.get("league")
            self.home_team_name = match_data.get("home_team_name")
            self.away_team_name = match_data.get("away_team_name")
            self.home_team_logo = match_data.get("home_team_logo")
            self.away_team_logo = match_data.get("away_team_logo")
            self.home_team_id = match_data.get("home_team_id")
            self.away_team_id = match_data.get("away_team_id")

            # Fetch and store weather data
            forecast = self.fetch_forecast(self.city, self.date)
            if forecast:
                temperature_kelvin = forecast["main"]["temp"]
                temperature_celsius = temperature_kelvin - 273.15
                feels_like_kelvin = forecast["main"]["feels_like"]
                feels_like_celsius = feels_like_kelvin - 273.15
                humidity = forecast["main"]["humidity"]
                weather_description = forecast["weather"][0]["description"]
                wind_speed = forecast["wind"]["speed"]
                rain = forecast.get("rain", {}).get("3h", 0)

                self.weather = {
                    "temperature": round(temperature_celsius, 2),
                    "feels_like": round(feels_like_celsius, 2),
                    "humidity": humidity,
                    "weather_description": weather_description.capitalize(),
                    "wind_speed": wind_speed,
                    "rain": rain,
                }
            else:
                self.weather = None
                self.weather_error = "Weather data not available."

            # Fetch and store match odds
            odds = self.fetch_match_odds(self.match_id)
            if odds:
                self.odds = odds
            else:
                self.odds = None

            # Fetch and store average goals per match
            # avg_goals_stats = self.fetch_average_goals_per_match(
            #     league_id=self.league_id
            # )
            # if avg_goals_stats:
            #     self.avg_goals_stats = avg_goals_stats
            # else:
            #     self.avg_goals_stats = None

            # # Fetch head-to-head data
            # h2h_data = self.fetch_head_to_head_statistics(
            #     self.home_team_id, self.away_team_id
            # )
            # if h2h_data:
            #     self.h2h = h2h_data
            # head_to_head_statistics_with_home_at_home_and_away_at_away = (
            #     self.fetch_head_to_head_statistics_with_home_at_home_and_away_at_away(
            #         self.home_team_id, self.away_team_id, self.league_id
            #     )
            # )
            # if head_to_head_statistics_with_home_at_home_and_away_at_away:
            #     self.head_to_head_statistics_with_home_at_home_and_away_at_away = (
            #         head_to_head_statistics_with_home_at_home_and_away_at_away
            #     )

            # # Fetch home and away run data
            # home_run = self.home_run_and_away_run(self.home_team_id, True)
            # if home_run:
            #     self.home_run = home_run
            # print(
            #     "pausing for the 4rth time before fetching away run, carry is 0........"
            # )
            # time.sleep(60)  # MUST RETURN
            # away_run = self.home_run_and_away_run(self.away_team_id, False)
            # if away_run:
            #     self.away_run = away_run

            # logger.info("Fetching player ratings data for home and away teams...")
            # home_team_player_ratings_sesason = self.get_players_data_by_position(
            #     self.home_team_id
            # )
            # if home_team_player_ratings_sesason:
            #     self.home_team_player_ratings_sesason = home_team_player_ratings_sesason

            # away_team_player_ratings_sesason = self.get_players_data_by_position(
            #     self.away_team_id
            # )
            # if away_team_player_ratings_sesason:
            #     self.away_team_player_ratings_sesason = away_team_player_ratings_sesason

            # # Fetch team stats for home and away teams,1//21/21/21/21/2
            # logger.info("Fetching home team statistics...")
            # home_stats_dict = self.fetch_data_for_team(self.home_team_id, is_home=True)
            # if home_stats_dict:
            #     self.home_stats_dict = home_stats_dict
            # else:
            #     self.home_stats_dict = None

            # logger.info("Fetching away team statistics...")
            # away_stats_dict = self.fetch_data_for_team(self.away_team_id, is_home=False)
            # if away_stats_dict:
            #     self.away_stats_dict = away_stats_dict
            # else:
            #     self.away_stats_dict = None

            # # Save all the statistics
            predictions = self.get_match_prediction(self.match_id)
            if predictions:
                self.predictions = predictions
            else:
                None

            # self.save_statistics(self.first_away(), self.first_home(), self.h_team_id())

            # # Populate mutual statistics
            # self.populate_mutual(self.first_away_id(), self.first_home_id())

            # Gather all the data for the match
            self.every_data = {
                "match_details": {
                    "fixture": f"{self.home_team_name} vs {self.away_team_name}",
                    "match_id": self.match_id,
                    "match_date": self.date,
                    "venue": self.venue,
                    "city": self.city,
                    "league_id": self.league_id,
                    "home_team_name": self.home_team_name,
                    "away_team_name": self.away_team_name,
                    "home_team_logo": self.home_team_logo,
                    "away_team_logo": self.away_team_logo,
                    "home_team_id": self.home_team_id,
                    "away_team_id": self.away_team_id,
                },
                "weather": self.weather,
                "odds": self.odds,
                "average_league_goals": self.avg_goals_stats,
                "head_to_head_data": self.h2h,
                "head_to_head_statistics_with_home_at_home_and_away_at_away": self.head_to_head_statistics_with_home_at_home_and_away_at_away,
                "home_run": self.home_run,
                "away_run": self.away_run,
                "home_team_player_ratings_sesason": self.home_team_player_ratings_sesason,
                "away_team_player_ratings_sesason": self.away_team_player_ratings_sesason,
                "home_last_five_fixture_and_stats": self.home_stats_dict,
                "away_last_five_fixture_and_stats": self.away_stats_dict,
                "predictions": self.predictions,
                "mutual": self.mutual,
            }

            # Print match details
            self.print_match_details()
            print(
                "EVERY Data successfully passed to analyze_data.---->----->--->--->--->---->---->---->---->---->----->--->--->--->---->---->---->---->"
            )

            return self.every_data
        except Exception as e:
            logger.exception(
                f"Error processing match data for match_id: {self.match_id} - {e}"
            )

    def print_match_details(self):
        """
        This method prints the stored match details.
        """
        try:
            logger.info(f"league_id--{self.league_id}")
            logger.info(f"Match ID: {self.match_id}")
            logger.info(f"Match: {self.home_team_name} vs {self.away_team_name}")
            logger.info(f"Date: {self.date}")
            logger.info(f"Venue: {self.venue}")
            logger.info(f"City: {self.city}")

            if self.weather:
                logger.info("Weather Data:")
                logger.info(f"  - Temperature: {self.weather['temperature']}°C")
                logger.info(f"  - Feels Like: {self.weather['feels_like']}°C")
                logger.info(f"  - Humidity: {self.weather['humidity']}%")
                logger.info(f"  - Weather: {self.weather['weather_description']}")
                logger.info(f"  - Wind Speed: {self.weather['wind_speed']} m/s")
                logger.info(f"  - Rain Volume: {self.weather['rain']} mm")
            else:
                logger.warning("Weather Data: Not available")
                if self.weather_error:
                    logger.error(f"Error: {self.weather_error}")

            if self.odds:
                logger.info("Match Odds Data is present:")

            else:
                logger.warning("Match Odds Data: Not available")
                if self.odds_error:
                    logger.error(f"Error: {self.odds_error}")

            if self.avg_goals_stats:
                logger.info(f"Avg Goals Per Match: {self.avg_goals_stats}")
            else:
                logger.error(
                    f"Error: {self.avg_goals_error}, League ID: {self.league_id}"
                )

            if self.h2h:
                logger.info(
                    "Head-to-Head Data with statistics and player performances present:"
                )
            else:
                logger.warning(
                    "No head-to-head data available with statistics and performances"
                )

            if self.head_to_head_statistics_with_home_at_home_and_away_at_away:
                logger.info("Head-to-Head Statistics with Home and Away Data present:")
            else:
                logger.warning(
                    "No data for head-to-head statistics with home and away data"
                )

            if self.home_run:
                logger.info("\n Last 3 Home Fixtures present")
            else:
                logger.warning("Failed to get data for home_run")

            if self.away_run:
                logger.info("\n Last 3 Away Fixtures present")
            else:
                logger.warning("Failed to get data for away_run")
            if self.predictions:
                logger.info("\n predictions are present")
            else:
                logger.info("\n no predictions data")
            # logger.info(f"Home Team Ratings: {self.home_team_name}")
            # logger.info(json.dumps(self.home_team_player_ratings_season, indent=4))
            # logger.info(f"Away Team Ratings: {self.away_team_name}")
            # logger.info(json.dumps(self.away_team_player_ratings_season, indent=4))

            # logger.info(f"Last Five Fixtures - HOME:")
            # logger.info(json.dumps(self.last_five_home_fixtures, indent=4))
            # logger.info(f"Last Five Fixtures - AWAY:")
            # logger.info(json.dumps(self.last_five_away_fixtures, indent=4))

            # logger.info(f"Last Five Statistics - HOME TEAM:")
            # logger.info(json.dumps(self.home_stats_dict, indent=4))
            # logger.info(f"Last Five Statistics - AWAY TEAM:")
            # logger.info(json.dumps(self.away_stats_dict, indent=4))

            logger.info(
                f"Saving mutual data in a file named {self.home_team_name} vs {self.away_team_name} data"
            )

        except Exception as e:
            logger.error(f"An error occurred while printing match details: {e}")


# API key and base URL
api_key = "996c177462abec830c211f413c3bdaa8"
base_url = "https://v3.football.api-sports.io"
