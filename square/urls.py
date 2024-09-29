from django.urls import path
from . import views


app_name = "square"

urlpatterns = [
    path("", views.index, name="index"),
    path("home/sport/<str:selected>", views.index, name="index"),
    path("home/sport/<str:selected>/<path:item>/", views.index, name="index"),
]
