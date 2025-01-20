from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, null=True, blank=True)
    flag = models.URLField(max_length=300, null=True, blank=True)

    def __str__(self):
        return self.name


class Season(models.Model):
    year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    current = models.BooleanField(default=False)

    def __str__(self):
        return f"Season {self.year}"


class League(models.Model):
    league_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    logo = models.URLField(max_length=300, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    seasons = models.ManyToManyField(Season, related_name="leagues")

    def __str__(self):
        return self.name


class MatchDate(models.Model):
    """
    Stores unique match dates to track activities on specific dates.
    """

    date = models.DateField(unique=True)

    def __str__(self):
        return self.date.strftime("%Y-%m-%d")


class Match(models.Model):
    """
    Stores match details, including league, venue, and team information.
    """

    match_id = models.IntegerField(unique=True)
    date = models.DateTimeField()
    referee = models.CharField(max_length=100, null=True, blank=True)
    timezone = models.CharField(max_length=50)

    # MatchDate relationship
    match_date = models.ForeignKey(
        MatchDate, related_name="matches", on_delete=models.CASCADE
    )

    # Venue details
    venue_name = models.CharField(max_length=100, null=True, blank=True)
    venue_city = models.CharField(max_length=100, null=True, blank=True)

    # Team details
    home_team_name = models.CharField(max_length=100)
    home_team_logo = models.URLField(max_length=300, null=True, blank=True)
    home_team_id = models.IntegerField(null=True, blank=True)
    away_team_name = models.CharField(max_length=100)
    away_team_logo = models.URLField(max_length=300, null=True, blank=True)
    away_team_id = models.IntegerField(null=True, blank=True)

    # League relationship
    league = models.ForeignKey(
        "League", related_name="matches", on_delete=models.CASCADE
    )
    to_be_predicted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.home_team_name} vs {self.away_team_name} on {self.date}"



class TaskProgress(models.Model):
    task_id = models.CharField(max_length=255)
    progress = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task {self.task_id} - {self.progress}%"
