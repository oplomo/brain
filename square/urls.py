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
]
