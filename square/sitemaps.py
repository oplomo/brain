from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import (
    FootballPrediction,
    SiteInformation,
    BasketballPrediction,
    TennisPrediction,
    Match,
)


class StaticViewSitemap(Sitemap):
    priority = 0.8  # Importance of the pages (1.0 is highest)
    changefreq = "weekly"  # How often the page content updates

    def items(self):
        return [
            "square:privacy",
            "square:terms",
        ]

    def location(self, item):
        return reverse(item)


class FootballPredictionSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return FootballPrediction.objects.all()


class BasketballPredictionSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return BasketballPrediction.objects.all()


class TennisPredictionSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return TennisPrediction.objects.all()
