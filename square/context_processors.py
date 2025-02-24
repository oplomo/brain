from .models import SiteInformation


def site_info_context(request):
    site_info = SiteInformation.objects.first()  # Get the first object or None
    return {"site_info": site_info}
