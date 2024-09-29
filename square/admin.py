from django.contrib import admin
from .models import CustomUser, Sport, Match, FootballPrediction, TennisPrediction, BasketballPrediction, VIPTip, SubscriptionPlan, Purchase, MatchView
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
    list_display = ('name',)
    search_fields = ('name',)

# Register the Match model
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'away_team', 'sport', 'match_date')
    search_fields = ('home_team', 'away_team', 'sport__name')
    list_filter = ('sport', 'match_date')

# Register the FootballPrediction model
@admin.register(FootballPrediction)
class FootballPredictionAdmin(admin.ModelAdmin):
    list_display = ('match', 'home_team_win_probability', 'away_team_win_probability', 'gg_probability')
    search_fields = ('match__home_team', 'match__away_team')

# Register the TennisPrediction model
@admin.register(TennisPrediction)
class TennisPredictionAdmin(admin.ModelAdmin):
    list_display = ('match', 'total_games_probability', 'total_games_odds')
    search_fields = ('match__home_team', 'match__away_team')

# Register the BasketballPrediction model
@admin.register(BasketballPrediction)
class BasketballPredictionAdmin(admin.ModelAdmin):
    list_display = ('match', 'expected_goals_overtime_probability', 'expected_goals_overtime_odds')
    search_fields = ('match__home_team', 'match__away_team')

# Register the VIPTip model
@admin.register(VIPTip)
class VIPTipAdmin(admin.ModelAdmin):
    list_display = ('match', 'tip', 'created_at')
    search_fields = ('match__home_team', 'match__away_team', 'tip')

# Register the SubscriptionPlan model
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days')
    search_fields = ('name',)

# Register the Purchase model
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'purchase_date', 'expiry_date')
    search_fields = ('user__username', 'subscription_plan__name')
    list_filter = ('purchase_date', 'expiry_date')

# Register the MatchView model
@admin.register(MatchView)
class MatchViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'match', 'viewed_at')
    search_fields = ('user__username', 'match__home_team', 'match__away_team')








