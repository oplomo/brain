from .models import SiteInformation, VIPStatus


def site_info_context(request):
    site_info = SiteInformation.objects.first()  # Get the first object or None
    vip_status, created = VIPStatus.objects.get_or_create(id=1)
    return {"site_info": site_info, "vip_status": vip_status}
