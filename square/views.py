from django.shortcuts import render, get_object_or_404
from .models import (
    FootballPrediction,
    SiteInformation,
    BasketballPrediction,
    TennisPrediction,
    Match,
    Sport,
    Fixture,
    VIPStatus,
)
import math
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify
import time
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)


def index(request, selected=None, item=None, day="today"):
    # Updated sports menu
    site = get_object_or_404(SiteInformation, pk=1)
    search_query = request.GET.get("q", "").strip()
    sports_menu = {
        "soccer": [
            "3 way(1X2)",
            "bts(GG)",
            "total(OVER/UNDER)",
            "cards",
            "corners",
            "double chance(12,1X,X2)",
            "correct_score",
        ],
        "basketball": ["3 way", "total overtime", "total halftime"],
        "tennis": ["3 way", "total"],
    }

    # Set default sport if none is selected
    selected = selected or "soccer"
    menu = sports_menu.get(selected, [])

    print(f"Selected sport: {selected}")
    print(f"Available menu options for {selected}: {menu}")

    # Get today's date and define start and end boundaries
    today = datetime.now().date()

    if day == "yesterday":
        start_date = today - timedelta(days=1)
        end_date = start_date
    elif day == "today":
        start_date = today
        end_date = datetime.combine(start_date, datetime.max.time())
    elif day == "tomorrow":
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=2)
    else:
        # If day is something else, default to today
        start_date = today
        end_date = today + timedelta(days=1)

    print(f"Start date: {start_date}, End date: {end_date}")
    # Determine the correct prediction model based on the selected sport
    if selected == "soccer":
        matches = FootballPrediction.objects.select_related("match").filter(
            match__sport__name="soccer",
            match__is_premium=False,
            match__date__date__range=[start_date, end_date],
        )

    elif selected == "basketball":
        matches = BasketballPrediction.objects.select_related("match").filter(
            match__sport__name=selected,
            match__match_date__date__range=[start_date, end_date],  # ✅ Fix applied
        )
    elif selected == "tennis":
        matches = TennisPrediction.objects.select_related("match").filter(
            match__sport__name=selected,
            match__match_date__date__range=[start_date, end_date],  # ✅ Fix applied
        )
    else:
        matches = Match.objects.none()  # Empty queryset for unknown sports

    if search_query:
        matches = matches.filter(
            Q(match__home_team__icontains=search_query) |
            Q(match__away_team__icontains=search_query) |
            Q(match__league__name__icontains=search_query) |
            Q(match__league__country__name__icontains=search_query)
        )

    # Initialize table headers and data
    table_headers = [
        "Sport Type",
        "Match Name",
        "Prediction",
        "Odds",
        "Result",
    ]
    table_data = []

    # Define item-specific options and data mapping for each sport
    sport_item_mapping = {
        "soccer": {
            "3 way(1X2)": [
                ("Home Win Probability %", "home_team_win_probability"),
                ("Draw Probability %", "draw_probability"),
                ("Away Win Probability %", "away_team_win_probability"),
                lambda match: {
                    "home_team_win_probability": (
                        math.ceil(match.home_team_win_probability)
                        if match.home_team_win_probability
                        else "---"
                    ),
                    "draw_probability": (
                        math.ceil(match.draw_probability)
                        if match.draw_probability
                        else "---"
                    ),
                    "away_team_win_probability": (
                        math.ceil(match.away_team_win_probability)
                        if match.away_team_win_probability
                        else "---"
                    ),
                },
            ],
            "bts(GG)": [
                ("GG Probability %", "gg_probability"),
                ("No GG Probability %", "no_gg_probability"),
                lambda match: {
                    "gg_probability": (
                        math.ceil(match.gg_probability)
                        if match.gg_probability
                        else "---"
                    ),
                    "no_gg_probability": (
                        math.ceil(match.no_gg_probability)
                        if match.no_gg_probability
                        else "---"
                    ),
                },
            ],
            "total(OVER/UNDER)": [
                ("OVER 2.5 %", "over_2_5_probability"),
                ("UNDER 2.5 %", "under_2_5_probability"),
                lambda match: {
                    "over_2_5_probability": (
                        math.ceil(match.over_2_5_probability)
                        if match.over_2_5_probability
                        else "---"
                    ),
                    "under_2_5_probability": (
                        math.ceil(match.under_2_5_probability)
                        if match.under_2_5_probability
                        else "---"
                    ),
                },
            ],
            "total_1_5(OVER/UNDER)": [
                ("OVER 1.5 %", "over_1_5_probability"),
                ("UNDER 1.5 %", "under_1_5_probability"),
                lambda match: {
                    "over_1_5_probability": (
                        math.ceil(match.over_1_5_probability)
                        if match.over_1_5_probability
                        else "---"
                    ),
                    "under_1_5_probability": (
                        math.ceil(match.under_1_5_probability)
                        if match.under_1_5_probability
                        else "---"
                    ),
                },
            ],
            "total_3_5(OVER/UNDER)": [
                ("OVER 3.5 %", "over_3_5_probability"),
                ("UNDER 3.5 %", "under_3_5_probability"),
                lambda match: {
                    "over_3_5_probability": (
                        math.ceil(match.over_3_5_probability)
                        if match.over_3_5_probability
                        else "---"
                    ),
                    "under_3_5_probability": (
                        math.ceil(match.under_3_5_probability)
                        if match.under_3_5_probability
                        else "---"
                    ),
                },
            ],
            "total_4_5(OVER/UNDER)": [
                ("OVER 4.5 %", "over_4_5_probability"),
                ("UNDER 4.5 %", "under_4_5_probability"),
                lambda match: {
                    "over_4_5_probability": (
                        math.ceil(match.over_4_5_probability)
                        if match.over_4_5_probability
                        else "---"
                    ),
                    "under_4_5_probability": (
                        math.ceil(match.under_4_5_probability)
                        if match.under_4_5_probability
                        else "---"
                    ),
                },
            ],
            "total_5_5(OVER/UNDER)": [
                ("OVER 5.5 %", "over_5_5_probability"),
                ("UNDER 5.5 %", "under_5_5_probability"),
                lambda match: {
                    "over_5_5_probability": (
                        math.ceil(match.over_5_5_probability)
                        if match.over_5_5_probability
                        else "---"
                    ),
                    "under_5_5_probability": (
                        math.ceil(match.under_5_5_probability)
                        if match.under_5_5_probability
                        else "---"
                    ),
                },
            ],
            "cards": [
                ("selection probability %", "total_cards_probability"),
                lambda match: {
                    "total_cards_probability": (
                        math.ceil(match.total_cards_probability)
                        if match.total_cards_probability
                        else "---"
                    )
                },
            ],
            "corners": [
                ("selection probability %", "total_corners_probability"),
                lambda match: {
                    "total_corners_probability": (
                        math.ceil(match.total_corners_probability)
                        if match.total_corners_probability
                        else "---"
                    )
                },
            ],
            "correct_score": [
                lambda match: {
                    "correct_score": (
                        f"{match.home_team_goals}-{match.away_team_goals}"
                        if match.home_team_goals is not None
                        and match.away_team_goals is not None
                        else "Waiting..."
                    )
                },
            ],
            "double chance(12,1X,X2)": [
                ("1X \n probability|normalized probability %", "dc1x_probability"),
                ("X2 \n probability|normalized probability %", "dcx2_probability"),
                (
                    "12 \n probability|normalized probability  %",
                    "dc12_probability",
                ),
                lambda match: {
                    "dc1x_probability": (
                        f"{math.ceil(match.dc1x_probability) if match.dc1x_probability else'---'}|{(match.dc1x_normalized_probability) if match.dc1x_normalized_probability else'---'}"
                    ),
                    "dcx2_probability": (
                        f"{math.ceil(match.dcx2_probability) if match.dcx2_probability else'---'}|{(match.dcx2_normalized_probability) if match.dcx2_normalized_probability else'---'}"
                    ),
                    "dc12_probability": (
                        f"{math.ceil(match.dc12_probability) if match.dc12_probability else'---'}|{(match.dc12_normalized_probability) if match.dc12_normalized_probability else'---'}"
                    ),
                },
            ],
        },
        "basketball": {
            "3 way": [
                ("Home Win Probability", "home_team_win_probability"),
                ("Draw Probability", "draw_probability"),
                ("Away Win Probability", "away_team_win_probability"),
                lambda match: {
                    "home_team_win_probability": (
                        math.ceil(match.home_team_win_probability)
                        if match.home_team_win_probability
                        else "---"
                    ),
                    "draw_probability": (
                        math.ceil(match.draw_probability)
                        if match.draw_probability
                        else "---"
                    ),
                    "away_team_win_probability": (
                        math.ceil(match.away_team_win_probability)
                        if match.away_team_win_probability
                        else "---"
                    ),
                },
            ],
            "total overtime": [
                ("selection probability %", "expected_goals_overtime_probability"),
                lambda match: {
                    "expected_goals_overtime_probability": (
                        math.ceil(match.expected_goals_overtime_probability)
                        if match.expected_goals_overtime_probability
                        else "---"
                    )
                },
            ],
            "total halftime": [
                ("selection probability %", "expected_goals_halftime_probability"),
                lambda match: {
                    "expected_goals_halftime_probability": (
                        math.ceil(match.expected_goals_halftime_probability)
                        if match.expected_goals_halftime_probability
                        else "---"
                    )
                },
            ],
            "home total": [
                ("selection probability(ft) %", "expected_goals_hometeam_probability"),
                lambda match: {
                    "expected_goals_hometeam_probability": (
                        math.ceil(match.expected_goals_hometeam_probability)
                        if match.expected_goals_hometeam_probability
                        else "---"
                    )
                },
            ],
            "away total": [
                ("selection probability(ft) %", "expected_goals_awayteam_probability"),
                lambda match: {
                    "expected_goals_awayteam_probability": (
                        math.ceil(match.expected_goals_awayteam_probability)
                        if match.expected_goals_awayteam_probability
                        else "---"
                    )
                },
            ],
        },
        "tennis": {
            "3 way": [
                ("Home Win Probability", "home_win_probability"),
                ("Away Win Probability", "away_win_probability"),
                lambda match: {
                    "home_win_probability": (
                        math.ceil(match.home_team_win_probability)
                        if match.home_team_win_probability
                        else "---"
                    ),
                    "away_win_probability": (
                        math.ceil(match.away_team_win_probability)
                        if match.away_team_win_probability
                        else "---"
                    ),
                },
            ],
            "total": [
                ("total games probability(ft) %", "total_games_probability"),
                lambda match: {
                    "total_games_probability": (
                        math.ceil(match.total_games_probability)
                        if match.total_games_probability
                        else "---"
                    )
                },
            ],
        },
    }

    # Determine the selected item
    item = item or ("3 way(1X2)" if selected == "soccer" else "3 way")

    # Get selected options and headers (excluding lambda functions)
    options = sport_item_mapping.get(selected, {}).get(item, [])
    table_headers = (
        [
            "Sport Type",
            "Match Name",
        ]
        + options[:-1]  # Exclude the lambda (the last element)
        + [
            "Prediction",
            "Odds",
            "Result",
        ]
    )
    dynamic_headers = table_headers[2:-3]

    # Populate table data
    for match in matches:
        data = {
            "pk": match.match.pk,
            "home_team": match.match.home_team,
            "home_team_logo": match.match.home_team_logo,
            "home_team_score": match.home_team_expected_goals,
            "home_res": match.home_team_goals,
            "away_res": match.away_team_goals,
            "away_team_score": match.away_team_expected_goals,
            "away_team": match.match.away_team,
            "away_team_logo": match.match.away_team_logo,
            "sport_type": match.match.sport.name,
            "league":match.match.league.name,
            "country":match.match.league.country.name,
            "flag":match.match.league.country.flag,
            "Temperature": match.match.temperature,
            "Feels_like": match.match.feels_like,
            "Humidity": match.match.humidity,
            "Weather description": match.match.weather_description,
            "Wind speed": match.match.wind_speed,
            "time": (
                match.match.date.strftime("%H:%M:%S")
                if match.match.date and isinstance(match.match.date, datetime)
                else None
            ),
            "match_name": match.match,
            "prediction": get_prediction(match, selected),
            "odds": get_odds(match, selected),
            "get_absolute_url": match.get_absolute_url(),
            "result": get_match_result(match, selected, item),
        }

        if item == "bts(GG)":
            data["prediction"] = get_prediction_bts(match)
            data["odds"] = get_odds_bts(match)
        elif item == "total(OVER/UNDER)":
            data["prediction"] = get_prediction_ov(match)
            data["odds"] = get_odds_ov(match)
        elif item == "total_1_5(OVER/UNDER)":
            data["prediction"] = get_prediction_ov_1_5(match)
            data["odds"] = get_odds_ov_1_5(match)
        elif item == "total_3_5(OVER/UNDER)":
            data["prediction"] = get_prediction_ov_3_5(match)
            data["odds"] = get_odds_ov_3_5(match)
        elif item == "total_4_5(OVER/UNDER)":
            data["prediction"] = get_prediction_ov_4_5(match)
            data["odds"] = get_odds_ov_4_5(match)
        elif item == "total_5_5(OVER/UNDER)":
            data["prediction"] = get_prediction_ov_5_5(match)
            data["odds"] = get_odds_ov_5_5(match)
        elif item == "correct_score":
            data["prediction"] = get_correctd_score(match)
            data["odds"] = get_correct_odds(match)
        elif item == "cards":
            data["prediction"] = get_prediction_cards(match)
            data["odds"] = get_odds_cards(match)
        elif item == "corners":
            data["prediction"] = get_prediction_corners(match)
            data["odds"] = get_odds_corners(match)
        elif item == "double chance(12,1X,X2)":
            data["prediction"] = get_prediction_dc(match)
            data["odds"] = get_odds_dc(match)
        elif item == "total overtime":
            data["prediction"] = get_prediction_basketball_overtime_total(match)
            data["odds"] = get_odds_basketball_overtime_odds(match)
        elif item == "total halftime":
            data["prediction"] = get_prediction_basketball_halftime_total(match)
            data["odds"] = get_odds_basketball_halftime_odds(match)
        elif item == "home total":
            data["prediction"] = get_prediction_basketball_hometeam_total(match)
            data["odds"] = get_odds_basketball_hometeam_odds(match)
        elif item == "away total":
            data["prediction"] = get_prediction_basketball_awayteam_total(match)
            data["odds"] = get_odds_basketball_awayteam_odds(match)
        elif item == "total":
            data["prediction"] = get_prediction_tennis_total(match)
            data["odds"] = get_odds_tennis_total_odds(match)

        else:
            data["prediction"] = get_prediction(match, selected)
            data["odds"] = get_odds(match, selected)

        if options and callable(options[-1]):
            data.update(options[-1](match))

        table_data.append(data)

    # Reconstruct table headers to ensure they're properly formatted
    table_headers = (
        [
            "Sport Type",
            "Match Name",
        ]
        + [name for name, _ in options[:-1]]
        + [
            "Prediction",
            "Odds",
            "Result",
        ]
    )

    return render(
        request,
        "public/index.html",
        {
            "menu": menu,
            "selected_sport": selected,
            "table_headers": table_headers,
            "table_data": table_data,
            "matches": matches,
            "dynamic_headers": dynamic_headers,
            "item": item,
            "day": day,
            "site": site,
            "search_query": search_query
        },
    )

