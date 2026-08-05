from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.forms import StyledFormMixin

from .models import LandlordVerification, TenantVerification


class LandlordVerificationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = LandlordVerification
        fields = [
            "national_id_number",
            "national_id_front",
            "national_id_back",
            "selfie",
            "ownership_proof_type",
            "ownership_document",
            "property_address",
            "video_call_slot",
        ]
        widgets = {
            "national_id_number": forms.TextInput(attrs={"placeholder": "12345678"}),
            "property_address": forms.TextInput(
                attrs={"placeholder": _("e.g. Sunrise Court, Ruaka, Kiambu")}
            ),
            "video_call_slot": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned = super().clean()
        proof_type = cleaned.get("ownership_proof_type")
        document = cleaned.get("ownership_document")
        slot = cleaned.get("video_call_slot")

        if proof_type == LandlordVerification.OwnershipProofType.VIDEO_CALL:
            if not slot:
                self.add_error(
                    "video_call_slot",
                    _("Pick a time for the verification call."),
                )
        elif not document and not self.instance.ownership_document:
            self.add_error(
                "ownership_document",
                _("Upload the document, or choose video call verification instead."),
            )
        return cleaned


class TenantVerificationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TenantVerification
        fields = [
            "national_id_number",
            "national_id_front",
            "national_id_back",
            "selfie",
            "employer_name",
            "income_document",
        ]
        widgets = {
            "national_id_number": forms.TextInput(attrs={"placeholder": "12345678"}),
            "employer_name": forms.TextInput(attrs={"placeholder": _("Optional")}),
        }
