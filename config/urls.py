from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

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
elif settings.SERVE_MEDIA_FILES:
    # WhiteNoise only handles collected static files, so user uploads still need
    # a route. Listing photos are the whole product, which makes this worth the
    # modest cost of serving them through the app at MVP traffic levels.
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"),
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]