from django.db.models import Q

def search_matches(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"matches": []})  # Return empty response if no query

    matches = Match.objects.filter(
        Q(home_team__icontains=query) |
        Q(away_team__icontains=query) |
        Q(league__name__icontains=query) |
        Q(league__country__name__icontains=query)
    ).select_related("league", "league__country")[:10]  # Limit to 10 results

    results = []
    for match in matches:
        try:
            prediction = FootballPrediction.objects.get(match=match)
            match_url = prediction.get_absolute_url()  # Get URL from related model
        except FootballPrediction.DoesNotExist:
            match_url = "#"  # Default URL if no prediction exists

        results.append({
            "home_team": match.home_team,
            "away_team": match.away_team,
            "league": match.league.name,
            "country": match.league.country.name,
            "url": match_url,
        })

    return JsonResponse({"matches": results})



def get_prediction(match, sport):
    """Determine the prediction based on the probabilities for each sport."""
    if sport == "soccer" or sport == "basketball":
        if (
            match.home_team_win_probability
            and match.draw_probability
            and match.away_team_win_probability
        ):
            home_prob = match.home_team_win_probability
            draw_prob = match.draw_probability
            away_prob = match.away_team_win_probability
            if home_prob > draw_prob and home_prob > away_prob:
                return "1"  # Home win
            elif draw_prob > home_prob and draw_prob > away_prob:
                return "X"  # Draw
            elif away_prob > home_prob and away_prob > draw_prob:
                return "2"  # Away win
            else:
                return "N/A"
        else:
            return "---"
    elif sport == "tennis":
        if match.home_team_win_probability and match.away_team_win_probability:
            home_prob = match.home_team_win_probability
            away_prob = match.away_team_win_probability
            if home_prob > away_prob:
                return "1"  # Home win
            elif away_prob > home_prob:
                return "2"  # Away win
            else:
                return "N/A"
        else:
            return "---"


