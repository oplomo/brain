from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse


class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow superuser to access the site
        if (
            getattr(settings, "MAINTENANCE_MODE", False)
            and not request.user.is_superuser
        ):
            return HttpResponse(
                "<h1>Site Under Maintenance</h1><p>We'll be back soon.</p>", status=503
            )

        return self.get_response(request)
