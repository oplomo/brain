from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.views.static import serve

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
    path(
        "see_data_progress", views.see_data_progress, name="see_data_progress"
    ),  # same us the check_task_progress url
    path(
        "predict_all/", views.predict_all_matches, name="predict_all_matches"
    ),  # a lin thatadmin cics when he wants to predict a matches, it is in o.html and not for the public
    path(
        "jeruqsore/premium/", views.premium, name="premium"
    ),  # a lin in index.html that taes visitoes to premium.html where the vistitor can see the games in that tempate,and if a person hasnt payed it will render payment_page.html that has a form for putting payment detais such as emai
    path(
        "destroy_premium/", views.destroy_premium, name="destroy_premium"
    ),  # . a lin in o.html that the admin cics when he want the premium games in the premium.html not to be treated as premium so that the can be rendered in index.html alongside other games,
    path(
        "recreate_premium/", views.recreate_premium, name="recreate_premium"
    ),  # . a lin in o.html that the admin cics when he want the premium games in the index.html not to be treated as norma so that the can be rendered in premium.html ,
    # this is for paystac i dont now its wor yet becouse i am yet to integrate paystac, ignore it
    path(
        "jerusqore/privacy/policy/", views.privacy, name="privacy"
    ),  # lin in index.htl in the footer that is to tae the visitor in privacy.hmtl where privacy terms are documented
    path(
        "jerusqore/terms/condition/", views.terms, name="terms"
    ),  # lin in index.htl in the footer that is to tae the visitor in terms.hmtl where terms and coditions are documented
    path(
        "fence/sct222-0190/2021/enter/", views.custom_login, name="fence"
    ),  # ignore this
    path(
        "logout/", views.custom_logout, name="logout"
    ),  # a lin in o.html that the admins cic when it wants to logout and browse as a regular visitor
    path(
        "toggle-maintenance/", views.toggle_maintenance, name="toggle_maintenance"
    ),  # a lin in o.html that admin cics when he want to turn on maintainance mode, it redirects to the same oage i.e o.html
    path("payment/", views.initiate_payment, name="initiate_payment"),
    path("payment/verify/", views.verify_payment, name="verify_payment"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/failed/", views.payment_failed, name="payment_failed"),
    path("send_game/", views.send_game, name="send_game"),
    path("toggle-vip/", views.toggle_vip, name="toggle_vip"),
    path("market/", views.market, name="market"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "yandex_b65d1afe014020d6.html",
        serve,
        {"document_root": ".", "path": "yandex_b65d1afe014020d6.html"},
    ),
]
