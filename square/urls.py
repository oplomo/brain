from django.urls import path
from . import views


app_name = "square"

urlpatterns = [
    path("", views.index, name="index"),#home page that shows today football prediction by defaut,it can also show tennis and bascetball when filtered,it has table that dispys(msport type,hometeam vs away team,time,probabiities of prediction,prediction,odds and match result),  ,its has a menu with these urls(soccer_detail,tennis_detail,basketball_detail,office,privacy,premium,terms,contact_info),it aso aows you to search for yesterdays,todays and tommorows games,and filter by selected sport by clicing the lin of each ITS NAVIGATE IS -INDEX.HTMl
    path("free predictons/sport/<str:selected>", views.index, name="index"),
    path(
        "free predictions/sport/<str:selected>/<path:item>/", views.index, name="index"
    ),#home page still IT NAVUGATES TO INDEX.HTMl
    path(
        "free predictions/sports/<str:selected>/<path:item>/<str:day>predictions/",
        views.index,
        name="index",
    ),#home page lin that filters the sports and shows every content of the home page ony that the sports are filtered to the desired one -IT NAVIGATED TO INDEX.HTMl
    path(
        "free football predictons/football/<int:pk>/<str:home_team_slug>/vs/<str:away_team_slug>/<str:time>/<str:sport_slug>",
        views.footballview,
        name="soccer_detail",
    ),#this is for a football template that shows the detailed view of the selected football match and alv the predictions made about it,result,weather contion of where the match is payed -IT NAIGATES TO FOOTBAllVIEW.HTMl
    path(
        "free tennis predictons/tennis/<int:pk>/<str:home_team_slug>/vs/<str:away_team_slug>/<str:time>/<str:sport_slug>",
        views.Tennisview,
        name="tennis_detail",
    ),#this is for a tennis template that shows the detailed view of the selected football match and alv the predictions made about it,result,weather contion of where the match is payed -IT NAIGATES TO TENNISVIEW.HTMl

    path(
        "free basketball predictons/basketball/<int:pk>/<str:home_team_slug>/vs/<str:away_team_slug>/<str:time>/<str:sport_slug>",
        views.Basketballview,
        name="basketball_detail",
    ),#this is for a basketball template that shows the detailed view of the selected football match and alv the predictions made about it,result,weather contion of where the match is payed -IT NAIGATES TO basketballview.HTMl

    path("manage sport create prediction tips betting/", views.office, name="office"),#a lin in the index.html that taes you to o.html where it has several private lins that are used by admin and not the public such which have url with these names:(recreate_football_league,select_football_prediction,check_task_progress,predict_all_matches,premium,destroy_premium,recreate_premium,toggle_maintenance,logout)
    path("refresh static database/", views.refresh, name="refresh"),#a lin that taes the admin to  refresh.html where he can mae changes to the database such as fetech for leagues again and store them,it has onvy one url with the name (recreate_football_league)  !!this is for admin not to the pubic
    path(
        "recreate football league database/",
        views.recreate_football_league,
        name="recreate_football_league",
    ),#a lin in atempate called o.html that lets the admin fetch different legues, this is only acceced by admin not the public,if the process is succesfu it renders a succes page nown as success_recreate_football_league.html
    path("fetch-matches/", views.fetch_matches_view, name="fetch_matches"),
    path(
        "select_football_prediction/",
        views.select_football_prediction,
        name="select_football_prediction",
    ),#a lin in o.html that taes the admin to select_football_prediction.html and helps admin select from the database the match you want to predict, it has a filter that give admin the option of sevecting todays or tommorws,after sevection ,it redirects the admin to the same page,again this is not for the pubic
    path(
        "start_soccer_prediction/<str:today>",
        views.start_soccer_prediction,
        name="start_soccer_prediction",
    ),# a lin in o.html that taes the admin to start_soccer_prediction.html where this page dispayes the sected games for prediction and the admin clics a button to start the process of prediction, the process is show by a tempate that is simpe with no lins , it ony shows tas progress,, here is its url name "check_task_progress" by defaut it starts predictions of today games its name is data_progress.html
    path(
        "start_soccer_prediction/<str:date>/",
        views.start_soccer_prediction,
        name="start_soccer_prediction",
    ),# a lin in o.html that taes the admin to start_soccer_prediction.html where this page dispayes the sected games for prediction and the admin clics a button to start the process of prediction, the process is show by a tempate that is simpe with no lins , it ony shows tas progress,, here is its url name "check_task_progress" by defaut it starts predictions of seected date games its name is data_progress.html
    path(
        "private/check_task_progress/<uuid:task_id>/",
        views.check_task_progress,
        name="check_task_progress",
    ),# a lin in o.html tha admin uses to chec fro the preogress of prediction tas, interms of the number of aready progressed, succesfull and failed
    path("see_data_progress", views.see_data_progress, name="see_data_progress"),#same us the check_task_progress url
    path("predict_all/", views.predict_all_matches, name="predict_all_matches"),#a lin thatadmin cics when he wants to predict a matches, it is in o.html and not for the public
    path("jeruqsore/premium/", views.premium, name="premium"),# a lin in index.html that taes visitoes to premium.html where the vistitor can see the games in that tempate,and if a person hasnt payed it will render payment_page.html that has a form for putting payment detais such as emai
    path("destroy_premium/", views.destroy_premium, name="destroy_premium"),#. a lin in o.html that the admin cics when he want the premium games in the premium.html not to be treated as premium so that the can be rendered in index.html alongside other games,
    path("recreate_premium/", views.recreate_premium, name="recreate_premium"),#. a lin in o.html that the admin cics when he want the premium games in the index.html not to be treated as norma so that the can be rendered in premium.html ,
    path("payment/", views.payment_page, name="payment_page"),#a lin in premium.html that taes the visitor to payment_page.html where he can mae payment for the premium games
    path("payment/callback/", views.payment_callback, name="payment_callback"),# this is for paystac i dont now its wor yet becouse i am yet to integrate paystac, ignore it
    path("jerusqore/privacy/policy/", views.privacy, name="privacy"),#lin in index.htl in the footer that is to tae the visitor in privacy.hmtl where privacy terms are documented
    path("jerusqore/terms/condition/", views.terms, name="terms"),#lin in index.htl in the footer that is to tae the visitor in terms.hmtl where terms and coditions are documented
    path("fence/sct222-0190/2021/enter/", views.custom_login, name="fence"),#ignore this
    path("logout/", views.custom_logout, name="logout"),  # a lin in o.html that the admins cic when it wants to logout and browse as a regular visitor
    path("toggle-maintenance/", views.toggle_maintenance, name="toggle_maintenance"),# a lin in o.html that admin cics when he want to turn on maintainance mode, it redirects to the same oage i.e o.html

]
