from django.urls import path

from . import views

app_name = "verification"

urlpatterns = [
    path("", views.status, name="status"),
    path("landlord/", views.landlord_verification, name="landlord"),
    path("tenant/", views.tenant_verification, name="tenant"),
]
