from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import LandlordVerification, TenantVerification


class BaseVerificationAdmin(admin.ModelAdmin):
    """The manual review desk described in the MVP scope."""

    list_display = ["user", "status", "national_id_number", "submitted_at", "reviewed_by"]
    list_filter = ["status", "submitted_at"]
    search_fields = ["user__full_name", "user__email", "user__phone", "national_id_number"]
    autocomplete_fields = ["user"]
    readonly_fields = ["submitted_at", "updated_at", "reviewed_at", "reviewed_by", "id_preview"]
    actions = ["approve_selected", "reject_selected"]
    list_select_related = ["user", "reviewed_by"]

    @admin.display(description=_("ID document"))
    def id_preview(self, obj):
        if not obj.national_id_front:
            return "None"
        return format_html(
            '<a href="{0}" target="_blank" rel="noopener">'
            '<img src="{0}" style="max-height:220px;border-radius:8px" /></a>',
            obj.national_id_front.url,
        )

    @admin.action(description=_("Approve selected verifications"))
    def approve_selected(self, request, queryset):
        count = 0
        for verification in queryset:
            verification.approve(reviewer=request.user)
            count += 1
        self.message_user(request, f"Approved {count} verification(s).", messages.SUCCESS)

    @admin.action(description=_("Reject selected verifications"))
    def reject_selected(self, request, queryset):
        count = 0
        for verification in queryset:
            verification.reject(
                reviewer=request.user,
                notes=verification.reviewer_notes or "Documents did not meet requirements.",
            )
            count += 1
        self.message_user(request, f"Rejected {count} verification(s).", messages.WARNING)


@admin.register(LandlordVerification)
class LandlordVerificationAdmin(BaseVerificationAdmin):
    list_display = BaseVerificationAdmin.list_display + ["ownership_proof_type"]
    list_filter = BaseVerificationAdmin.list_filter + ["ownership_proof_type"]
    fieldsets = (
        (None, {"fields": ("user", "status", "reviewer_notes")}),
        (_("Identity"), {"fields": ("national_id_number", "national_id_front", "national_id_back", "selfie", "id_preview")}),
        (_("Proof of control"), {"fields": ("ownership_proof_type", "ownership_document", "property_address", "video_call_slot")}),
        (_("Review trail"), {"fields": ("reviewed_by", "reviewed_at", "submitted_at", "updated_at")}),
    )


@admin.register(TenantVerification)
class TenantVerificationAdmin(BaseVerificationAdmin):
    fieldsets = (
        (None, {"fields": ("user", "status", "reviewer_notes")}),
        (_("Identity"), {"fields": ("national_id_number", "national_id_front", "national_id_back", "selfie", "id_preview")}),
        (_("Income"), {"fields": ("employer_name", "income_document")}),
        (_("Review trail"), {"fields": ("reviewed_by", "reviewed_at", "submitted_at", "updated_at")}),
    )
