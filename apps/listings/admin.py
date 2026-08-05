from django.contrib import admin

from .models import Listing, ListingPhoto, SavedListing


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 1
    fields = ["image", "category", "caption", "sort_order"]


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ["title", "area", "county", "rent_amount", "bedrooms", "status", "photo_set_ok", "landlord"]
    list_filter = ["status", "county", "property_type", "bedrooms"]
    search_fields = ["title", "area", "nearest_landmark", "landmark_description", "landlord__full_name"]
    autocomplete_fields = ["landlord"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ListingPhotoInline]
    readonly_fields = ["view_count", "published_at", "created_at", "updated_at"]
    list_select_related = ["landlord"]

    @admin.display(boolean=True, description="Photo set complete")
    def photo_set_ok(self, obj):
        return obj.has_complete_photo_set


admin.site.register(SavedListing)
