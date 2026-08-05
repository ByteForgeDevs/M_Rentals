from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import validate_file_size


class VerificationStatus(models.TextChoices):
    UNSUBMITTED = "unsubmitted", _("Not submitted")
    PENDING = "pending", _("Pending review")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")


class BaseVerification(models.Model):
    """Shared review workflow for both sides of the marketplace.

    Review is deliberately manual for the MVP: a human looks at the documents in
    the Django admin and approves or rejects with a reason.
    """

    status = models.CharField(
        max_length=16, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )
    national_id_number = models.CharField(_("national ID number"), max_length=20)
    national_id_front = models.ImageField(
        _("national ID (front)"),
        upload_to="verification/id/",
        validators=[validate_file_size(settings.VERIFICATION_DOC_MAX_BYTES)],
    )
    national_id_back = models.ImageField(
        _("national ID (back)"),
        upload_to="verification/id/",
        blank=True,
        null=True,
        validators=[validate_file_size(settings.VERIFICATION_DOC_MAX_BYTES)],
    )
    selfie = models.ImageField(
        _("selfie holding your ID"),
        upload_to="verification/selfie/",
        blank=True,
        null=True,
        validators=[validate_file_size(settings.VERIFICATION_DOC_MAX_BYTES)],
    )
    reviewer_notes = models.TextField(blank=True, max_length=800)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-submitted_at"]

    @property
    def is_approved(self) -> bool:
        return self.status == VerificationStatus.APPROVED

    @property
    def is_pending(self) -> bool:
        return self.status == VerificationStatus.PENDING

    @property
    def is_rejected(self) -> bool:
        return self.status == VerificationStatus.REJECTED

    def approve(self, reviewer=None, notes: str = ""):
        self.status = VerificationStatus.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if notes:
            self.reviewer_notes = notes
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "reviewer_notes", "updated_at"])

    def reject(self, reviewer=None, notes: str = ""):
        self.status = VerificationStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if notes:
            self.reviewer_notes = notes
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "reviewer_notes", "updated_at"])


class LandlordVerification(BaseVerification):
    """Landlord/agent proof of identity plus proof they control the property."""

    class OwnershipProofType(models.TextChoices):
        TITLE_DEED = "title_deed", _("Title deed")
        SALE_AGREEMENT = "sale_agreement", _("Sale agreement")
        MANAGEMENT_LETTER = "management_letter", _("Property management letter")
        AGENCY_LICENCE = "agency_licence", _("Agency licence")
        VIDEO_CALL = "video_call", _("Video call verification")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="landlord_verification",
    )
    ownership_proof_type = models.CharField(
        _("proof of control"), max_length=24, choices=OwnershipProofType.choices
    )
    ownership_document = models.FileField(
        _("supporting document"),
        upload_to="verification/ownership/",
        blank=True,
        null=True,
        validators=[validate_file_size(settings.VERIFICATION_DOC_MAX_BYTES)],
        help_text=_("Not required if you chose video call verification."),
    )
    property_address = models.CharField(
        max_length=200, help_text=_("The building or estate the document refers to.")
    )
    video_call_slot = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Preferred time for the verification call, if applicable."),
    )

    class Meta(BaseVerification.Meta):
        verbose_name = _("landlord verification")
        verbose_name_plural = _("landlord verifications")

    def __str__(self):
        return f"Landlord verification for {self.user} ({self.get_status_display()})"


class TenantVerification(BaseVerification):
    """Optional tenant-side verification that unlocks landlord trust."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_verification",
    )
    employer_name = models.CharField(max_length=140, blank=True)
    income_document = models.FileField(
        _("payslip or M-Pesa statement"),
        upload_to="verification/income/",
        blank=True,
        null=True,
        validators=[validate_file_size(settings.VERIFICATION_DOC_MAX_BYTES)],
        help_text=_("Optional. Some landlords ask for proof of income."),
    )

    class Meta(BaseVerification.Meta):
        verbose_name = _("tenant verification")
        verbose_name_plural = _("tenant verifications")

    def __str__(self):
        return f"Tenant verification for {self.user} ({self.get_status_display()})"
