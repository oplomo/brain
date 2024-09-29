from django.shortcuts import render
from .models import FootballPrediction, BasketballPrediction, TennisPrediction, Match


def index(request, selected=None, item=None):
    # Updated sports menu
    sports_menu = {
        "soccer": [
            "3 way(1X2)",
            "bts(GG)",
            "total(OVER/UNDER)",
            "cards & corners",
            "double chance(12,1X,X2)",
        ],
        "basketball": ["3 way", "total overtime"],
        "tennis": ["3 way", "total"],
    }

    # Set default sport if none is selected
    selected = selected or "soccer"
    menu = sports_menu.get(selected, [])

    # Determine the correct prediction model based on the selected sport
    if selected == "soccer":
        matches = FootballPrediction.objects.select_related("match").filter(
            match__sport__name=selected
        )
    elif selected == "basketball":
        matches = BasketballPrediction.objects.select_related("match").filter(
            match__sport__name=selected
        )
    elif selected == "tennis":
        matches = TennisPrediction.objects.select_related("match").filter(
            match__sport__name=selected
        )
    else:
        matches = Match.objects.none()  # Empty queryset for unknown sports

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
                        int(match.home_team_win_probability)
                        if match.home_team_win_probability
                        else "---"
                    ),
                    "draw_probability": (
                        int(match.draw_probability) if match.draw_probability else "---"
                    ),
                    "away_team_win_probability": (
                        int(match.away_team_win_probability)
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
                        int(match.gg_probability) if match.gg_probability else "---"
                    ),
                    "no_gg_probability": (
                        int(match.no_gg_probability)
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
                        int(match.over_2_5_probability)
                        if match.over_2_5_probability
                        else "---"
                    ),
                    "under_2_5_probability": (
                        int(match.under_2_5_probability)
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
                        int(match.over_1_5_probability)
                        if match.over_1_5_probability
                        else "---"
                    ),
                    "under_1_5_probability": (
                        int(match.under_1_5_probability)
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
                        int(match.over_3_5_probability)
                        if match.over_3_5_probability
                        else "---"
                    ),
                    "under_3_5_probability": (
                        int(match.under_3_5_probability)
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
                        int(match.over_4_5_probability)
                        if match.over_4_5_probability
                        else "---"
                    ),
                    "under_4_5_probability": (
                        int(match.under_4_5_probability)
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
                        int(match.over_5_5_probability)
                        if match.over_5_5_probability
                        else "---"
                    ),
                    "under_5_5_probability": (
                        int(match.under_5_5_probability)
                        if match.under_5_5_probability
                        else "---"
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
                    "home_team_win_probability": match.home_team_win_probability,
                    "draw_probability": match.draw_probability,
                    "away_team_win_probability": match.away_team_win_probability,
                },
            ],
        },
        "tennis": {
            "3 way": [
                ("Home Win Probability", "home_win_probability"),
                ("Away Win Probability", "away_win_probability"),
                lambda match: {
                    "home_win_probability": match.home_team_win_probability,
                    "away_win_probability": match.away_team_win_probability,
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
            "sport_type": match.match.sport.name,
            "match_name": match.match,
            "prediction": get_prediction(match, selected),
            "odds": get_odds(match, selected),
            "result": (
                match.gg_match_result
                if selected == "soccer" and item == "bts(GG)"
                else (
                    match.o_2_5_match_result
                    if selected == "soccer" and item == "total(OVER/UNDER)"
                    else (
                        match.o_1_5_match_result
                        if selected == "soccer" and item == "total_1_5(OVER/UNDER)"
                        else (
                            match.o_3_5_match_result
                            if selected == "soccer" and item == "total_3_5(OVER/UNDER)"
                            else (
                                match.o_4_5_match_result
                                if selected == "soccer"
                                and item == "total_4_5(OVER/UNDER)"
                                else (
                                    match.o_5_5_match_result
                                    if selected == "soccer"
                                    and item == "total_5_5(OVER/UNDER)"
                                    else match.three_way_match_result
                                    
                                )
                            )
                        )
                    )
                )
            ),
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
