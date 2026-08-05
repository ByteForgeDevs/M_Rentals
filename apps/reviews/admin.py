from django.contrib import admin

from .models import LandlordReview, TenantReview, Tenancy


@admin.register(Tenancy)
class TenancyAdmin(admin.ModelAdmin):
    list_display = ["listing", "tenant", "landlord", "status", "started_on", "ended_on"]
    list_filter = ["status", "started_on"]
    search_fields = ["listing__title", "tenant__full_name", "landlord__full_name"]
    autocomplete_fields = ["listing", "tenant", "landlord"]


@admin.register(LandlordReview)
class LandlordReviewAdmin(admin.ModelAdmin):
    list_display = ["landlord", "author", "overall_rating", "created_at"]
    list_filter = ["overall_rating", "created_at"]
    search_fields = ["landlord__full_name", "author__full_name", "comment"]
    readonly_fields = ["overall_rating", "created_at"]


@admin.register(TenantReview)
class TenantReviewAdmin(admin.ModelAdmin):
    list_display = ["tenant", "author", "overall_rating", "created_at"]
    list_filter = ["overall_rating", "created_at"]
    search_fields = ["tenant__full_name", "author__full_name", "comment"]
    readonly_fields = ["overall_rating", "created_at"]
