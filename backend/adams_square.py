import requests
from datetime import datetime, timedelta
from dateutil import parser
import pprint
import numpy as np
import time
import json
import logging


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
        self.avg_goals = None  # Average goals per match
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

        try:
            target_time = parser.parse(target_time_utc)
        except ValueError as e:
            print(f"Error parsing date: {e}")
            return None

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise error if the response code isn't 200
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve forecast for {city}: {e}")
            return None

        data = response.json()

        if "list" not in data:
            print(f"Unexpected response format for {city}.")
            return None

        closest_forecast = None
        smallest_diff = timedelta.max

        for forecast in data["list"]:
            forecast_time = parser.parse(forecast["dt_txt"])
            time_diff = abs(forecast_time - target_time)

            if time_diff < smallest_diff:
                smallest_diff = time_diff
                closest_forecast = forecast

        return closest_forecast

    def fetch_match_odds(self, match_id):
        """
        Fetch match odds using the football API for the given match ID
        """
        url = Jerusalem.ODDS_API_URL
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": Jerusalem.FOOTBALL_API_KEY,
        }
        params = {"fixture": match_id}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise error if the response code isn't 200
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve match odds for match {match_id}: {e}")
            self.odds_error = "Odds data not available"
            return None

        data = response.json()

        if data.get("response"):
            odds_comparison = {}
            target_bookmakers = ["Bet365"]
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
            ]

            for bookmaker in data["response"][0]["bookmakers"]:
                if bookmaker["name"] in target_bookmakers:
                    odds_comparison[bookmaker["name"]] = {}

                    for bet in bookmaker["bets"]:
                        if bet["name"] in target_bet_names:
                            odds_comparison[bookmaker["name"]][bet["name"]] = bet[
                                "values"
                            ]

            return odds_comparison
        else:
            self.odds_error = "No odds data found"
            return None

    def fetch_average_goals_per_match(self, league_id, last=99):
        """
        Fetches the last `last` matches for the specified league and calculates the average goals per match.
        Stores the results in `self.avg_goals` or error in `self.avg_goals_error`.
        """
        statistics_url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": "996c177462abec830c211f413c3bdaa8",
        }
        params = {"league": league_id, "last": last}

        try:
            response = requests.get(statistics_url, headers=headers, params=params)
            response.raise_for_status()
            match_data = response.json().get("response", [])

            if not match_data:
                self.avg_goals = None
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
                self.avg_goals = round(np.mean(goals_per_match), 3)
                self.avg_goals_error = None
            else:
                self.avg_goals = None
                self.avg_goals_error = "No valid scores found in match data."

        except requests.exceptions.RequestException as e:
            self.avg_goals = None
            self.avg_goals_error = f"Failed to fetch data: {e}"

    def get_players_data_by_position(self, team_id):
        url = f"{self.BASE_URL}/players"

        headers = self.HEADERS

        params = {"team": team_id, "season": 2021}

        # Make the API request
        response = requests.get(url, headers=headers, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            players = data.get("response", [])
            position_classification = {}

            if not players:
                print("No player data found.")
            else:
                for player_data in players:
                    player_info = player_data.get("player", {})
                    statistics = player_data.get("statistics", [])

                    # Extract basic player information
                    player_id = player_info.get("id", "N/A")
                    name = player_info.get("name", "N/A")
                    age = player_info.get("age", "N/A")
                    height = player_info.get("height", "N/A")
                    weight = player_info.get("weight", "N/A")

                    # Extract statistics only for league_id 179
                    for stat in statistics:
                        league = stat.get("league", {})
                        if int(league.get("id")) == int(self.league_id):
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
            return position_classification

        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None

    def fetch_fixture_players_data(self, fixture_id, team_id):

        base_url = f"{self.BASE_URL}/fixtures/players"
        headers = self.HEADERS
        params = {"fixture": fixture_id}

        try:
            response = requests.get(base_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                info = data.get("response", [])
                position_classification = {}

                if not info:
                    print("No player data found.")
                else:
                    for team in info:
                        team_info = team.get("team", {})
                        if team_info["id"] == team_id:
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
                                    position_classification[position].append(
                                        player_entry
                                    )

                return position_classification
            else:
                print(f"Error: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Request failed:")
            return None

    def fetch_head_to_head_statistics(self, team1_id, team2_id):
        """
        Fetch and return head-to-head fixture statistics and details for two teams incuding the rattings for the payers.
        this maes 10 requests
        """
        base_url = f"{self.BASE_URL}/fixtures/headtohead"
        headers = self.HEADERS
        params = {"h2h": f"{team1_id}-{team2_id}"}

        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            sliced_data = dict(list(data.items())[1:])  # Skipping the first item
            fixtures = data.get("response", [])
            sorted_data = sorted(
                fixtures, key=lambda x: parser.parse(x["fixture"]["date"]), reverse=True
            )
            fixtures = sorted_data[:3]
            results = []

            for fixture in fixtures:
                fixture_id = fixture["fixture"]["id"]
                league_id = fixture["league"]["id"]
                league_name = fixture["league"]["name"]
                home_team = fixture["teams"]["home"]
                away_team = fixture["teams"]["away"]
                goals = fixture["goals"]
                date = fixture["fixture"]["date"]

                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
                stats_response = requests.get(stats_url, headers=headers)

                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    sliced_stats = dict(
                        list(stats_data.items())[1:]
                    )  # Skipping metadata
                    statistics = [
                        {
                            "team": {
                                "name": stat["team"]["name"],
                                "id": stat["team"]["id"],
                            },
                            "statistics": stat["statistics"],
                            "player_perfomance": self.fetch_fixture_players_data(
                                fixture_id, stat["team"]["id"]
                            ),
                        }
                        for stat in stats_data.get("response", [])
                    ]
                else:
                    print("issue ies here")
                    statistics = []

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

            return {"fixtures": results}
        else:
            print("there is something wrong somewhere")
            return {"error": f"Error: {response.status_code}, {response.text}"}

    def fetch_head_to_head_statistics_with_home_at_home_and_away_at_away(
        self, home_team_id, away_team_id, league_id
    ):
        """
        Fetch and return head-to-head statistics between two football teams using the API-Sports service.


        Returns:
            list: A list of dictionaries containing fixture details and their statistics.
        """
        base_url = f"{self.BASE_URL}/fixtures/headtohead"
        headers = self.HEADERS
        params = {"h2h": f"{home_team_id}-{away_team_id}"}

        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get("response", [])

            # Sort fixtures by date from most recent to oldest
            sorted_data = sorted(
                fixtures, key=lambda x: parser.parse(x["fixture"]["date"]), reverse=True
            )

            data_list = []
            number_of_games = 0
            for fixture in sorted_data:  # Limit iteration to 5 times
                if number_of_games >= 5:
                    break
                if (
                    fixture["teams"]["home"]["id"] == int(home_team_id)
                    and fixture["teams"]["away"]["id"] == int(away_team_id)
                    and fixture["league"]["id"] == int(league_id)
                ):
                    fixture_id = fixture["fixture"]["id"]

                    stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
                    stats_response = requests.get(stats_url, headers=headers)

                    if stats_response.status_code == 200:
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
                    else:
                        print(
                            f"Error fetching statistics: {stats_response.status_code}, {stats_response.text}"
                        )
            return data_list
        else:
            print(f"Error: {response.status_code}, {response.text}")
            None

    def home_run_and_away_run(self, team_id, is_home=True):
        """
        Fetch past fixtures (home or away) for a specific team and return relevant data.



        Returns:
            list: A list of dictionaries containing fixture and statistics information.
        """
        base_url = f"{self.BASE_URL}/fixtures"
        headers = self.HEADERS
        params = {"team": team_id, "season": 2023}

        response = requests.get(base_url, headers=headers, params=params)
        fixture_count = 2
        league_id = self.league_id
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get("response", [])

            # Filter fixtures based on the is_home parameter
            filtered_fixtures = [
                fixture
                for fixture in fixtures
                if (
                    (is_home and fixture["teams"]["home"]["id"] == int(team_id))
                    or (not is_home and fixture["teams"]["away"]["id"] == int(team_id))
                )
                and fixture["league"]["id"] == int(league_id)
            ]

            # Sort fixtures by date (assuming "fixture.date" is in ISO format) and select the last ones
            filtered_fixtures = sorted(
                filtered_fixtures, key=lambda x: x["fixture"]["date"], reverse=True
            )[:fixture_count]

            results = []
            for fixture in filtered_fixtures:
                fixture_id = fixture["fixture"]["id"]
                fixture_data = {
                    "fixture": fixture,
                }

                # Fetch statistics for the fixture
                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
                stats_response = requests.get(stats_url, headers=headers)

                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    fixture_data["Statistics"] = [
                        {
                            "Team": stat.get("team", {}).get("name", "N/A"),
                            "Statistics": stat.get("statistics", []),
                        }
                        for stat in stats_data.get("response", [])
                    ]
                else:
                    fixture_data["Statistics Error"] = (
                        f"Error: {stats_response.status_code}, {stats_response.text}"
                    )

                results.append(fixture_data)

            return results
        else:
            return {"Error": f"Error: {response.status_code}, {response.text}"}

    def get_last_five_fixtures(self, team_id):
        """Fetches the last five fixtures for a given team ID."""
        url = f"{self.BASE_URL}/fixtures"
        params = {"team": team_id, "season": 2021}
        response = requests.get(url, headers=self.HEADERS, params=params)
        self.fixture_response = response.json()
        return response.json()

    def get_fixture_statistics(self, fixture_id):
        """Fetches statistics for a specific fixture ID."""
        url = f"{self.BASE_URL}/fixtures/statistics"
        params = {"fixture": fixture_id}
        response = requests.get(url, headers=self.HEADERS, params=params)
        self.statistics_response = response.json()
        return response.json()

    def fetch_data_for_team(self, team_id, is_home=True):
        """Fetches last five fixtures and their statistics for a team."""
        number_of_games = 3
        fixtures = self.get_last_five_fixtures(team_id)
        stats_dict = {}
        # print("ets chec if fitters is empty", fixtures)# debugging statement
        game_count = 0

        if fixtures.get("response"):
            if is_home:
                self.last_five_home_fixtures = fixtures
            else:
                self.last_five_away_fixtures = fixtures
            # while number_of_games >=0:

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
            pprint(f"No fixtures found for team ID {team_id}.")
            if is_home:
                self.last_five_home_fixtures = None
            else:
                self.last_five_away_fixtures = None

        return stats_dict

    def statistics_extraction(self):
        fixtures = self.last_five_home_fixtures
        # print(
        #     "this is the dadadadadadadadadadadadadadadadadadadadadadadata type",
        #     fixtures,
        # )# debugging statement

        if fixtures.get("response"):
            for fixture in fixtures["response"]:
                fixture_id = fixture["fixture"]["id"]
                if fixture_id in self.home_stats_dict:
                    statistics = self.home_stats_dict[fixture_id]

                    self.fixtures_data[fixture_id] = (
                        statistics  # Store each fixture's stats
                    )

                    # print(f"Fixture ID: {fixture_id}")# debugging statement

        else:
            print("No fixtures found for the team.")

        return self.fixtures_data

    def extract_teams_info_from_fixtures(self, fixtures_data):
        extracted_info = {}
        # print("this is fixdata", fixtures_data)# debugging statement
        if fixtures_data:
            for fixture_id, fixture_data in fixtures_data.items():
                statistics = fixture_data.get(
                    "statistics", {}
                )  # different from bu print but wors,tiyo
                response = statistics.get("response", [])

                fixture_info = {"Fixture ID": fixture_id, "Teams": {}}
                # print(
                #     "\n \n £££££££££££££££££££££££££££££££££££££££this is response",
                #     response,
                #     "and its ength is ",
                #     len(response),
                # )# debugging statement
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
                    print(
                        "\n \n omera@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ not greater than 2"
                    )

                extracted_info[fixture_id] = fixture_info
                # print(
                #     "------------\\\\\\\\\\\\\\\\----------------the state of extracted info",
                #     extracted_info,
                # )# debugging statement

            return extracted_info
        else:
            print("the function extract_teams_info_from_fixtures is haing some prob")
            return None

    def get_first_away_and_home_fixtures(self, fixtures, team_name):
        first_away = None
        first_home = None
        # print("yawa this are the fixtures", fixtures)# debugging statement
        # print("this var reached and here they the team name-->\n", team_name)# debugging statement
        for fixture_id, fixture in fixtures.items():
            away_team = fixture["Teams"]["Away Team"]
            home_team = fixture["Teams"]["Home Team"]
            # print(
            #     "upto here things are great we have away_team--> \n",
            #     away_team,
            #     "\n and home_team -->",
            #     home_team,
            # )# debugging statement

            if away_team["Team Name"] == team_name and first_away is None:
                first_away = {
                    "Fixture ID": fixture_id,
                    "Opponent Team ID": home_team["Team ID"],
                    "Opponent Team Name": home_team["Team Name"],
                }

            if home_team["Team Name"] == team_name and first_home is None:
                first_home = {
                    "Fixture ID": fixture_id,
                    "Opponent Team ID": away_team["Team ID"],
                    "Opponent Team Name": away_team["Team Name"],
                }

            if first_away and first_home:
                break

        return first_away, first_home

    def teams_info(self):
        fix_d = self.statistics_extraction()
        # print("\n \n \n \nis this team info empty?", fix_d)
        teams_info = self.extract_teams_info_from_fixtures(fix_d)
        return teams_info

    def team_name(self):
        return self.home_team_name

    def first_away(self):
        tim = self.get_first_away_and_home_fixtures(self.teams_info(), self.team_name())
        # print("this what var tim has", tim)# debugging statement
        first_away = tim[0]
        return first_away

    def first_home(self):
        tim = self.get_first_away_and_home_fixtures(self.teams_info(), self.team_name())
        first_home = tim[1]
        return first_home

    # print(f"First Away Fixture for {self.team_name()}:", first_away)
    # print(f"First Home Fixture for {team_name}:", first_away)

    def save_statistics(self, first_away, first_home, constant_team_id):

        # Fetch statistics for First Away Fixture
        # away_fixture_stats = get_fixture_statistics(first_away["Fixture ID"])
        print(
            "the first away reached this function and here it is--->",
            first_away,
            "\n then this is the first home---->",
            first_home,
            "\n constant id is ",
            constant_team_id,
            type(constant_team_id),
        )  # debugging statement
        constant_team_id = int(constant_team_id)
        # first away mean the target team was away whereas first home means the target team was home
        if self.fixtures_data[first_away["Fixture ID"]]:
            teams = self.fixtures_data[first_away["Fixture ID"]]["statistics"][
                "response"
            ]
            # print(
            #     "for now this is the teams,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            #     json.dumps(teams, indent=4),
            # )# debugging statement
            for team in teams:
                team_id = team["team"]["id"]
                team_name = team["team"]["name"]
                print(
                    "||||||||||||||||||||||||||||||||||||||,this is team_name for now",
                    team_name,
                )
                stats = team["statistics"]

                if (
                    team_id == constant_team_id
                ):  # Stats for the constant team (e.g., Napoli)
                    # print(
                    #     "::::::::::::::::::::::::::::::::::::::::::::: data for const"
                    # )# debugging statement
                    self.mutual["away"]["guest_vs_home"]["home_data"] = stats
                    self.mutual["away"]["guest_vs_home"]["home_ratings"] = (
                        self.fetch_fixture_players_data(
                            self.fixtures_data[first_away["Fixture ID"]], team_id
                        )
                    )

                    self.mutual["away"]["guest_vs_home"]["match"][
                        "home_name"
                    ] = f"home team name+++++---- {team_name}"
                elif (
                    team_id == first_away["Opponent Team ID"]
                ):  # Stats for the opponent

                    self.mutual["away"]["guest_vs_home"]["guest_data"] = stats
                    self.mutual["away"]["guest_vs_home"]["guest_ratings"] = (
                        self.fetch_fixture_players_data(
                            self.fixtures_data[first_away["Fixture ID"]], team_id
                        )
                    )
                    self.mutual["away"]["guest_vs_home"]["match"][
                        "guest_name"
                    ] = f"guest team name+++++++---- {team_name}"

        else:
            print(
                f"-/-/-/--/--//--/-/-//-/-/-/---/-/-/- fixture data here \n NO FIXURES DATA"
            )

        # Fetch statistics for First Home Fixture
        # home_fixture_stats = get_fixture_statistics(first_home["Fixture ID"])
        if self.fixtures_data[first_home["Fixture ID"]]:
            teams = self.fixtures_data[first_home["Fixture ID"]]["statistics"][
                "response"
            ]

            for team in teams:
                team_id = team["team"]["id"]
                team_name = team["team"]["name"]
                stats = team["statistics"]
                print(
                    "||||||||||||||||||||||||||||||||||||||,this is team_name for now number 2",
                    team_name,
                )
                if (
                    team_id == constant_team_id
                ):  # Stats for the constant team (e.g., Napoli)
                    self.mutual["home"]["home_vs_guest"]["home_data"] = stats
                    self.mutual["home"]["home_vs_guest"]["home_ratings"] = (
                        self.fetch_fixture_players_data(
                            self.fixtures_data[first_home["Fixture ID"]], team_id
                        )
                    )
                    self.mutual["home"]["home_vs_guest"]["match"][
                        "home_name"
                    ] = f"home team name+++++---- {team_name}"

                elif (
                    team_id == first_home["Opponent Team ID"]
                ):  # Stats for the opponent
                    self.mutual["home"]["home_vs_guest"]["guest_data"] = stats
                    self.mutual["home"]["home_vs_guest"]["guest_ratings"] = (
                        self.fetch_fixture_players_data(
                            self.fixtures_data[first_home["Fixture ID"]], team_id
                        )
                    )
                    self.mutual["home"]["home_vs_guest"]["match"][
                        "guest_name"
                    ] = f"guest team name+++++++---- {team_name}"

        return self.mutual

    def h_team_id(self):
        return self.home_team_id

    # def unown_mutual(self):
    #     mutual = self.save_statistics(self.first_away, self.first_home, self.h_team_id)
    #     return mutual

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

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
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("response", [])

                if not fixtures:
                    logger.info("No fixtures found for the given combination.")
                    return None

                # Filter for past fixtures only
                now = datetime.now(datetime.now().astimezone().tzinfo)
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
                logger.error(f"Error fetching H2H data: {response.status_code}")
                return None
        except Exception as e:
            logger.exception(f"An error occurred: {e}")
            return None

    def populate_mutual(
        self,
        first_away_id,
        first_home_id,
        constant_team_id=None,
        constant_team_name=None,
    ):
        # Fetch H2H for first_away_id
        constant_team_id = self.away_team_id
        constant_team_name = self.away_team_name

        h2h_away_combination = f"{first_away_id}-{constant_team_id}"
        latest_fixture_away = self.fetch_h2h_data(h2h_away_combination)
        if latest_fixture_away:
            fixture_id_away = latest_fixture_away["fixture"]["id"]
            stats_away = self.get_fixture_statistics(fixture_id_away)
            for stat in stats_away["response"]:
                team_id = stat["team"]["id"]
                team_name = stat["team"]["name"]
                stats = stat["statistics"]
                print(
                    "||||||||||||||||||||||||||||||||||||||,this is team_name for now number 3",
                    team_name,
                )
                if team_id == int(
                    constant_team_id
                ):  # Stats for the constant team (e.g., Napoli)

                    self.mutual["away"]["guest_vs_away"]["away_data"] = stats
                    self.mutual["away"]["guest_vs_away"]["away_ratings"] = (
                        self.fetch_fixture_players_data(fixture_id_away, team_id)
                    )

                    self.mutual["away"]["guest_vs_away"]["match"][
                        "away_name"
                    ] = f"away team name+++++---- {team_name}"
                elif team_id == first_away_id:  # Stats for the opponent
                    self.mutual["away"]["guest_vs_away"]["guest_data"] = stats
                    self.mutual["away"]["guest_vs_away"]["guest_ratings"] = (
                        self.fetch_fixture_players_data(fixture_id_away, team_id)
                    )
                    self.mutual["away"]["guest_vs_away"]["match"][
                        "guest_name"
                    ] = f"guest team name+++++++---- {team_name}"

        # Fetch H2H for first_home_id
        h2h_home_combination = f"{constant_team_id}-{first_home_id}"
        latest_fixture_home = self.fetch_h2h_data(h2h_home_combination)
        if latest_fixture_home:
            # print(
            #     "yes we have the data ////////////////////////////////////////////////////////////////////////"
            # )# debugging statement
            fixture_id_home = latest_fixture_home["fixture"]["id"]
            stats_home = self.get_fixture_statistics(fixture_id_home)
            for stat in stats_home["response"]:
                team_id = stat["team"]["id"]
                team_name = stat["team"]["name"]
                stats = stat["statistics"]
                print(
                    "||||||||||||||||||||||||||||||||||||||,this is team_name for now number 4",
                    team_name,
                )
                if team_id == int(
                    constant_team_id
                ):  # Stats for the constant team (e.g., Napoli)
                    self.mutual["home"]["away_vs_guest"]["away_data"] = stats
                    self.mutual["home"]["away_vs_guest"]["away_ratings"] = (
                        self.fetch_fixture_players_data(latest_fixture_home, team_id)
                    )
                    self.mutual["home"]["away_vs_guest"]["match"][
                        "away_name"
                    ] = f"away team name+++++---- {team_name}"
                elif team_id == first_home_id:  # Stats for the opponent
                    self.mutual["home"]["away_vs_guest"]["guest_data"] = stats
                    self.mutual["home"]["away_vs_guest"]["guest_ratings"] = (
                        self.fetch_fixture_players_data(latest_fixture_home, team_id)
                    )
                    self.mutual["home"]["away_vs_guest"]["match"][
                        "guest_name"
                    ] = f"guest team name+++++++---- {team_name}"
        else:
            print(
                "NO NO NO we  DONT have the data ////////////////////////////////////////////////////////////////////////"
            )
        return self.mutual

    def first_away_id(self):
        first_away_id = self.first_away()
        first_away_id = first_away_id["Opponent Team ID"]  # Replace with actual ID
        return first_away_id

    def first_home_id(self):
        first_home_id = self.first_home()
        first_home_id = first_home_id["Opponent Team ID"]  # Replace with actual ID
        return first_home_id

    # Populate mutual dictionary
    # def unown_mutual_data(self):
    #     mutual_data = self.populate_mutual(self.first_away_id, self.first_home_id)
    #     return mutual_data

    def receive_match(self, match_data):
        """
        This method receives match data and stores it in instance variables
        """
        self.match_id = match_data.get("id")
        self.date = match_data.get("date")
        self.venue = match_data.get("venue")
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
        # odds = self.fetch_match_odds(self.match_id)
        odds = None
        if odds:
            self.odds = odds
        else:
            self.odds = None

        # avg_goals = self.fetch_average_goals_per_match(
        #     league_id=self.league_id, last=99
        # )
        avg_goals = None
        if avg_goals:
            self.average_goals_per_match = avg_goals
        else:
            avg_goals = None

        # h2h_data = self.fetch_head_to_head_statistics(
        #     self.home_team_id, self.away_team_id
        # )
        h2h_data = None
        if h2h_data:
            self.h2h = h2h_data

        # head_to_head_statistics_with_home_at_home_and_away_at_away = (
        #     self.fetch_head_to_head_statistics_with_home_at_home_and_away_at_away(
        #         self.home_team_id, self.away_team_id, self.league_id
        #     )
        # )
        head_to_head_statistics_with_home_at_home_and_away_at_away = None
        if head_to_head_statistics_with_home_at_home_and_away_at_away:
            self.head_to_head_statistics_with_home_at_home_and_away_at_away = (
                head_to_head_statistics_with_home_at_home_and_away_at_away
            )

        # home_run = self.home_run_and_away_run(self.home_team_id, True)
        # if home_run:
        #     self.home_run = home_run
        # away_run = self.home_run_and_away_run(self.away_team_id, False)
        # if away_run:
        #     self.away_run = away_run

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

        # print("Fetching data for the home team...")
        home_stats_dict = self.fetch_data_for_team(self.home_team_id, is_home=True)
        # home_stats_dict = None
        if home_stats_dict:
            self.home_stats_dict = home_stats_dict
            # print(
            #     "this is the nature of the home start dict 444444444444444444444444444444 ",
            #     self.home_stats_dict,
            # )# debugging statement
        else:
            self.home_stats_dict = None
        print("Waiting for one minute before fetching data for the away team...")
        time.sleep(
            60
        )  # **************************************************************************************************************************
        print("Fetching data for the away team...")
        away_stats_dict = self.fetch_data_for_team(self.away_team_id, is_home=False)
        # away_stats_dict = None
        if away_stats_dict:
            self.away_stats_dict = away_stats_dict

        else:
            self.away_stats_dict = None

        self.save_statistics(self.first_away(), self.first_home(), self.h_team_id())
        time.sleep(60)
        self.populate_mutual(self.first_away_id(), self.first_home_id())

        self.print_match_details()

    def print_match_details(self):
        """
        This method prints the stored match details
        """
        print(f"league_id--{self.league_id}")
        print(f"Match ID: {self.match_id}")
        print(f"match:{self.home_team_name} vs {self.away_team_name}")
        print(f"Date: {self.date}")
        print(f"Venue: {self.venue}")
        print(f"City: {self.city}")

        if self.weather:
            print("Weather Data:")
            print(f"  - Temperature: {self.weather['temperature']}°C")
            print(f"  - Feels Like: {self.weather['feels_like']}°C")
            print(f"  - Humidity: {self.weather['humidity']}%")
            print(f"  - Weather: {self.weather['weather_description']}")
            print(f"  - Wind Speed: {self.weather['wind_speed']} m/s")
            print(f"  - Rain Volume: {self.weather['rain']} mm")
        else:
            print("Weather Data: Not available")
            if self.weather_error:
                print(f"Error: {self.weather_error}")

        if self.odds:
            print("Match Odds Data:")
            pprint.pprint(self.odds)
        else:
            print("Match Odds Data: Not available")
            if self.odds_error:
                print(f"Error: {self.odds_error}")
        if self.avg_goals:
            print(f"avg_goals_per_match--{self.avg_goals}")
        else:
            print(f"error--{self.avg_goals_error},{self.league_id}")
        if self.h2h:
            print(
                "this head to head data with statistics and perfomace of payers \n\n",
                self.h2h,
            )
        else:
            print("no  head to head data avaiabe with th statistics and perfomances")

        if self.head_to_head_statistics_with_home_at_home_and_away_at_away:
            print(
                "the data for head_to_head_statistics_with_home_at_home_and_away_at_away is here:\n\n",
                self.head_to_head_statistics_with_home_at_home_and_away_at_away,
            )
        else:
            print(
                "no data for head_to_head_statistics_with_home_at_home_and_away_at_away"
            )

        if self.home_run:
            print("\n--- Last 3 Home Fixtures ---")
            print(json.dumps(self.home_run, indent=4))
        else:
            print("faied to get data for home_run")

        if self.away_run:
            print("\n--- Last 3 away Fixtures ---")
            print(json.dumps(self.away_run, indent=4))
        else:
            print("faied to get data for away_run")

        # print(
        #     "HHHHHHOOOOOMMMMMMEEEEEEEEEE  RRRRRRRRRRAAAAAAATTTTTTTTTTTTTIIIIIIINNNNNNNNNNGGGGGGGGSSSSSSSSSSS",
        #     self.home_team_name,
        # )
        # print(self.home_team_player_ratings_sesason)
        # print(
        #     "AAAAAWWWAYYYYYYYYYYYY  RRRRRRRRRRRRRAAAAAAAATTTTTTTTTTIIIIIIIIIIINNNNNNNNNNNNGGGGGGGSSSSSSSSSSSSSS",
        #     self.away_team_name,
        # )
        # print(self.away_team_player_ratings_sesason)

        # print(f"last five fixture HOME............................")
        # print(json.dumps(self.last_five_home_fixtures, indent=4))
        # print(f"last five fixture AWAY............................")
        # print(json.dumps(self.last_five_away_fixtures, indent=4))
        # print(f"last five statistics HOME TEAM............................")
        # print(json.dumps(self.home_stats_dict, indent=4))
        # print(f"last five statistics AWAY TEAM............................")
        # print(json.dumps(self.away_stats_dict, indent=4)) #shoud buncommented to chec data
        # print("-------------------------------------------------------------------")

        print(
            f"saving mutual in a fie named {self.home_team_name} vs {self.away_team_name} data ------------------------------------------------------"
        )

        def save_mutual_to_file():
            filename = f"{self.home_team_name} vs {self.away_team_name} data"
            try:
                with open(filename, "w") as file:
                    json.dump(self.mutual, file, indent=4)
                print(f"Data successfully written to {filename}")
            except Exception as e:
                print(f"Error writing to file: {e}")

        save_mutual_to_file()


import requests
import json
from datetime import datetime

# API key and base URL
api_key = "996c177462abec830c211f413c3bdaa8"
base_url = "https://v3.football.api-sports.io"

# Headers for API requests
headers = {"x-apisports-key": api_key}


# Function to fetch H2H data
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
