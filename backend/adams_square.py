class Jerusalem:
    # Static variables for the API keys
    WEATHER_API_KEY = "1795372653d0553aa30f7e6be0c9d7d5"
    FOOTBALL_API_KEY = "8f15eaf630b27aa1971df895e7ca6997"

    def __init__(self):
        # Instance variables to store match data
        self.match_id = None
        self.date = None
        self.venue = None
        self.home_team_name = None
        self.away_team_name = None
        self.league_id = None
        self.home_team_logo = None
        self.away_team_logo = None

    def receive_match(self, match_data):
        """
        This method receives match data and stores it in instance variables
        """
        # Assign match details to instance variables
        self.match_id = match_data.get("id")
        self.date = match_data.get("date")
        self.venue = match_data.get("venue")
        self.home_team_name = match_data.get("home_team_name")
        self.away_team_name = match_data.get("away_team_name")
        self.league_id = match_data.get("league")
        self.home_team_logo = match_data.get("home_team_logo")
        self.away_team_logo = match_data.get("away_team_logo")

        # Optionally, print to debug or confirm storage
        self.print_match_details()

    def print_match_details(self):
        """
        This method prints the stored match details
        """
        print(f"Match ID: {self.match_id}")
        print(f"Date: {self.date}")
        print(f"Venue: {self.venue}")
        print(f"Home Team: {self.home_team_name}")
        print(f"Away Team: {self.away_team_name}")
        print(f"League ID: {self.league_id}")
        print(f"Home Team Logo: {self.home_team_logo}")
        print(f"Away Team Logo: {self.away_team_logo}")
        print("-----------")