def get_odds(match, sport):
    """Get odds based on the prediction for each sport."""
    prediction = get_prediction(match, sport)
    if sport == "soccer" or sport == "basketball":
        if prediction != "---":
            if prediction == "1":
                return match.home_team_win_odds
            elif prediction == "X":
                return match.draw_odds
            elif prediction == "2":
                return match.away_team_win_odds
            else:
                return "N/A"
        else:
            return "---"
    elif sport == "tennis":
        if prediction != "---":
            if prediction == "1":
                return match.home_team_win_odds
            elif prediction == "2":
                return match.away_team_win_odds
            else:
                return "N/A"
        else:
            return "---"


def get_prediction_bts(match):
    """Determine the prediction for BTS based on the probabilities."""
    if match.gg_probability and match.no_gg_probability:
        gg_prob = match.gg_probability
        no_gg_prob = match.no_gg_probability
        if gg_prob > no_gg_prob:
            return "YES"  # Both teams to score
        else:
            return "NO"  # Not both teams to score
    else:
        return "---"


def get_correctd_score(match):

    return f"{match.home_team_expected_goals}-{match.away_team_expected_goals}"


def get_correct_odds(match):
    return "---"


def get_odds_bts(match):
    """Get odds based on the prediction for BTS."""
    prediction = get_prediction_bts(match)
    if prediction != "---":
        if prediction == "YES":
            return match.gg_odds  # Odds for both teams to score
        else:
            return match.no_gg_odds
    else:
        return "---"


def get_prediction_ov(match):
    """Determine the prediction for over/under based on the probabilities."""
    if match.over_2_5_probability and match.under_2_5_probability:
        ov_prob = match.over_2_5_probability
        un_prob = match.under_2_5_probability
        if ov_prob > un_prob:
            return "OVER(+2.5)"  # 3+ goals
        else:
            return "UNDER(-2.5)"  # -3 goals
    else:
        return "---"


def get_odds_ov(match):
    """Get odds based on the prediction for over/under."""
    prediction = get_prediction_ov(match)
    if prediction != "---":
        if prediction == "OVER(+2.5)":

            return match.over_2_5_odds  # Odds for over 2.5 to score

        else:
            return match.under_2_5_odds
    else:
        return "---"


def get_prediction_ov_1_5(match):
    """Determine the prediction for over/under 1.5 based on the probabilities."""
    if match.over_1_5_probability and match.under_1_5_probability:
        ov_prob = match.over_1_5_probability
        un_prob = match.under_1_5_probability
        if ov_prob > un_prob:
            return "OVER(+1.5)"  # 2+ goals
        else:
            return "UNDER(-1.5)"  # -2 goals
    else:
        return "---"


def get_odds_ov_1_5(match):
    """Get odds based on the prediction for over/under."""
    prediction = get_prediction_ov_1_5(match)
    if prediction != "---":
        if prediction == "OVER(+1.5)":

            return match.over_1_5_odds  # Odds for over 1.5 to score

        else:
            return match.under_1_5_odds
    else:
        return "---"


def get_prediction_ov_3_5(match):
    """Determine the prediction for over/under 3.5 based on the probabilities."""
    if match.over_3_5_probability and match.under_3_5_probability:
        ov_prob = match.over_3_5_probability
        un_prob = match.under_3_5_probability
        if ov_prob > un_prob:
            return "OVER(+3.5)"  # 4+ goals
        else:
            return "UNDER(-3.5)"  # -4 goals
    else:
        return "---"


def get_odds_ov_3_5(match):
    """Get odds based on the prediction for over/under."""
    prediction = get_prediction_ov_3_5(match)
    if prediction != "---":
        if prediction == "OVER(+3.5)":

            return match.over_3_5_odds  # Odds for over 3.5 to score

        else:
            return match.under_3_5_odds
    else:
        return "---"


def get_prediction_ov_4_5(match):
    """Determine the prediction for over/under 4.5 based on the probabilities."""
    if match.over_4_5_probability and match.under_4_5_probability:
        ov_prob = match.over_4_5_probability
        un_prob = match.under_4_5_probability
        if ov_prob > un_prob:
            return "OVER(+4.5)"  # 5+ goals
        else:
            return "UNDER(-4.5)"  # -5 goals
    else:
        return "---"


def get_odds_ov_4_5(match):
    """Get odds based on the prediction for over/under."""
    prediction = get_prediction_ov_4_5(match)
    if prediction != "---":
        if prediction == "OVER(+4.5)":
            return match.over_4_5_odds  # Odds for over 4.5 to score

        else:
            return match.under_4_5_odds
    else:
        return "---"


