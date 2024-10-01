from django.shortcuts import render, get_object_or_404
from .models import FootballPrediction, BasketballPrediction, TennisPrediction, Match
import math
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify


def index(request, selected=None, item=None, day="today"):
    # Updated sports menu
    sports_menu = {
        "soccer": [
            "3 way(1X2)",
            "bts(GG)",
            "total(OVER/UNDER)",
            "cards",
            "corners",
            "double chance(12,1X,X2)",
        ],
        "basketball": ["3 way", "total overtime", "total halftime"],
        "tennis": ["3 way", "total"],
    }

    # Set default sport if none is selected
    selected = selected or "soccer"
    menu = sports_menu.get(selected, [])

    # Get today's date and define start and end boundaries
    today = timezone.now().date()

    if day == "yesterday":
        start_date = today - timedelta(days=1)
        end_date = today
    elif day == "today":
        start_date = today
        end_date = today + timedelta(days=1)
    elif day == "tomorrow":
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=2)
    else:
        # If day is something else, default to today
        start_date = today
        end_date = today + timedelta(days=1)

    # Determine the correct prediction model based on the selected sport
    if selected == "soccer":
        matches = FootballPrediction.objects.select_related("match").filter(
            match__sport__name=selected, match__match_date__range=[start_date, end_date]
        )
    elif selected == "basketball":
        matches = BasketballPrediction.objects.select_related("match").filter(
            match__sport__name=selected, match__match_date__range=[start_date, end_date]
        )
    elif selected == "tennis":
        matches = TennisPrediction.objects.select_related("match").filter(
            match__sport__name=selected, match__match_date__range=[start_date, end_date]
        )
    else:
        matches = Match.objects.none()  # Empty queryset for unknown sports

    # Initialize table headers and data
    table_headers = [
        "Sport Type",
        "time",
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
            "time",
            "Match Name",
        ]
        + options[:-1]  # Exclude the lambda (the last element)
        + [
            "Prediction",
            "Odds",
            "Result",
        ]
    )
    dynamic_headers = table_headers[3:-3]

    # Populate table data
    for match in matches:
        data = {
            "pk": match.match.pk,
            "home_team": match.match.home_team,
            "away_team": match.match.away_team,
            "sport_type": match.match.sport.name,
            "time": (match.match.match_date).strftime("%Y-%m-%d-%H:%M"),
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
            "time",
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
        },
    )


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
            "result": match.gg_match_result,
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
            "result": match.o_2_5_match_result,
        },
        "total corners": {
            "prediction": get_prediction_corners(match),
            "probability": (match.total_corners_probability),
            "odds": get_odds_corners(match),
            "result": match.total_corner_result,
        },
        "total cards": {
            "prediction": get_prediction_cards(match),
            "probability": (match.total_cards_probability),
            "odds": get_odds_cards(match),
            "result": match.total_card_result,
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
            "result": match.dc_result,
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
    }

    return render(request, "public/footballview.html", context)


def Tennisview(request, pk, home_team_slug, away_team_slug, time, sport_slug):
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
    }

    return render(request, "public/tennisview.html", context)


def Basketballview(request, pk, home_team_slug, away_team_slug, time, sport_slug):
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
    }

    return render(request, "public/basketballview.html", context)
