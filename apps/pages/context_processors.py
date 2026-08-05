from django.conf import settings


def site_context(request):
    return {
        "SITE_NAME": "Mrentals",
        "SITE_TAGLINE": "Verified landlord. Verified location.",
        "DEBUG": settings.DEBUG,
    }