def get_prediction_ov_5_5(match):
    """Determine the prediction for over/under 5.5 based on the probabilities."""
    if match.over_5_5_probability and match.under_5_5_probability:
        ov_prob = match.over_5_5_probability
        un_prob = match.under_5_5_probability
        if ov_prob > un_prob:
            return "OVER(+5.5)"  # 6+ goals
        else:
            return "UNDER(-5.5)"  # -6 goals
    else:
        return "---"


def get_odds_ov_5_5(match):
    """Get odds based on the prediction for over/under."""
    prediction = get_prediction_ov_5_5(match)
    if prediction != "---":
        if prediction == "OVER(+5.5)":
            return match.over_5_5_odds  # Odds for over 5.5 to score

        else:
            return match.under_5_5_odds
    else:
        return "---"


def get_prediction_cards(match):
    """Determine the prediction for total based on the probabilities."""
    if match.total_cards:
        return f"{math.ceil(match.total_cards)}+ cards"  # cards
    else:
        return "---"


def get_odds_cards(match):
    """Get odds based on the prediction for cards"""
    prediction = get_prediction_cards(match)
    if prediction != "---":
        return match.total_cards_odds

    else:
        return "---"


def get_prediction_corners(match):
    """Determine the prediction for total corners based on the probabilities."""
    if match.total_corners:
        return f"{math.ceil(match.total_corners)}+ corners"  # cards
    else:
        return "---"


def get_odds_corners(match):
    """Get odds based on the prediction for corners"""
    prediction = get_prediction_corners(match)
    if prediction != "---":
        return match.total_corners_odds

    else:
        return "---"


def get_prediction_dc(match):
    """Determine the dc prediction based on the probabilities for each sport."""

    if match.dc1x_probability and match.dcx2_probability and match.dc12_probability:
        dc1x = match.dc1x_probability
        dcx2 = match.dcx2_probability
        dc12 = match.dc12_probability
        if dc1x > dcx2 and dc1x > dc12:
            return "1X"  # Home win / draw
        elif dcx2 > dc1x and dcx2 > dc12:
            return "X2"  # Draw/away win
        elif dc12 > dc1x and dc12 > dcx2:
            return "12"  # home win/ Away win
        else:
            return "N/A"
    else:
        return "---"


def get_odds_dc(match):
    """Get odds based on the dc prediction for each sport."""
    prediction = get_prediction_dc(match)
    if prediction != "---":
        if prediction == "1X":
            if match.dc1x_odds:
                return match.dc1x_odds
            else:
                return "---"
        elif prediction == "X2":
            if match.dcx2_odds:
                return match.dcx2_odds
            else:
                return "---"
        elif prediction == "12":
            if match.dc12_odds:
                return match.dc12_odds
            else:
                return "---"
        else:
            return "N/A"
    else:
        return "---"


def get_prediction_basketball_overtime_total(match):
    """Determine the prediction for total basketball based on the probabilities."""
    if match.expected_goals_overtime:
        return f"{math.ceil(match.expected_goals_overtime)}+ goals"  # cards
    else:
        return "---"


def get_odds_basketball_overtime_odds(match):
    """Get odds based on the prediction for overtime basketball"""
    prediction = get_prediction_basketball_overtime_total(match)
    if prediction != "---":
        if match.expected_goals_overtime_odds:
            return match.expected_goals_overtime_odds
        else:
            return "---"
    else:
        return "---"


def get_prediction_basketball_halftime_total(match):
    """Determine the prediction for halftime total basketball based on the probabilities."""
    if match.expected_goals_halftime:
        return f"{math.ceil(match.expected_goals_halftime)}+ halftime goals"
    else:
        return "---"


def get_odds_basketball_halftime_odds(match):
    """Get odds based on the prediction for halftime basketball"""
    prediction = get_prediction_basketball_halftime_total(match)
    if prediction != "---":
        if match.expected_goals_halftime_odds:
            return match.expected_goals_halftime_odds
        else:
            return "---"
    else:
        return "---"


def get_prediction_basketball_hometeam_total(match):
    """Determine the prediction for hometeam total basketball based on the probabilities."""
    if match.expected_goals_hometeam:
        return f"{match.match.home_team}--{math.ceil(match.expected_goals_hometeam)}+  goals"
    else:
        return "---"


def get_odds_basketball_hometeam_odds(match):
    """Get odds based on the prediction for home team total basketball"""
    prediction = get_prediction_basketball_halftime_total(match)
    if prediction != "---":
        if match.expected_goals_hometeam_odds:
            return match.expected_goals_hometeam_odds
        else:
            return "---"
    else:
        return "---"


def get_prediction_basketball_awayteam_total(match):
    """Determine the prediction for away total basketball based on the probabilities."""
    if match.expected_goals_awayteam:
        return f"{match.match.away_team}--{math.ceil(match.expected_goals_awayteam)}+ goals"
    else:
        return "---"


def get_odds_basketball_awayteam_odds(match):
    """Get odds based on the prediction for expected_goals_awayteam_total basketball"""
    prediction = get_prediction_basketball_halftime_total(match)
    if prediction != "---":
        if match.expected_goals_awayteam_odds:
            return match.expected_goals_awayteam_odds
        else:
            return "---"
    else:
        return "---"


def get_prediction_tennis_total(match):
    """Determine the prediction for total tenis based on the probabilities."""
    if match.total_games:
        return f"{math.ceil(match.total_games)}+ games"
    else:
        return "---"


def get_odds_tennis_total_odds(match):
    """Get odds based on the prediction for total tennis"""
    prediction = get_prediction_tennis_total(match)
    if prediction != "---":
        if match.total_games_odds:
            return match.total_games_odds
        else:
            return "---"
    else:
        return "---"


def get_match_result(match, selected, item):
    if selected == "soccer":
        if item == "bts(GG)":
            return match.gg_match_result
        elif item == "total(OVER/UNDER)":
            return match.o_2_5_match_result
        elif item == "total_1_5(OVER/UNDER)":
            return match.o_1_5_match_result
        elif item == "total_3_5(OVER/UNDER)":
            return match.o_3_5_match_result
        elif item == "total_4_5(OVER/UNDER)":
            return match.o_4_5_match_result
        elif item == "total_5_5(OVER/UNDER)":
            return match.o_5_5_match_result
        elif item == "cards":
            return match.total_card_result
        elif item == "corners":
            return match.total_card_result
        elif item == "double chance(12,1X,X2)":
            return match.dc_result
    elif selected == "basketball":
        if item == "total overtime":
            return match.tovertime_match_result
        elif item == "total halftime":
            return match.thalftime_match_result
        elif item == "home total":
            return match.t_hometeam_result
        elif item == "away total":
            return match.t_awayteam_result
    elif selected == "tennis":
        return match.tgame_match_result

    return match.three_way_match_result  # Default return if no conditions met


