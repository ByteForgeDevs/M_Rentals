from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import validate_file_size

KENYAN_COUNTIES = [
    "Nairobi",
    "Kiambu",
    "Machakos",
    "Kajiado",
    "Mombasa",
    "Kilifi",
    "Nakuru",
    "Uasin Gishu",
    "Kisumu",
    "Nyeri",
    "Meru",
    "Kakamega",
]


class PhotoCategory(models.TextChoices):
    """The structured photo set that replaces unreliable map pins."""

    EXTERIOR = "exterior", _("Building exterior")
    ENTRANCE = "entrance", _("Gate / entrance")
    ROOM = "room", _("Room interior")
    METER = "meter", _("Water / electricity meter")
    LANDMARK = "landmark", _("Nearest landmark")
    OTHER = "other", _("Other")


class ListingQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Listing.Status.PUBLISHED)

    def visible_to(self, user):
        """Published listings, plus the user's own drafts and pending listings."""
        if user is None or not user.is_authenticated:
            return self.published()
        if user.is_staff:
            return self
        return self.filter(models.Q(status=Listing.Status.PUBLISHED) | models.Q(landlord=user))

    def from_verified_landlords(self):
        return self.filter(landlord__landlord_verification__status="approved")

    def with_landlord_rating(self):
        return self.annotate(
            landlord_rating=Avg("landlord__reviews_received__overall_rating"),
            landlord_review_count=Count("landlord__reviews_received", distinct=True),
        )

    def with_cover(self):
        return self.prefetch_related("photos").select_related("landlord")


