from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("tenancies/", views.tenancy_list, name="tenancies"),
    path("tenancies/record/<slug:slug>/", views.record_tenancy, name="record_tenancy"),
    path("tenancies/<int:pk>/end/", views.end_tenancy, name="end_tenancy"),
    path("tenancies/<int:pk>/review-landlord/", views.review_landlord, name="review_landlord"),
    path("tenancies/<int:pk>/review-tenant/", views.review_tenant, name="review_tenant"),
]