def footballview(request, pk, home_team_slug, away_team_slug, time, sport_slug):
    match = get_object_or_404(FootballPrediction, pk=pk)
    site = get_object_or_404(SiteInformation, pk=1)

    home_score = match.home_team_goals
    away_score = match.away_team_goals
    match_data = {
        "winner": {
            "prediction": get_prediction(match, match.match.sport.name),
            "probability": (
                math.ceil(match.home_team_win_probability)
                if get_prediction(match, match.match.sport.name) == "1"
                else (
                    math.ceil(match.draw_probability)
                    if get_prediction(match, match.match.sport.name) == "X"
                    else (
                        math.ceil(match.away_team_win_probability)
                        if get_prediction(match, match.match.sport.name) == "2"
                        else None
                    )
                )
            ),
            "odds": get_odds(match, match.match.sport.name),
        },
        "both teams to score(gg)": {
            "prediction": get_prediction_bts(match),
            "probability": (
                math.ceil(match.gg_probability)
                if get_prediction_bts(match) == "YES"
                else (
                    math.ceil(match.no_gg_probability)
                    if get_prediction_bts(match) == "NO"
                    else None
                )
            ),
            "odds": get_odds_bts(match),
        },
        "over 2.5": {
            "prediction": get_prediction_ov(match),
            "probability": (
                math.ceil(match.over_2_5_probability)
                if get_prediction_ov(match) == "OVER(+2.5)"
                else (
                    math.ceil(match.under_2_5_probability)
                    if get_prediction_bts(match) == "UNDER(-2.5)"
                    else None
                )
            ),
            "odds": get_odds_ov(match),
        },
        "total corners": {
            "prediction": get_prediction_corners(match),
            "probability": (match.total_corners_probability),
            "odds": get_odds_corners(match),
        },
        "total cards": {
            "prediction": get_prediction_cards(match),
            "probability": (match.total_cards_probability),
            "odds": get_odds_cards(match),
        },
        "correct_score": {
            "prediction": get_correctd_score(match),
            "probability": "N/A",
            "odds": get_correct_odds(match),
        },
        "double chance": {
            "prediction": get_prediction_dc(match),
            "probability": (
                math.ceil(match.dc1x_probability)
                if get_prediction_dc(match) == "1X"
                else (
                    match.dcx2_probability
                    if get_prediction_dc(match) == "X2"
                    else (
                        match.dc12_probability
                        if get_prediction_dc(match) == "12"
                        else None
                    )
                )
            ),
            "odds": get_odds_dc(match),
        },
    }
    headers = []
    for market_name, market_data in match_data.items():
        # Only check for 'prediction' and 'probability'
        if (
            market_data["prediction"] is not None and market_data["prediction"] != "---"
        ) and (
            market_data["probability"] is not None
            and market_data["probability"] != "---"
        ):
            headers.append(market_name)

    context = {
        "match": match,
        "time": time,
        "sport_slug": sport_slug,
        "headers": headers,
        "match_data": match_data,
        "site": site,
        "home_score": home_score,
        "away_score": away_score,
    }

    return render(request, "public/footballview.html", context)


def Tennisview(request, pk, home_team_slug, away_team_slug, time, sport_slug):
    site = get_object_or_404(SiteInformation, pk=1)
    match = get_object_or_404(TennisPrediction, pk=pk)
    match_data = {
        "winner": {
            "prediction": get_prediction(match, match.match.sport.name),
            "probability": (
                math.ceil(match.home_team_win_probability)
                if get_prediction(match, match.match.sport.name) == "1"
                else (
                    math.ceil(match.away_team_win_probability)
                    if get_prediction(match, match.match.sport.name) == "2"
                    else None
                )
            ),
            "odds": get_odds(match, match.match.sport.name),
            "result": match.three_way_match_result,
        },
        "total games": {
            "prediction": get_prediction_tennis_total(match),
            "probability": (match.total_games_probability),
            "odds": get_odds_tennis_total_odds(match),
            "result": match.tgame_match_result,
        },
    }
    headers = []
    for market_name, market_data in match_data.items():
        # Only check for 'prediction' and 'probability'
        if (
            market_data["prediction"] is not None and market_data["prediction"] != "---"
        ) and (
            market_data["probability"] is not None
            and market_data["probability"] != "---"
        ):
            headers.append(market_name)

    context = {
        "match": match,
        "time": time,
        "sport_slug": sport_slug,
        "headers": headers,
        "match_data": match_data,
        "site": site,
    }

    return render(request, "public/tennisview.html", context)


def Basketballview(request, pk, home_team_slug, away_team_slug, time, sport_slug):
    site = get_object_or_404(SiteInformation, pk=1)
    match = get_object_or_404(BasketballPrediction, pk=pk)
    match_data = {
        "winner": {
            "prediction": get_prediction(match, match.match.sport.name),
            "probability": (
                math.ceil(match.home_team_win_probability)
                if get_prediction(match, match.match.sport.name) == "1"
                else (
                    math.ceil(match.draw_probability)
                    if get_prediction(match, match.match.sport.name) == "X"
                    else (
                        math.ceil(match.away_team_win_probability)
                        if get_prediction(match, match.match.sport.name) == "2"
                        else None
                    )
                )
            ),
            "odds": get_odds(match, match.match.sport.name),
            "result": match.three_way_match_result,
        },
        "total overtime": {
            "prediction": get_prediction_basketball_overtime_total(match),
            "probability": (match.expected_goals_overtime_probability),
            "odds": get_odds_basketball_overtime_odds(match),
            "result": match.tovertime_match_result,
        },
        "total halftime": {
            "prediction": get_prediction_basketball_halftime_total(match),
            "probability": (match.expected_goals_halftime_probability),
            "odds": get_odds_basketball_halftime_odds(match),
            "result": match.thalftime_match_result,
        },
        match.match.home_team
        + " total": {
            "prediction": get_prediction_basketball_hometeam_total(match),
            "probability": (match.expected_goals_hometeam_probability),
            "odds": get_odds_basketball_hometeam_odds(match),
            "result": match.t_hometeam_result,
        },
        match.match.away_team
        + " total": {
            "prediction": get_prediction_basketball_awayteam_total(match),
            "probability": (match.expected_goals_awayteam_probability),
            "odds": get_odds_basketball_awayteam_odds(match),
            "result": match.t_awayteam_result,
        },
    }
    headers = []
    for market_name, market_data in match_data.items():
        # Only check for 'prediction' and 'probability'
        if (
            market_data["prediction"] is not None and market_data["prediction"] != "---"
        ) and (
            market_data["probability"] is not None
            and market_data["probability"] != "---"
        ):
            headers.append(market_name)

    context = {
        "match": match,
        "time": time,
        "sport_slug": sport_slug,
        "headers": headers,
        "match_data": match_data,
        "site": site,
    }

    return render(request, "public/basketballview.html", context)


from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required


def office(request):
    vip_status, created = VIPStatus.objects.get_or_create(id=1)
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return render(request, "private/o.html", {"vip_status": vip_status})
        else:
            return redirect("square:index")  # Redirect if credentials are wrong
    return render(request, "private/superuser_login.html")


def refresh(request):
    return render(request, "private/refresh.html")


from django.http import HttpResponse
import requests
import json
from datetime import datetime
from backend.models import Country, Season, League
from django.conf import settings

