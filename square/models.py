from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from datetime import date


# Custom User model to extend with profile and VIP access status
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_vip = models.BooleanField(default=False)  # To track VIP access
    vip_expiry = models.DateTimeField(null=True, blank=True)  # When VIP access expires

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
        related_query_name="customuser",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
        related_query_name="customuser",
    )

    def has_vip_access(self):
        """Check if the user currently has VIP access."""
        return self.vip_expiry and self.vip_expiry > timezone.now()

    def __str__(self):
        return self.username


# Model for different sports (soccer, basketball, tennis)
class Sport(models.Model):
    name = models.CharField(max_length=50)  # Example: Soccer, Basketball, Tennis

    def __str__(self):
        return self.name


# Model for matches (soccer, basketball, tennis)
from backend.models import MatchDate, League


class Match(models.Model):

    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    match_id = models.IntegerField(unique=True, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    referee = models.CharField(max_length=100, null=True, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    match_date = models.ForeignKey(
        MatchDate, related_name="mechis", on_delete=models.CASCADE
    )

    # Venue details
    venue_name = models.CharField(max_length=100, null=True, blank=True)
    venue_city = models.CharField(max_length=100, null=True, blank=True)

    home_team = models.CharField(max_length=100)
    home_team_logo = models.URLField(max_length=300, null=True, blank=True)
    home_team_id = models.IntegerField(null=True, blank=True)
    away_team = models.CharField(max_length=100)
    away_team_logo = models.URLField(max_length=300, null=True, blank=True)
    away_team_id = models.IntegerField(null=True, blank=True)
    updated = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    gold_bar = models.CharField(max_length=50, default="N/A")
    league = models.ForeignKey(
        League,
        related_name="League_matches",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    # Weather details
    temperature = models.FloatField(null=True, blank=True)
    feels_like = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    weather_description = models.CharField(max_length=255, null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    rain = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

    def get_prediction_model(self):
        """Return the appropriate prediction model based on sport."""
        if self.sport.name.lower() == "football":
            return FootballPrediction
        elif self.sport.name.lower() == "basketball":
            return BasketballPrediction
        elif self.sport.name.lower() == "tennis":
            return TennisPrediction
        return None


class MatchPredictionBase(models.Model):
    match = models.ForeignKey(Match, to_field="match_id", on_delete=models.CASCADE)

    class ResultChoices(models.TextChoices):
        WAITING = "waiting", "Waiting"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    # Common to all sports
    home_team_win_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    home_team_expected_goals = models.IntegerField(null=True, blank=True)
    home_team_win_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    draw_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    draw_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    away_team_win_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    away_team_expected_goals = models.IntegerField(null=True, blank=True)

    away_team_win_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    three_way_match_result = models.CharField(
        max_length=50, choices=ResultChoices.choices, default=ResultChoices.WAITING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True  # Mark this model as abstract

    def __str__(self):
        return f"Prediction for {self.match}"


class FootballPrediction(MatchPredictionBase):
    # Keep draw and goal-related fields specific to football
    gg_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    gg_odds = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    no_gg_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    no_gg_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    gg_match_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    # Over/Under 1.5 Goals
    over_1_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    over_1_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_1_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_1_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    o_1_5_match_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )
    # Over/Under 2.5 Goals
    over_2_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    over_2_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_2_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_2_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    o_2_5_match_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    # Over/Under 3.5 Goals
    over_3_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    over_3_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_3_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_3_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    o_3_5_match_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    # Over/Under 4.5 Goals
    over_4_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    over_4_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_4_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_4_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    o_4_5_match_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    # Over/Under 5.5 Goals
    over_5_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    over_5_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_5_5_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    under_5_5_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    o_5_5_match_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    # Total Corners
    total_corners = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    total_corners_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    total_corners_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    total_corner_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )
    # Total Cards
    total_cards = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    total_cards_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    total_cards_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    total_card_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    dc12_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    dc12_normalized_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    dc12_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    dc1x_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    dc1x_normalized_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    dc1x_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    dcx2_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    dcx2_normalized_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    dcx2_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    dc_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )
    home_team_goals = models.IntegerField(blank=True, null=True)
    away_team_goals = models.IntegerField(blank=True, null=True)
    correct_score_odds = models.CharField(max_length=50, blank=True, null=True)
    correct_score_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    def save(self, *args, **kwargs):
        # Make sure the probabilities are set
        if (
            self.home_team_win_probability
            and self.draw_probability
            and self.away_team_win_probability
        ):
            # Convert to floats for calculation
            home_prob = float(self.home_team_win_probability)
            draw_prob = float(self.draw_probability)
            away_prob = float(self.away_team_win_probability)

            # Double Chance Calculations
            self.dc1x_probability = home_prob + draw_prob
            self.dcx2_probability = draw_prob + away_prob
            self.dc12_probability = home_prob + away_prob

            # Normalize to ensure probabilities sum to 100%
            total_dc_prob = (
                self.dc1x_probability + self.dcx2_probability + self.dc12_probability
            )

            # Normalize if total is not zero to avoid division by zero
            if total_dc_prob > 0:
                self.dc1x_normalized_probability = (
                    self.dc1x_probability / total_dc_prob
                ) * 100
                self.dcx2_normalized_probability = (
                    self.dcx2_probability / total_dc_prob
                ) * 100
                self.dc12_normalized_probability = (
                    self.dc12_probability / total_dc_prob
                ) * 100
            else:
                self.dc1x_normalized_probability = 0
                self.dcx2_normalized_probability = 0
                self.dc12_normalized_probability = 0

        # Call the parent's save method to ensure the model is saved
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Football Prediction for {self.match}"

    def get_absolute_url(self):
        home_team_slug = self.match.home_team
        away_team_slug = self.match.away_team
        sport_slug = self.match.sport.name
        time_str = (
            self.match.match_date.date.strftime("%H:%M:%S")
            if self.match.match_date
            else "N/A"
        )

        return reverse(
            "square:soccer_detail",
            args=[self.pk, home_team_slug, away_team_slug, time_str, sport_slug],
        )


class TennisPrediction(MatchPredictionBase):

    total_games = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    total_games_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    total_games_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    tgame_match_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    def __str__(self):
        return f"Tennis Prediction for {self.match}"

    def get_absolute_url(self):
        home_team_slug = self.match.home_team
        away_team_slug = self.match.home_team
        sport_slug = self.match.sport.name
        time_str = self.match.match_date.strftime("%Y-%m-%d-%H:%M")
        return reverse(
            "square:tennis_detail",
            args=[
                self.pk,
                home_team_slug,
                away_team_slug,
                time_str,
                sport_slug,
            ],
        )


class BasketballPrediction(MatchPredictionBase):
    # Basketball-specific parameters
    expected_goals_overtime = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    expected_goals_overtime_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    expected_goals_overtime_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    tovertime_match_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    expected_goals_halftime = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    expected_goals_halftime_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    expected_goals_halftime_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    thalftime_match_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    expected_goals_hometeam = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    expected_goals_hometeam_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    expected_goals_hometeam_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    t_hometeam_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    expected_goals_awayteam = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    expected_goals_awayteam_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    expected_goals_awayteam_odds = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    t_awayteam_result = models.CharField(
        max_length=50,
        choices=MatchPredictionBase.ResultChoices.choices,
        default=MatchPredictionBase.ResultChoices.WAITING,
    )

    # Add other specific basketball fields as needed

    def __str__(self):
        return f"Basketball Prediction for {self.match}"

    def get_absolute_url(self):
        home_team_slug = self.match.home_team
        away_team_slug = self.match.home_team
        sport_slug = self.match.sport.name
        time_str = self.match.match_date.strftime("%Y-%m-%d-%H:%M")
        return reverse(
            "square:basketball_detail",
            args=[self.pk, home_team_slug, away_team_slug, time_str, sport_slug],
        )


# VIP tips for users who purchase access
class VIPTip(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    tip = models.TextField()  # Example: "Home team wins by 2 goals"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"VIP Tip for {self.match}"


# Subscription Plan for VIP users
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)  # Example: '1 month VIP Access'
    price = models.DecimalField(max_digits=6, decimal_places=2)  # Example: 19.99 USD
    duration_days = (
        models.PositiveIntegerField()
    )  # Example: 30 days for 1-month subscription

    def __str__(self):
        return f"{self.name} - {self.price} USD"


# Track users' purchases and VIP access
class Purchase(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()  # VIP access expiry

    def __str__(self):
        return f"Purchase by {self.user.username} for {self.subscription_plan.name}"

    def save(self, *args, **kwargs):
        """Set the VIP expiry date based on the subscription plan duration."""
        if not self.expiry_date:
            self.expiry_date = self.purchase_date + timezone.timedelta(
                days=self.subscription_plan.duration_days
            )
        super().save(*args, **kwargs)
        # Update the user's VIP status and expiry
        self.user.is_vip = True
        self.user.vip_expiry = self.expiry_date
        self.user.save()


# Model to track user views of matches (optional, if needed for analytics)
class MatchView(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} viewed {self.match}"


class SiteInformation(models.Model):
    # Basic site info
    site_name = models.CharField(max_length=255, help_text="The name of the website.")
    site_description = models.TextField(
        blank=True, help_text="A brief description of the website."
    )
    logo = models.ImageField(
        upload_to="media/logos/",
        blank=True,
        null=True,
        help_text="The logo of the site.",
    )

    # Policies and legal
    privacy_policy = models.TextField(
        blank=True, help_text="Privacy policy of the website."
    )
    terms_and_conditions = models.TextField(
        blank=True, help_text="Terms and conditions of the website."
    )

    # Social media links
    facebook_link = models.URLField(blank=True, help_text="Link to Facebook page.")
    twitter_link = models.URLField(blank=True, help_text="Link to Twitter profile.")
    instagram_link = models.URLField(blank=True, help_text="Link to Instagram profile.")
    linkedin_link = models.URLField(blank=True, help_text="Link to LinkedIn profile.")
    youtube_link = (models.URLField(blank=True, help_text="Link to YouTube channel."),)
    telegram_link = (
        models.URLField(blank=True, help_text="Link to telegram channel."),
    )
    reddit_link = models.URLField(blank=True, help_text="Link to reddit channel.")
    discord_link = models.URLField(blank=True, help_text="Link to discord channel.")

    # Contact information
    contact_email = models.EmailField(
        max_length=255, blank=True, help_text="Contact email for the site."
    )
    contact_phone = models.CharField(
        max_length=20, blank=True, help_text="Contact phone number for the site."
    )
    address = models.TextField(
        blank=True, help_text="Physical address of the site or organization."
    )

    # Other relevant fields
    support_email = models.EmailField(
        max_length=255, blank=True, help_text="Support email address."
    )
    about_us = models.TextField(
        blank=True, help_text="Information about the website or company."
    )
    newsletter_link = models.URLField(
        blank=True, help_text="Link to newsletter or subscription page."
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name


class ResultDate(models.Model):
    date = models.DateField()  # Store just the date (not datetime)

    def __str__(self):
        return str(self.date)


def get_default_result_date():
    result_date, created = ResultDate.objects.get_or_create(date=date.today())
    return result_date.id


class Fixture(models.Model):
    fixture_id = models.IntegerField(unique=True)
    fixture_date = models.DateTimeField()
    status_short = models.CharField(max_length=10)
    team_home = models.CharField(max_length=255)
    team_away = models.CharField(max_length=255)
    score_fulltime_home = models.IntegerField(null=True, blank=True)
    score_fulltime_away = models.IntegerField(null=True, blank=True)
    result_date = models.ForeignKey(
        ResultDate,
        on_delete=models.CASCADE,
        related_name="fixtures",
        default=get_default_result_date,
    )

    def __str__(self):
        return f"{self.team_home} vs {self.team_away} ({self.status_short})"
