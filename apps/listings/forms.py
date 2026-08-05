from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from apps.accounts.forms import StyledFormMixin

from .models import KENYAN_COUNTIES, Listing, ListingPhoto, PhotoCategory


class ListingForm(StyledFormMixin, forms.ModelForm):
    """Listing details. Landmark directions are mandatory, GPS is optional."""

    class Meta:
        model = Listing
        fields = [
            "title",
            "property_type",
            "description",
            "bedrooms",
            "bathrooms",
            "rent_amount",
            "deposit_amount",
            "county",
            "area",
            "nearest_landmark",
            "walking_minutes_to_landmark",
            "landmark_description",
            "latitude",
            "longitude",
            "walkthrough_video_url",
            "water_supply",
            "has_water_included",
            "has_parking",
            "has_security",
            "has_borehole_backup",
            "is_furnished",
            "allows_pets",
            "available_from",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": _("e.g. Spacious 2 bedroom in Ruaka, own compound")}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": _("What is the house like? Be honest — reviews check this."),
                }
            ),
            "area": forms.TextInput(attrs={"placeholder": _("e.g. Ruaka")}),
            "nearest_landmark": forms.TextInput(
                attrs={"placeholder": _("e.g. Quickmart Ruaka")}
            ),
            "landmark_description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": _(
                        "200m from Quickmart Ruaka, take the murram road opposite the "
                        "petrol station, blue gate, third building past the mosque."
                    ),
                }
            ),
            "available_from": forms.DateInput(attrs={"type": "date"}),
            "walkthrough_video_url": forms.URLInput(
                attrs={"placeholder": "https://youtube.com/..."}
            ),
            "rent_amount": forms.NumberInput(attrs={"step": "500", "placeholder": "25000"}),
            "deposit_amount": forms.NumberInput(attrs={"step": "500", "placeholder": "25000"}),
            "latitude": forms.NumberInput(attrs={"step": "0.000001", "placeholder": "-1.2050"}),
            "longitude": forms.NumberInput(attrs={"step": "0.000001", "placeholder": "36.7650"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["county"].choices = [("", _("Select a county"))] + [
            (c, c) for c in KENYAN_COUNTIES
        ]
        self.fields["deposit_amount"].required = False

    def clean_landmark_description(self):
        value = (self.cleaned_data.get("landmark_description") or "").strip()
        if len(value) < 30:
            raise ValidationError(
                _(
                    "Give real directions — at least a sentence. This is what replaces the "
                    "map pin for new buildings."
                )
            )
        return value


class ListingPhotoForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ListingPhoto
        fields = ["image", "category", "caption"]
        widgets = {"caption": forms.TextInput(attrs={"placeholder": _("Optional caption")})}


class BaseListingPhotoFormSet(forms.BaseInlineFormSet):
    """Enforce the structured photo set that replaces unreliable map pins."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        categories, total = set(), 0
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue
            if form.cleaned_data.get("image"):
                categories.add(form.cleaned_data.get("category"))
                total += 1

        # Photos already saved on the listing count towards the requirement.
        if self.instance and self.instance.pk:
            existing = self.instance.photos.exclude(
                pk__in=[f.instance.pk for f in self.forms if f.instance.pk and f.cleaned_data.get("DELETE")]
            )
            categories |= set(existing.values_list("category", flat=True))
            total += existing.count()

        if total > settings.LISTING_MAX_PHOTOS:
            raise ValidationError(
                _("Upload at most %(max)s photos.") % {"max": settings.LISTING_MAX_PHOTOS}
            )

        labels = dict(PhotoCategory.choices)
        missing = [
            str(labels[c])
            for c in settings.LISTING_REQUIRED_PHOTO_CATEGORIES
            if c not in categories
        ]
        if missing:
            raise ValidationError(
                _("Still missing required photos: %(items)s.") % {"items": ", ".join(missing)}
            )


ListingPhotoFormSet = inlineformset_factory(
    Listing,
    ListingPhoto,
    form=ListingPhotoForm,
    formset=BaseListingPhotoFormSet,
    extra=5,
    max_num=settings.LISTING_MAX_PHOTOS,
    can_delete=True,
)


SORT_CHOICES = [
    ("recent", _("Newest first")),
    ("price_asc", _("Price: low to high")),
    ("price_desc", _("Price: high to low")),
    ("rating", _("Best-rated landlords")),
]


class ListingSearchForm(forms.Form):
    """Filters for the search page. Every field is optional."""

    q = forms.CharField(
        required=False,
        label=_("Search"),
        widget=forms.TextInput(
            attrs={"placeholder": _("Area, landmark or keyword"), "autocomplete": "off"}
        ),
    )
    county = forms.ChoiceField(required=False, label=_("County"))
    min_price = forms.IntegerField(
        required=False, min_value=0, widget=forms.NumberInput(attrs={"placeholder": "5,000"})
    )
    max_price = forms.IntegerField(
        required=False, min_value=0, widget=forms.NumberInput(attrs={"placeholder": "50,000"})
    )
    bedrooms = forms.ChoiceField(
        required=False,
        choices=[("", _("Any")), ("0", _("Bedsitter")), ("1", "1"), ("2", "2"), ("3", "3+")],
    )
    property_type = forms.ChoiceField(required=False)
    verified_only = forms.BooleanField(
        required=False, label=_("Verified landlords only"), initial=False
    )
    has_video = forms.BooleanField(required=False, label=_("Has walkthrough video"))
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES, initial="recent")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["county"].choices = [("", _("All counties"))] + [
            (c, c) for c in KENYAN_COUNTIES
        ]
        self.fields["property_type"].choices = [("", _("Any type"))] + list(
            Listing.PropertyType.choices
        )
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault(
                    "class", "h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand"
                )
            else:
                widget.attrs.setdefault(
                    "class",
                    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm "
                    "text-slate-900 focus:border-brand focus:outline-none focus:ring-2 "
                    "focus:ring-brand/30",
                )

    def clean(self):
        cleaned = super().clean()
        min_price, max_price = cleaned.get("min_price"), cleaned.get("max_price")
        if min_price and max_price and min_price > max_price:
            raise ValidationError(_("Minimum price cannot be higher than the maximum price."))
        return cleaned