def recreate_football_league(request):

    # API details
    url = "https://v3.football.api-sports.io/leagues"
    headers = {
        "x-rapidapi-key": settings.API_FOOTBALL,
        "x-rapidapi-host": "v3.football.api-sports.io",
    }

    # Make the request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        leagues = response.json()["response"]

        for league_data in leagues:
            # Extract country information
            country_data = league_data["country"]
            country_name = country_data["name"]
            country_code = country_data.get("code", None)
            country_flag = country_data.get("flag", None)

            # Check if the country already exists or create it
            country, created = Country.objects.get_or_create(
                name=country_name, defaults={"code": country_code, "flag": country_flag}
            )

            # Process seasons
            for season_data in league_data["seasons"]:
                season_year = season_data["year"]
                season_start_date = datetime.strptime(
                    season_data["start"], "%Y-%m-%d"
                ).date()
                season_end_date = datetime.strptime(
                    season_data["end"], "%Y-%m-%d"
                ).date()
                season_current = season_data["current"]

                # Check if the season already exists or create it
                season, created = Season.objects.get_or_create(
                    year=season_year,
                    start_date=season_start_date,
                    end_date=season_end_date,
                    current=season_current,
                )

                # Process league information
                league_name = league_data["league"]["name"]
                league_type = league_data["league"]["type"]
                league_logo = league_data["league"]["logo"]
                league_id = league_data["league"]["id"]

                # Check if the league already exists or create it
                league, created = League.objects.get_or_create(
                    league_id=league_id,
                    defaults={
                        "name": league_name,
                        "type": league_type,
                        "logo": league_logo,
                        "country": country,
                    },
                )

                # Add season to the league if it's not already added
                league.seasons.add(season)

    else:
        return HttpResponse(
            f"Failed with status code: {response.status_code}", status=400
        )

    return render(request, "private/success_recreate_football_league.html")


from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import date, timedelta

from backend.models import MatchDate, League
from backend.models import Match as M


API_KEY = settings.API_FOOTBALL
API_URL = "https://v3.football.api-sports.io/fixtures"


