from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.listings.models import Listing

RATING_VALIDATORS = [MinValueValidator(1), MaxValueValidator(5)]


class Tenancy(models.Model):
    """A confirmed rental relationship between a landlord and a tenant.

    Reviews are gated on this record: the landlord confirms who actually rented
    the unit, which is what stops the review system from being spammable.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        ENDED = "ended", _("Ended")

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="tenancies")
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenancies"
    )
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenancies_as_landlord"
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    started_on = models.DateField(default=timezone.localdate)
    ended_on = models.DateField(null=True, blank=True)
    confirmed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_on"]
        verbose_name_plural = _("tenancies")
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "tenant", "started_on"], name="unique_tenancy_per_start"
            )
        ]

    def __str__(self):
        return f"{self.tenant} @ {self.listing.title}"

    def clean(self):
        super().clean()
        if self.tenant_id and self.landlord_id and self.tenant_id == self.landlord_id:
            raise ValidationError(_("A landlord cannot record themselves as their own tenant."))
        if self.ended_on and self.ended_on < self.started_on:
            raise ValidationError({"ended_on": _("End date cannot be before the start date.")})

    def save(self, *args, **kwargs):
        if not self.landlord_id and self.listing_id:
            self.landlord = self.listing.landlord
        if self.ended_on and self.status == self.Status.ACTIVE:
            self.status = self.Status.ENDED
        super().save(*args, **kwargs)

    @property
    def has_landlord_review(self) -> bool:
        return hasattr(self, "landlord_review")

    @property
    def has_tenant_review(self) -> bool:
        return hasattr(self, "tenant_review")


class LandlordReview(models.Model):
    """A tenant rating their landlord — the trust signal renters care about."""

    tenancy = models.OneToOneField(
        Tenancy, on_delete=models.CASCADE, related_name="landlord_review"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="landlord_reviews_written"
    )
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_received"
    )
    responsiveness = models.PositiveSmallIntegerField(
        _("responsiveness to repairs and calls"), validators=RATING_VALIDATORS
    )
    deposit_fairness = models.PositiveSmallIntegerField(
        _("deposit returned fairly"), validators=RATING_VALIDATORS
    )
    listing_honesty = models.PositiveSmallIntegerField(
        _("the house matched the listing"), validators=RATING_VALIDATORS
    )
    overall_rating = models.PositiveSmallIntegerField(
        validators=RATING_VALIDATORS, editable=False, default=3
    )
    comment = models.TextField(max_length=1200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} → {self.landlord}: {self.overall_rating}/5"

    def save(self, *args, **kwargs):
        self.overall_rating = round(
            (self.responsiveness + self.deposit_fairness + self.listing_honesty) / 3
        )
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.tenancy_id and self.author_id and self.tenancy.tenant_id != self.author_id:
            raise ValidationError(_("Only the tenant on this tenancy can review the landlord."))


class TenantReview(models.Model):
    """A landlord rating a past tenant, for the next landlord to see."""

    tenancy = models.OneToOneField(
        Tenancy, on_delete=models.CASCADE, related_name="tenant_review"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenant_reviews_written"
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_reviews_received",
    )
    payment_reliability = models.PositiveSmallIntegerField(
        _("paid rent on time"), validators=RATING_VALIDATORS
    )
    property_care = models.PositiveSmallIntegerField(
        _("looked after the property"), validators=RATING_VALIDATORS
    )
    communication = models.PositiveSmallIntegerField(
        _("communication"), validators=RATING_VALIDATORS
    )
    overall_rating = models.PositiveSmallIntegerField(
        validators=RATING_VALIDATORS, editable=False, default=3
    )
    comment = models.TextField(max_length=1200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} → {self.tenant}: {self.overall_rating}/5"

    def save(self, *args, **kwargs):
        self.overall_rating = round(
            (self.payment_reliability + self.property_care + self.communication) / 3
        )
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.tenancy_id and self.author_id and self.tenancy.landlord_id != self.author_id:
            raise ValidationError(_("Only the landlord on this tenancy can review the tenant."))