class Listing(models.Model):
    """A long-term residential rental unit.

    Location is landmark-first: formal map data is unreliable for new estates,
    so the listing carries written directions plus a mandatory photo set, with
    optional GPS coordinates as a bonus rather than the source of truth.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PENDING = "pending", _("Pending review")
        PUBLISHED = "published", _("Published")
        RENTED = "rented", _("Rented out")
        ARCHIVED = "archived", _("Archived")

    class PropertyType(models.TextChoices):
        BEDSITTER = "bedsitter", _("Bedsitter")
        SINGLE = "single", _("Single room")
        APARTMENT = "apartment", _("Apartment")
        MAISONETTE = "maisonette", _("Maisonette")
        BUNGALOW = "bungalow", _("Bungalow")
        SHARED = "shared", _("Shared house")

    class WaterSupply(models.TextChoices):
        BOREHOLE = "borehole", _("Borehole")
        COUNCIL = "council", _("County water")
        TANK = "tank", _("Tank / delivered")
        BOTH = "both", _("Borehole + county")

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings"
    )
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(max_length=2000)
    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, default=PropertyType.APARTMENT
    )
    bedrooms = models.PositiveSmallIntegerField(
        default=1, validators=[MaxValueValidator(10)], help_text=_("Use 0 for a bedsitter.")
    )
    bathrooms = models.PositiveSmallIntegerField(default=1, validators=[MaxValueValidator(10)])
    rent_amount = models.DecimalField(
        _("monthly rent (KES)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1000"))],
    )
    deposit_amount = models.DecimalField(
        _("deposit (KES)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )

    # --- Landmark-first location -------------------------------------------
    county = models.CharField(max_length=60, choices=[(c, c) for c in KENYAN_COUNTIES])
    area = models.CharField(
        _("estate / area"), max_length=120, help_text=_("e.g. Ruaka, Membley, Nyali")
    )
    landmark_description = models.TextField(
        _("how to find it"),
        max_length=600,
        help_text=_(
            "Directions the way people actually navigate, e.g. \"200m from Quickmart "
            "Ruaka, blue gate, third building past the mosque\"."
        ),
    )
    nearest_landmark = models.CharField(
        _("nearest well-known landmark"),
        max_length=140,
        help_text=_("e.g. Quickmart Ruaka, Ruaka Stage, Membley Police Post"),
    )
    walking_minutes_to_landmark = models.PositiveSmallIntegerField(
        _("walking minutes from that landmark"),
        default=5,
        validators=[MaxValueValidator(120)],
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("-5")), MaxValueValidator(Decimal("5.5"))],
        help_text=_("Optional. Landmarks come first; a pin is a bonus."),
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("33.5")), MaxValueValidator(Decimal("42"))],
    )

    walkthrough_video_url = models.URLField(
        _("walkthrough video link"),
        blank=True,
        help_text=_("Optional YouTube/Drive link to a full walk-through of the unit."),
    )

    # --- Amenities ----------------------------------------------------------
    water_supply = models.CharField(
        max_length=20, choices=WaterSupply.choices, default=WaterSupply.COUNCIL
    )
    has_water_included = models.BooleanField(_("water included in rent"), default=False)
    has_parking = models.BooleanField(_("parking"), default=False)
    has_security = models.BooleanField(_("gated / security"), default=False)
    has_borehole_backup = models.BooleanField(_("water backup"), default=False)
    is_furnished = models.BooleanField(_("furnished"), default=False)
    allows_pets = models.BooleanField(_("pets allowed"), default=False)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    available_from = models.DateField(default=timezone.localdate)
    view_count = models.PositiveIntegerField(default=0, editable=False)
    published_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ListingQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["county", "area"]),
            models.Index(fields=["rent_amount"]),
            models.Index(fields=["bedrooms"]),
        ]

    def __str__(self):
        return f"{self.title} — {self.area}, {self.county}"

    def get_absolute_url(self):
        return reverse("listings:detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._build_unique_slug()
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def _build_unique_slug(self) -> str:
        base = slugify(f"{self.title}-{self.area}")[:150] or "listing"
        slug, counter = base, 2
        while Listing.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base[:150 - len(str(counter)) - 1]}-{counter}"
            counter += 1
        return slug

    def clean(self):
        super().clean()
        if (self.latitude is None) != (self.longitude is None):
            raise ValidationError(
                {"longitude": _("Provide both latitude and longitude, or neither.")}
            )
        if self.deposit_amount is not None and self.rent_amount:
            if self.deposit_amount > self.rent_amount * 3:
                raise ValidationError(
                    {"deposit_amount": _("Deposit cannot exceed three months' rent.")}
                )

    # --- Photo-set completeness --------------------------------------------
    @property
    def required_photo_categories(self) -> list[str]:
        return list(settings.LISTING_REQUIRED_PHOTO_CATEGORIES)

    def present_photo_categories(self) -> set[str]:
        return set(self.photos.values_list("category", flat=True))

    def missing_photo_categories(self) -> list[str]:
        present = self.present_photo_categories()
        return [c for c in self.required_photo_categories if c not in present]

    def missing_photo_labels(self) -> list[str]:
        labels = dict(PhotoCategory.choices)
        return [str(labels[c]) for c in self.missing_photo_categories()]

    @property
    def has_complete_photo_set(self) -> bool:
        return not self.missing_photo_categories()

    @property
    def can_publish(self) -> bool:
        return self.has_complete_photo_set and self.landlord.is_verified_landlord

    def publication_blockers(self) -> list[str]:
        blockers = []
        if not self.landlord.is_verified_landlord:
            blockers.append(str(_("Your landlord identity is not verified yet.")))
        missing = self.missing_photo_labels()
        if missing:
            blockers.append(
                str(_("Missing required photos: %(items)s.")) % {"items": ", ".join(missing)}
            )
        return blockers

    @property
    def cover_photo(self):
        photos = list(self.photos.all())
        if not photos:
            return None
        for category in (PhotoCategory.EXTERIOR, PhotoCategory.ROOM):
            for photo in photos:
                if photo.category == category:
                    return photo
        return photos[0]

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED

    @property
    def is_landlord_verified(self) -> bool:
        return self.landlord.is_verified_landlord

    @property
    def location_summary(self) -> str:
        return f"{self.area}, {self.county}"

    @property
    def bedrooms_label(self) -> str:
        if self.bedrooms == 0:
            return str(_("Bedsitter"))
        return f"{self.bedrooms} " + str(_("bedroom") if self.bedrooms == 1 else _("bedrooms"))


def listing_photo_path(instance, filename: str) -> str:
    return f"listings/{instance.listing_id}/{instance.category}/{filename}"


class ListingPhoto(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(
        upload_to=listing_photo_path,
        validators=[validate_file_size(settings.LISTING_IMAGE_MAX_BYTES)],
    )
    category = models.CharField(
        max_length=20, choices=PhotoCategory.choices, default=PhotoCategory.ROOM
    )
    caption = models.CharField(max_length=160, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "uploaded_at"]

    def __str__(self):
        return f"{self.get_category_display()} — {self.listing.title}"


class SavedListing(models.Model):
    """A tenant's shortlist entry."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_listings"
    )
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "listing"], name="unique_saved_listing")
        ]

    def __str__(self):
        return f"{self.user} saved {self.listing}"
