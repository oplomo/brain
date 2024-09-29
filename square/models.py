
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone


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
class Match(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    match_date = models.DateTimeField()

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} - {self.sport.name}"

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
    match = models.ForeignKey("Match", on_delete=models.CASCADE)

    class ResultChoices(models.TextChoices):
        WAITING = "waiting", "Waiting"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    # Common to all sports
    home_team_win_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
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

    def __str__(self):
        return f"Football Prediction for {self.match}"


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

    # Add other specific basketball fields as needed

    def __str__(self):
        return f"Basketball Prediction for {self.match}"


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
