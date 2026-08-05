from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.accounts.forms import StyledFormMixin
from apps.accounts.validators import normalize_phone

from .models import LandlordReview, TenantReview, Tenancy

User = get_user_model()

RATING_CHOICES = [
    (5, _("5: Excellent")),
    (4, _("4: Good")),
    (3, _("3: Okay")),
    (2, _("2: Poor")),
    (1, _("1: Terrible")),
]


class RecordTenancyForm(StyledFormMixin, forms.ModelForm):
    """A landlord confirms who actually rented the unit.

    Identifying the tenant by their registered email or phone is what ties the
    review back to a real person instead of an anonymous claim.
    """

    tenant_identifier = forms.CharField(
        label=_("Tenant's email or phone number"),
        help_text=_("They must already have an Mrentals account."),
        widget=forms.TextInput(attrs={"placeholder": "0712 345 678"}),
    )

    class Meta:
        model = Tenancy
        fields = ["started_on", "ended_on"]
        widgets = {
            "started_on": forms.DateInput(attrs={"type": "date"}),
            "ended_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, listing=None, landlord=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing
        self.landlord = landlord
        self.fields["ended_on"].required = False
        self.fields["ended_on"].help_text = _("Leave blank if they still live there.")

    def clean_tenant_identifier(self):
        raw = (self.cleaned_data.get("tenant_identifier") or "").strip()
        lookup = Q(email__iexact=raw)
        if phone := normalize_phone(raw):
            lookup |= Q(phone=phone)

        tenant = User.objects.filter(lookup).first()
        if tenant is None:
            raise ValidationError(
                _("No Mrentals account matches that email or phone number.")
            )
        if self.landlord and tenant.pk == self.landlord.pk:
            raise ValidationError(_("You cannot record yourself as your own tenant."))
        self.tenant = tenant
        return raw

    def clean(self):
        cleaned = super().clean()
        tenant = getattr(self, "tenant", None)
        started_on = cleaned.get("started_on")
        if tenant and self.listing and started_on:
            exists = Tenancy.objects.filter(
                listing=self.listing, tenant=tenant, started_on=started_on
            ).exclude(pk=self.instance.pk).exists()
            if exists:
                raise ValidationError(
                    _("This tenancy is already recorded for that start date.")
                )
        ended_on = cleaned.get("ended_on")
        if started_on and ended_on and ended_on < started_on:
            self.add_error("ended_on", _("End date cannot be before the start date."))
        return cleaned

    def save(self, commit=True):
        tenancy = super().save(commit=False)
        tenancy.listing = self.listing
        tenancy.landlord = self.landlord
        tenancy.tenant = self.tenant
        if commit:
            tenancy.save()
        return tenancy


class RatingFormMixin(StyledFormMixin):
    rating_fields: tuple[str, ...] = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.rating_fields:
            self.fields[name] = forms.TypedChoiceField(
                choices=RATING_CHOICES,
                coerce=int,
                label=self._meta.model._meta.get_field(name).verbose_name,
                widget=forms.RadioSelect,
            )
        self.order_fields([*self.rating_fields, "comment"])

    def clean_comment(self):
        comment = (self.cleaned_data.get("comment") or "").strip()
        if len(comment) < 20:
            raise ValidationError(
                _("Write at least a sentence. This is what other people rely on.")
            )
        return comment


class LandlordReviewForm(RatingFormMixin, forms.ModelForm):
    rating_fields = ("responsiveness", "deposit_fairness", "listing_honesty")

    class Meta:
        model = LandlordReview
        fields = ["responsiveness", "deposit_fairness", "listing_honesty", "comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": _(
                        "How was it renting from this landlord? Repairs, deposit, honesty."
                    ),
                }
            )
        }


class TenantReviewForm(RatingFormMixin, forms.ModelForm):
    rating_fields = ("payment_reliability", "property_care", "communication")

    class Meta:
        model = TenantReview
        fields = ["payment_reliability", "property_care", "communication", "comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": _("How was this tenant? Rent, care of the house, comms."),
                }
            )
        }