def fetch_matches_view(request):
    vip_status, created = VIPStatus.objects.get_or_create(id=1)
    if request.method == "POST":
        fetch_date = request.POST.get("fetch_date")

        if fetch_date:
            # Determine the date to fetch
            if fetch_date == "today":
                target_date = date.today()
            elif fetch_date == "tomorrow":
                target_date = date.today() + timedelta(days=1)
            elif fetch_date == "yesterday":
                target_date = date.today() - timedelta(days=1)

            # API request headers
            headers = {"x-apisports-key": API_KEY}

            # Fetch matches from the API
            response = requests.get(f"{API_URL}?date={target_date}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                fixture_list = data.get("response", [])

                # Save matches in the database
                match_date_obj, _ = MatchDate.objects.get_or_create(date=target_date)
                for fixture in fixture_list:
                    fixture_info = fixture.get("fixture", {})
                    league_info = fixture.get("league", {})
                    home_team = fixture.get("teams", {}).get("home", {})
                    away_team = fixture.get("teams", {}).get("away", {})

                    # Fetch the league from the database
                    league = League.objects.filter(
                        league_id=league_info.get("id")
                    ).first()
                    if not league:
                        # If league not found, log an error (or handle as needed)
                        continue

                    # Save the match
                    M.objects.update_or_create(
                        match_id=fixture_info.get("id"),
                        defaults={
                            "date": fixture_info.get("date"),
                            "referee": fixture_info.get("referee"),
                            "timezone": fixture_info.get("timezone"),
                            "match_date": match_date_obj,
                            "venue_name": fixture_info.get("venue", {}).get(
                                "name", "N/A"
                            ),
                            "venue_city": fixture_info.get("venue", {}).get(
                                "city", "N/A"
                            ),
                            "home_team_name": home_team.get("name"),
                            "home_team_logo": home_team.get("logo"),
                            "home_team_id": home_team.get("id"),  # Added home team ID
                            "away_team_name": away_team.get("name"),
                            "away_team_logo": away_team.get("logo"),
                            "away_team_id": away_team.get("id"),  # Added away team ID
                            "league": league,
                        },
                    )
                return JsonResponse(
                    {
                        "message": f"Matches for {target_date} fetched and saved successfully."
                    }
                )
            else:
                return JsonResponse(
                    {"error": "Failed to fetch data from the API."}, status=400
                )

    return render(request, "private/o.html", {"vip_status": vip_status})


from backend.models import Country, Season, League, MatchDate


from django.contrib import messages
from datetime import datetime, timedelta


def select_football_prediction(request):
    if request.method == "POST":
        # Get selected match IDs from the form
        selected_matches = request.POST.getlist("selected_matches")

        # Ensure the user doesn't select more than 15 matches
        # if len(selected_matches) > 25:
        #     messages.error(request, "You can only select up to 25 matches.")
        #     return redirect("square:select_football_prediction")

        # Update the 'to_be_predicted' field for the selected matches
        for match_id in selected_matches:
            match = M.objects.get(id=match_id)
            match.to_be_predicted = True
            match.save()

        # Display a success message with the selected matches
        selected_match_names = M.objects.filter(id__in=selected_matches)
        match_names = ", ".join(
            [
                match.home_team_name + " vs " + match.away_team_name
                for match in selected_match_names
            ]
        )
        messages.success(
            request,
            f"The following matches have been successfully selected: {match_names}",
        )

        return redirect("square:select_football_prediction")

    # Get today's date and tomorrow's date
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    # Get the selected filter from the form (default is today's matches)
    date_filter = request.GET.get("date_filter", "today")
    # Get the search query (if any)
    search_query = request.GET.get("search", "")
    selected_matches = request.GET.get("selected_matches", "").split(",")
    selected_matches = [match_id for match_id in selected_matches if match_id]  # Remove empty values


    # Fetch matches based on the date filter (today or tomorrow)
    if date_filter == "today":
        matches = M.objects.filter(date__date=today, to_be_predicted=False)
    elif date_filter == "tomorrow":
        matches = M.objects.filter(date__date=tomorrow, to_be_predicted=False)
    else:
        matches = M.objects.filter(to_be_predicted=False)

    if search_query:
        matches = matches.filter(
            Q(home_team_name__icontains=search_query) |
            Q(away_team_name__icontains=search_query) |
            Q(league__name__icontains=search_query) |
            Q(league__country__name__icontains=search_query)
        )
    return render(
        request,
        "private/select_football_prediction.html",
        {
            "matches": matches,
            "today": today,
            "tomorrow": tomorrow,
            "date_filter": date_filter,
            "search_query": search_query,
            "selected_matches": selected_matches,
        },
    )


from django.shortcuts import render
from django.utils.timezone import localdate
from datetime import timedelta


def start_soccer_prediction(request, date):
    today = localdate()
    tomorrow = today + timedelta(days=1)

    if date == "today":
        matches = M.objects.filter(date__date=today, to_be_predicted=True)
    elif date == "tomorrow":
        matches = M.objects.filter(date__date=tomorrow, to_be_predicted=True)
    else:
        matches = M.objects.filter(to_be_predicted=True)

    return render(request, "private/start_soccer_prediction.html", {"matches": matches})


import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from backend.adams_square import (
    Jerusalem,
)  # Importing the Jerusalem class from the script


from backend.tasks import fetch_data_for_matches, analyze_fetched_data


@csrf_exempt
def predict_all_matches(request):
    if request.method == "POST":
        matches_data = request.POST.get("matches")
        if matches_data:
            try:
                # Try parsing the matches data as JSON
                matches = json.loads(matches_data)

                result = fetch_data_for_matches.delay(
                    matches
                )  # Send the whole list in a single task
                task_id = result.id  # Get the task ID

                # Render a template to show the progress with the task ID
                return render(
                    request, "private/data_progress.html", {"fetch_task_id": task_id}
                )
            except json.JSONDecodeError:
                return HttpResponse("Invalid JSON format.", status=400)
        else:
            return HttpResponse("No match data provided.", status=400)
    else:
        return HttpResponse("Invalid request method.", status=400)


from backend.models import TaskProgress
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def check_task_progress(request, task_id):
    """Fetch progress for a specific task."""
    try:
        task_progress = TaskProgress.objects.filter(task_id=task_id).first()
    except TaskProgress.DoesNotExist:
        return JsonResponse({"status": "Failed or Not Started", "progress": 0})

    if task_progress:
        response_data = {
            "status": "In Progress",
            "progress": task_progress.progress,
            "successful": task_progress.successful,
            "failed": task_progress.failed,
            "to_be_processed": task_progress.to_be_processed(),
            "total": task_progress.total,
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({"status": "Failed or Not Started", "progress": 0})


def see_data_progress(request):
    """Render the page to display progress for the most recent fetch and analyze tasks."""
    try:
        # Fetch the latest task progress for fetching data and analyzing data
        task_progress = TaskProgress.objects.latest("last_updated")
    except TaskProgress.DoesNotExist:
        task_progress = None

    # Extract progress details for the analyze task (default to 0 if not available)
    if task_progress:
        progress = task_progress.progress
        successful = task_progress.successful
        failed = task_progress.failed
        to_be_processed = task_progress.to_be_processed()

        total = task_progress.total
        fetch_task_id = task_progress.task_id
    else:
        total_processed = successful = failed = to_be_processed = 0
        fetch_task_id = None

    # Pass task details to the template
    return render(
        request,
        "private/data_progress.html",
        {
            "total": total,
            "progress": progress,
            "analyze_task_id": fetch_task_id,
            "total_processed": total,
            "successful": successful,
            "failed": failed,
            "to_be_processed": to_be_processed,
        },
    )


from django.shortcuts import render
from .models import Match, Fixture, FootballPrediction
from django.db.models import Q


def update_matches_with_fixtures(request):
    matches = Match.objects.filter(updated=False)
    fixtures = Fixture.objects.filter(Q(status_short="FT") | Q(status_short="PEN"))

    fixture_map = {
        fixture.fixture_id: fixture for fixture in fixtures
    }  # Create a fixture lookup dictionary

    for match in matches:
        if match.match_id in fixture_map:  # Check if match_id exists in fixture
            fixture = fixture_map[match.match_id]

            # Update FootballPrediction fields
            football_prediction = FootballPrediction.objects.filter(match=match).first()
            if football_prediction:
                football_prediction.home_team_expected_goals = (
                    fixture.score_fulltime_home
                )
                football_prediction.away_team_expected_goals = (
                    fixture.score_fulltime_away
                )
                football_prediction.save()

            # Mark match as updated
            match.updated = True
            match.save()

    return render(
        request,
        "matches_fixtures_list.html",
        {"matches": matches, "fixtures": fixtures},
    )


today = timezone.now().date()


def premium(request):
    matches = Match.objects.filter(is_premium=True).prefetch_related(
        "footballprediction_set"
    )

    # Process matches based on gold_bar field
    match_context = []
    for match in matches:
        football = get_object_or_404(FootballPrediction, match=match)

        if match.gold_bar == "gg":
            description = "both teams to score"
            prediction = get_prediction_bts(football)
            odds = get_odds_bts(football)

        elif match.gold_bar == "three_way":
            description = "team to win"
            prediction = get_prediction(football, football.match.sport.name)
            odds = get_odds(
                football, football.match.sport.name
            )  # Added odds assignment

        elif match.gold_bar == "ov":
            description = "total goals"
            prediction = get_prediction_ov(football)
            odds = get_odds_ov(football)

        else:
            description = ""
            prediction = None
            odds = None  # Changed from "----" for consistency

        match_context.append(
            {
                "matches": match,
                "description": description,
                "prediction": prediction,
                "odds": odds,
            }
        )

    return render(request, "public/premium.html", {"matches": match_context})


from django.db.models import Q


def destroy_premium(request):
    # Update all premium matches to set is_premium to False
    updated_count = Match.objects.filter(is_premium=True).update(is_premium=False)

    # Add a success message
    if updated_count > 0:
        messages.success(
            request, f"{updated_count} premium match(es) removed successfully."
        )
    else:
        messages.info(request, "No premium matches were found to remove.")

    # Redirect to the home page
    return redirect("square:index")


def recreate_premium(request):
    # Update matches where gold_bar is not "N/A" to set is_premium to True
    updated_count = Match.objects.filter(~Q(gold_bar="N/A")).update(is_premium=True)

    # Add success or info message based on the update result
    if updated_count > 0:
        messages.success(
            request, f"{updated_count} premium match(es) recreated successfully."
        )
    else:
        messages.info(request, "No matches available for premium recreation.")

    # Redirect to the home page
    return redirect("square:index")


def privacy(request):
    site = get_object_or_404(SiteInformation, pk=1)
    return render(request, "public/privacy.html", {"site": site})


def terms(request):
    site = get_object_or_404(SiteInformation, pk=1)
    return render(request, "public/terms.html", {"site": site})


def custom_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("square:index")  # Redirect to home after successful login
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "private/login.html")  # Render login page


from django.contrib.auth import logout


def custom_logout(request):
    logout(request)  # Logs out the user
    return redirect("square:index")  # Redirects to homepage after logout


from django.conf import settings
from django.contrib.auth.decorators import user_passes_test


def is_admin(user):
    return user.is_superuser  # Only superusers can toggle maintenance mode


@user_passes_test(is_admin)
def toggle_maintenance(request):
    settings.MAINTENANCE_MODE = not settings.MAINTENANCE_MODE
    return redirect("square:index")  # Redirect back to homepage


from django.http import FileResponse, Http404
from django.conf import settings
import os


def serve_media(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("File not found")
    return FileResponse(open(file_path, "rb"))


def payment_success(request):
    """
    View to render the payment success page.
    """
    return render(request, "public/payment_success.html")


def payment_failed(request):
    """
    Render the payment failed page.
    """
    return render(request, "public/payment_failed.html")


PAYSTACK_SECRET_KEY = "sk_live_ec9a4539e28760d416c6aa58b9053c53a52db484"

# views.py

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import json
import hmac
import hashlib

# Paystack secret key (from your Paystack dashboard)
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY


@csrf_exempt
def paystack_webhook(request):
    """
    Webhook to handle Paystack payment notifications.
    """
    if request.method == "POST":
        # Verify the request is from Paystack
        payload = request.body
        signature = request.headers.get("X-Paystack-Signature")

        if not signature:
            return HttpResponse(status=400)  # Bad request

        # Compute HMAC SHA512 hash
        computed_signature = hmac.new(
            PAYSTACK_SECRET_KEY.encode("utf-8"), payload, hashlib.sha512
        ).hexdigest()

        # Verify the signature
        if computed_signature != signature:
            return HttpResponse(status=403)  # Forbidden

        # Parse the payload
        try:
            data = json.loads(payload)
            event = data.get("event")
            payment_data = data.get("data")

            # Handle different events
            if event == "charge.success":
                # Payment was successful
                email = payment_data.get("customer", {}).get("email")
                amount = (
                    payment_data.get("amount") / 100
                )  # Convert to currency (e.g., NGN to ₦)
                reference = payment_data.get("reference")

                # Send email to the user
                subject = "Payment Received - Jerusqore"
                message = f"""
                Hello,

                Thank you for your payment of ₦{amount:.2f} (Reference: {reference}).
                Your payment has been successfully received, and your subscription is now active.

                Start enjoying premium predictions on Jerusqore!

                Best regards,
                The Jerusqore Team
                """
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

                print(f"Email sent to {email} for successful payment.")
                return JsonResponse({"status": "success"})

            elif event == "charge.failed":
                # Payment failed
                print("Payment failed:", payment_data)
                return JsonResponse({"status": "failed"})

            else:
                # Handle other events (e.g., refunds)
                print("Unhandled event:", event)
                return JsonResponse({"status": "unhandled"})

        except json.JSONDecodeError:
            return HttpResponse(status=400)  # Bad request

    return HttpResponse(status=405)  # Method not allowed


from .forms import PaymentForm
from django.core.mail import send_mail
from .models import Payslips


def initiate_payment(request):
    """
    Render the payment form and initialize Paystack payment.
    """
    vip_status = VIPStatus.objects.first()
    amount = (
        int(vip_status.price * 100) if vip_status else 50000
    )  # Convert KES to kobo (default 100 KES)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]

            # Paystack API endpoint
            url = "https://api.paystack.co/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            }
            data = {
                "email": email,
                "amount": amount,
                "callback_url": "https://www.jeruscore.com/payment/verify/",  # Callback URL for verification
            }

            # Make API request to Paystack
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                # Redirect to Paystack payment page
                payment_url = response.json()["data"]["authorization_url"]
                return redirect(payment_url)
            else:
                # Handle API error
                return render(request, "public/payment_failed.html")
    else:
        form = PaymentForm()

    return render(request, "public/payment_page.html", {"form": form})


from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Match
from backend.models import League, Country
from .models import FootballPrediction


def verify_payment(request):
    """
    Verify Paystack payment, send confirmation email, and redirect to success or failure page.
    """

    reference = request.GET.get("reference")
    if not reference:
        return redirect("square:payment_failed")

    # Verify payment with Paystack
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    response = requests.get(url, headers=headers)
    result = response.json()
    if result.get("status"):  # Payment successful
        data = result["data"]
        email = data.get("customer", {}).get("email", "")
        phone = data.get("customer", {}).get("phone", "")
        amount = data.get("amount") / 100  # Convert from kobo to Naira/USD
        status = data.get("status")

        # Save to the database
        payment, created = Payslips.objects.get_or_create(
            reference=reference,
            defaults={
                "email": email,
                "phone": phone,
                "amount": amount,
                "status": status,
                "verified": status == "success",
            },
        )

    if response.status_code == 200:
        data = response.json().get("data", {})
        if data.get("status") == "success":
            # Payment successful, get user email
            matches = Match.objects.filter(
                updated=False,
                is_premium=True,
                date__date=today,  # Filter by today's date
            ).prefetch_related("footballprediction_set")
            match_data = []
            for match in matches:
                football = get_object_or_404(FootballPrediction, match=match)

                if match.gold_bar == "gg":
                    description = "both teams to score"
                    prediction = get_prediction_bts(football)
                    odds = get_odds_bts(football)

                elif match.gold_bar == "three_way":
                    description = "team to win"
                    prediction = get_prediction(football, football.match.sport.name)
                    odds = get_odds(football, football.match.sport.name)

                elif match.gold_bar == "ov":
                    description = "total goals"
                    prediction = get_prediction_ov(football)
                    odds = get_odds_ov(football)

                else:
                    description = ""
                    prediction = None
                    odds = None

                match_data.append(
                    {
                        "match": match,
                        "description": description,
                        "prediction": prediction,
                        "odds": odds,
                        "league_logo": match.league.logo if match.league else None,
                        "country_name": (
                            match.league.country.name if match.league else None
                        ),
                        "country_flag": (
                            match.league.country.flag if match.league else None
                        ),
                    }
                )

            email = data.get("customer", {}).get("email", "")

            if email:
                # Send confirmation email
                subject = "Premium Match Predictions"
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [email]
                html_content = render_to_string(
                    "public/email_template.html", {"match_data": match_data}
                )
                email = EmailMultiAlternatives(subject, "", from_email, recipient_list)
                email.attach_alternative(html_content, "text/html")
                email.send()
            return redirect("square:payment_success")

    return redirect("square:payment_failed")


from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Match
from backend.models import League, Country
from .models import FootballPrediction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


from django.utils import timezone
from datetime import datetime, timedelta

# Get today's date
today = timezone.now().date()


def send_game(request):
    # Filter matches where the date is today and other conditions
    today = timezone.now().date()
    vip_status = VIPStatus.objects.first()
    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Please enter your email.")
            return redirect("square:send_game") 

        try:
            validate_email(email)  # Validate email format
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("square:send_game")  # Redirect to refresh the page with the message


        matches = Match.objects.filter(
            updated=False, is_premium=True, date__date=today  # Filter by today's date
        ).prefetch_related("footballprediction_set")

        match_data = []
        for match in matches:
            football = get_object_or_404(FootballPrediction, match=match)

            if match.gold_bar == "gg":
                description = "both teams to score"
                prediction = get_prediction_bts(football)
                odds = get_odds_bts(football)

            elif match.gold_bar == "three_way":
                description = "team to win"
                prediction = get_prediction(football, football.match.sport.name)
                odds = get_odds(football, football.match.sport.name)

            elif match.gold_bar == "ov":
                description = "total goals"
                prediction = get_prediction_ov(football)
                odds = get_odds_ov(football)

            else:
                description = ""
                prediction = None
                odds = None

            match_data.append(
                {
                    "match": match,
                    "description": description,
                    "prediction": prediction,
                    "odds": odds,
                    "league_logo": match.league.logo if match.league else None,
                    "country_name": match.league.country.name if match.league else None,
                    "country_flag": match.league.country.flag if match.league else None,
                }
            )

        # Send email
        subject = "Premium Match Predictions"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        html_content = render_to_string(
            "public/email_template.html", {"match_data": match_data}
        )
        email = EmailMultiAlternatives(subject, "", from_email, recipient_list)
        email.attach_alternative(html_content, "text/html")
        email.send()
        messages.success(request, "Predictions have been sent to your email.")
        return redirect("square:payment_success")
    return render(
        request,
        "private/o.html",
        {"vip_status": vip_status},
    )

from .models import VIPStatus


def toggle_vip(request):
    vip_status, created = VIPStatus.objects.get_or_create(id=1, defaults={"price": 500})
    vip_status.is_active = not vip_status.is_active
    vip_status.save()
    return redirect("square:office")  # Ensure this URL is correct


def market(request):
    vip_status = VIPStatus.objects.first()
    today = timezone.now().date()
    matches = Match.objects.filter(
        updated=False, is_premium=True, date__date=today  # Filter by today's date
    ).prefetch_related("footballprediction_set")

    match_data = []
    for match in matches:

        match_data.append(
            {
                "match": match,
                "league_logo": match.league.logo if match.league else None,
                "country_name": match.league.country.name if match.league else None,
                "country_flag": match.league.country.flag if match.league else None,
            }
        )

    return render(
        request,
        "public/market.html",
        {"match_data": match_data, "VIPStatus": vip_status},
    )
