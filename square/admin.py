from django.contrib import admin
from .models import (
    CustomUser,
    Sport,
    Match,
    FootballPrediction,
    TennisPrediction,
    BasketballPrediction,
    VIPTip,
    SubscriptionPlan,
    Purchase,
    MatchView,
    SiteInformation,
    ResultDate,
    Fixture,
    Payslips,
)
from django.contrib.auth.admin import UserAdmin

# Register the CustomUser model


class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_vip", "vip_expiry", "date_joined")
    list_filter = ("is_vip", "date_joined", "is_active")
    search_fields = ("username", "email")
    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("VIP Access", {"fields": ("is_vip", "vip_expiry")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


# Register the Sport model
@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# Register the Match model
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "match_id",
        "date",
        "home_team_id",
        "home_team",
        "away_team_id",
        "away_team",
        "league",
        "sport",
    )
    search_fields = (
        "match_id",
        "home_team_id",
        "home_team",
        "away_team_id",
        "away_team",
        "sport__name",
    )
    list_filter = ("sport", "match_date", "league", "is_premium")


# Register the FootballPrediction model
@admin.register(FootballPrediction)
class FootballPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "match",
        "home_team_win_probability",
        "away_team_win_probability",
        "gg_probability",
    )
    search_fields = ("match__home_team", "match__away_team")


# Register the TennisPrediction model
@admin.register(TennisPrediction)
class TennisPredictionAdmin(admin.ModelAdmin):
    list_display = ("match", "total_games_probability", "total_games_odds")
    search_fields = ("match__home_team", "match__away_team")


# Register the BasketballPrediction model
@admin.register(BasketballPrediction)
class BasketballPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "match",
        "expected_goals_overtime_probability",
        "expected_goals_overtime_odds",
    )
    search_fields = ("match__home_team", "match__away_team")


# Register the VIPTip model
@admin.register(VIPTip)
class VIPTipAdmin(admin.ModelAdmin):
    list_display = ("match", "tip", "created_at")
    search_fields = ("match__home_team", "match__away_team", "tip")


# Register the SubscriptionPlan model
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_days")
    search_fields = ("name",)


# Register the Purchase model
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "subscription_plan", "purchase_date", "expiry_date")
    search_fields = ("user__username", "subscription_plan__name")
    list_filter = ("purchase_date", "expiry_date")


# Register the MatchView model
@admin.register(MatchView)
class MatchViewAdmin(admin.ModelAdmin):
    list_display = ("user", "match", "viewed_at")
    search_fields = ("user__username", "match__home_team", "match__away_team")


@admin.register(SiteInformation)
class siteinfoAdmin(admin.ModelAdmin):
    list_display = ("site_name",)


from django.contrib import admin
from backend.models import Country, Season, League, Match, MatchDate


class CountryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "flag",
    )  # Customize the fields to display in the list view
    search_fields = ("name", "code")  # Allow searching by name and code


class SeasonAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "start_date",
        "end_date",
        "current",
    )  # Customize the fields to display in the list view
    list_filter = ("current",)  # Add a filter for the 'current' field


class LeagueAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "league_id",
        "type",
        "country",
    )  # Customize the fields to display in the list view
    search_fields = ("name", "type")  # Allow searching by name and type
    list_filter = ("country",)  # Add a filter for the 'country' field


# Register models with their respective admin classes
admin.site.register(Country, CountryAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(League, LeagueAdmin)


# Admin class for Match model
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "match_id",
        "home_team_name",
        "away_team_name",
        "date",
        "referee",
        "timezone",
        "league",
        "match_date",
    )
    search_fields = ("home_team_name", "away_team_name", "match_id", "league__name")
    list_filter = ("to_be_predicted", "date", "league", "match_date")
    ordering = ("date",)


# Admin class for MatchDate model
class MatchDateAdmin(admin.ModelAdmin):
    list_display = ("date",)
    search_fields = ("date",)
    ordering = ("date",)


# Register models
admin.site.register(Match, MatchAdmin)
admin.site.register(MatchDate, MatchDateAdmin)

from backend.models import TaskProgress


@admin.register(TaskProgress)
class TaskProgressAdmin(admin.ModelAdmin):
    list_display = (
        "task_id",
        "progress",
        "successful",
        "failed",
        "total",
    )  # Fields to display in the admin list view
    search_fields = ("task_id",)  # Allow searching by task ID
    list_filter = ("last_updated",)  # Optional: Filter by last updated date

    def __str__(self):
        return f"Task {self.task_id} - Processed: {self.successful + self.failed}, Success: {self.successful}, Fail: {self.failed}, Total to be processed: {self.Total}"


class FixtureAdmin(admin.ModelAdmin):
    list_display = (
        "fixture_id",
        "fixture_date",
        "status_short",
        "team_home",
        "team_away",
        "score_fulltime_home",
        "score_fulltime_away",
    )
    search_fields = ("team_home", "team_away", "status_short")
    list_filter = ("fixture_date", "status_short")


admin.site.register(Fixture, FixtureAdmin)


class ResultDateAdmin(admin.ModelAdmin):
    list_display = ("date",)
    search_fields = ("date",)
    list_filter = ("date",)


admin.site.register(ResultDate, ResultDateAdmin)


@admin.register(Payslips)
class PayslipsAdmin(admin.ModelAdmin):
    list_display = ("email", "reference", "amount", "status", "verified", "date_paid")
    search_fields = ("email", "reference")
    list_filter = ("status", "verified", "date_paid")
