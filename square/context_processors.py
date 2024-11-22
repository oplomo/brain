# myapp/context_processors.py

from .models import SiteInformation


def site_info_context(request):
    site_info = SiteInformation.objects.filter(pk=1)

    return {"site": site_info}
