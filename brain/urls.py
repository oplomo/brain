

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from square.views import serve_media


from django.contrib import sitemaps
from django.contrib.sitemaps.views import sitemap


from square.sitemaps import (
    StaticViewSitemap,
    FootballPredictionSitemap,
    BasketballPredictionSitemap,
    TennisPredictionSitemap,
)

sitemaps = {
    "static": StaticViewSitemap(),
    "football_predictions": FootballPredictionSitemap(),
    "basketball_predictions": BasketballPredictionSitemap(),
    "tennis_predictions": TennisPredictionSitemap(),
}


urlpatterns = [
    path("", include("square.urls", namespace="square")),
    path("admin/", admin.site.urls),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve_media),
    ]
