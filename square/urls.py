from django.urls import path
from . import views


app_name = "square"

urlpatterns = [
    path("", views.index, name="index"),
    path("free predictons/sport/<str:selected>", views.index, name="index"),
    path(
        "free predictions/sport/<str:selected>/<path:item>/", views.index, name="index"
    ),
    path(
        "free predictions/sports/<str:selected>/<path:item>/<str:day>predictions/",
        views.index,
        name="index",
    ),
    path(
        "free football predictons/football/<int:pk>/<str:home_team_slug>/vs/<str:away_team_slug>/<str:time>/<str:sport_slug>",
        views.footballview,
        name="soccer_detail",
    ),
    path(
        "free tennis predictons/tennis/<int:pk>/<str:home_team_slug>/vs/<str:away_team_slug>/<str:time>/<str:sport_slug>",
        views.Tennisview,
        name="tennis_detail",
    ),
    path(
        "free basketball predictons/basketball/<int:pk>/<str:home_team_slug>/vs/<str:away_team_slug>/<str:time>/<str:sport_slug>",
        views.Basketballview,
        name="basketball_detail",
    ),
    path("manage sport create prediction tips betting/", views.office, name="office"),
    path("refresh static database/", views.refresh, name="refresh"),
    path(
        "recreate football league database/",
        views.recreate_football_league,
        name="recreate_football_league",
    ),
    path("fetch-matches/", views.fetch_matches_view, name="fetch_matches"),
    path(
        "select_football_prediction/",
        views.select_football_prediction,
        name="select_football_prediction",
    ),
    path(
        "start_soccer_prediction/<str:today>",
        views.start_soccer_prediction,
        name="start_soccer_prediction",
    ),
    path(
        "start_soccer_prediction/<str:date>/",
        views.start_soccer_prediction,
        name="start_soccer_prediction",
    ),
    path(
        "private/check_task_progress/<uuid:task_id>/",
        views.check_task_progress,
        name="check_task_progress",
    ),
    path("see_data_progress", views.see_data_progress, name="see_data_progress"),
    path("predict_all/", views.predict_all_matches, name="predict_all_matches"),
]
