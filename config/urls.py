from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Mrentals admin"
admin.site.site_title = "Mrentals admin"
admin.site.index_title = "Trust & verification desk"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.pages.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("houses/", include("apps.listings.urls")),
    path("verification/", include("apps.verification.urls")),
    path("reviews/", include("apps.reviews.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
