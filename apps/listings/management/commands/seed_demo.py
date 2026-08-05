"""Populate the database with believable Kenyan demo data.

Everything here exists so a reviewer can open the site and immediately see the
trust loop working end to end: verified landlords, complete photo sets,
recorded tenancies and the two-way reviews they unlock.
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from apps.listings.models import Listing, ListingPhoto, PhotoCategory, SavedListing
from apps.reviews.models import LandlordReview, Tenancy, TenantReview
from apps.verification.models import (
    LandlordVerification,
    TenantVerification,
    VerificationStatus,
)

User = get_user_model()

PASSWORD = "mrentals2024"

LANDLORDS = [
    ("Achieng Otieno", "achieng@example.com", "+254712000001", True),
    ("Peter Kamau", "peter@example.com", "+254712000002", True),
    ("Fatuma Hassan", "fatuma@example.com", "+254712000003", True),
    ("Brian Kiptoo", "brian@example.com", "+254712000004", False),
]

TENANTS = [
    ("Wanjiru Njoroge", "wanjiru@example.com", "+254722000001", True),
    ("Dennis Omollo", "dennis@example.com", "+254722000002", True),
    ("Grace Mutindi", "grace@example.com", "+254722000003", False),
    ("Samuel Barasa", "samuel@example.com", "+254722000004", False),
]

LISTINGS = [
    {
        "title": "Bright 2 bedroom in Ruaka, water backup",
        "county": "Kiambu",
        "area": "Ruaka",
        "nearest_landmark": "Quickmart Ruaka",
        "walking_minutes_to_landmark": 4,
        "landmark_description": (
            "From Quickmart Ruaka, walk towards Banana on the left side of the road. "
            "Pass the mosque, take the second murram lane on your left. Blue gate, "
            "third building, the one with the green water tanks on the roof."
        ),
        "bedrooms": 2,
        "bathrooms": 1,
        "rent": 32000,
        "property_type": Listing.PropertyType.APARTMENT,
        "water_supply": Listing.WaterSupply.BOTH,
        "description": (
            "Third floor, faces east so you get morning sun in the sitting room. "
            "Borehole plus county water, so taps do not run dry. Tokens meter is "
            "yours alone, and the photo of the meter is in the gallery. Rent is "
            "exclusive of water and electricity. One month deposit."
        ),
        "amenities": ["has_parking", "has_security", "has_borehole_backup"],
    },
    {
        "title": "Bedsitter near Membley Police Post",
        "county": "Kiambu",
        "area": "Membley",
        "nearest_landmark": "Membley Police Post",
        "walking_minutes_to_landmark": 7,
        "landmark_description": (
            "Alight at Membley Police Post. Walk down the tarmac towards the estate "
            "gate, turn right at the shop painted Safaricom green. It is the cream "
            "storey building with black grills, opposite the borehole."
        ),
        "bedrooms": 0,
        "bathrooms": 1,
        "rent": 12500,
        "property_type": Listing.PropertyType.APARTMENT,
        "water_supply": Listing.WaterSupply.BOREHOLE,
        "description": (
            "Self-contained bedsitter with its own shower and toilet. Water is "
            "included in the rent because the compound is on borehole. Caretaker "
            "lives on site. Good for one person working in town, since the stage is a "
            "seven minute walk."
        ),
        "amenities": ["has_water_included", "has_security"],
    },
    {
        "title": "3 bedroom maisonette, gated court in Nyali",
        "county": "Mombasa",
        "area": "Nyali",
        "nearest_landmark": "Nyali Cinemax",
        "walking_minutes_to_landmark": 12,
        "landmark_description": (
            "From Nyali Cinemax head towards Links Road. After the second roundabout "
            "take the lane next to the pharmacy. The court has a white wall and a "
            "manned gate. Ask for Palm Court, house number 6."
        ),
        "bedrooms": 3,
        "bathrooms": 2,
        "rent": 78000,
        "property_type": Listing.PropertyType.MAISONETTE,
        "water_supply": Listing.WaterSupply.TANK,
        "description": (
            "Corner unit in a nine-house gated court. All bedrooms en-suite except "
            "the guest room. There is a 5,000 litre tank plus county supply. Parking "
            "for two cars inside the compound. Two months deposit, negotiable for a "
            "one year lease."
        ),
        "amenities": ["has_parking", "has_security", "is_furnished", "allows_pets"],
    },
    {
        "title": "1 bedroom in Kilimani, walk to Yaya",
        "county": "Nairobi",
        "area": "Kilimani",
        "nearest_landmark": "Yaya Centre",
        "walking_minutes_to_landmark": 9,
        "landmark_description": (
            "From Yaya Centre walk down Argwings Kodhek towards Kileleshwa. Turn into "
            "the third road on your right after the fuel station. The building is the "
            "grey one with balconies, next to the small church."
        ),
        "bedrooms": 1,
        "bathrooms": 1,
        "rent": 45000,
        "property_type": Listing.PropertyType.APARTMENT,
        "water_supply": Listing.WaterSupply.COUNCIL,
        "description": (
            "Open plan sitting and kitchen, balcony facing the back so it is quiet. "
            "Lift in the building, backup generator for the common areas. Service "
            "charge of KES 3,000 covers garbage, security and the lift."
        ),
        "amenities": ["has_parking", "has_security"],
    },
    {
        "title": "Spacious 2 bedroom in Kisumu, Milimani",
        "county": "Kisumu",
        "area": "Milimani",
        "nearest_landmark": "Kisumu Girls High School",
        "walking_minutes_to_landmark": 6,
        "landmark_description": (
            "Coming from Kisumu Girls, take the road heading to the Nyanza Club. It "
            "is the second gate after the big flame tree, house with the red roof "
            "and a hedge."
        ),
        "bedrooms": 2,
        "bathrooms": 2,
        "rent": 28000,
        "property_type": Listing.PropertyType.BUNGALOW,
        "water_supply": Listing.WaterSupply.BOTH,
        "description": (
            "Standalone bungalow section with its own entrance and small garden. "
            "Master en-suite. Compound is shared with the landlord's family, which "
            "means the place is genuinely secure. No agent fee."
        ),
        "amenities": ["has_parking", "has_security", "has_borehole_backup"],
    },
    {
        "title": "Shared 4 bedroom for students, Juja",
        "county": "Kiambu",
        "area": "Juja",
        "nearest_landmark": "JKUAT Main Gate",
        "walking_minutes_to_landmark": 10,
        "landmark_description": (
            "From JKUAT main gate walk towards Gachororo. Pass the two hostels, then "
            "turn left at the cyber. It is the yellow building with the water tank "
            "tower, first floor."
        ),
        "bedrooms": 4,
        "bathrooms": 2,
        "rent": 9000,
        "property_type": Listing.PropertyType.SHARED,
        "water_supply": Listing.WaterSupply.TANK,
        "description": (
            "Price is per room in a shared four bedroom unit. Kitchen and sitting "
            "room are shared. Wi-Fi is included. Suits students or people doing "
            "attachment at JKUAT. Two rooms currently free."
        ),
        "amenities": ["has_water_included", "has_security"],
    },
]

PHOTO_PALETTE = {
    PhotoCategory.EXTERIOR: (("#8FB8A6", "Building exterior"),),
    PhotoCategory.ENTRANCE: (("#6E8CA0", "Gate and entrance"),),
    PhotoCategory.ROOM: (("#C9A227", "Sitting room"),),
    PhotoCategory.METER: (("#7A7A7A", "Tokens meter"),),
    PhotoCategory.LANDMARK: (("#1B9D80", "Nearest landmark"),),
    PhotoCategory.OTHER: (("#B5651D", "Kitchen"),),
}

LANDLORD_COMMENTS = [
    "The house was exactly what the photos showed, including the meter. Repairs took "
    "a day or two but they always came. Deposit came back in full.",
    "Honest landlord. When the borehole pump failed she fixed it within 48 hours and "
    "did not pass the cost to us. I would rent from her again.",
    "Good experience overall. Only issue was the water bill splitting, which we sorted "
    "after a conversation. Directions on the listing were spot on.",
]

TENANT_COMMENTS = [
    "Paid rent by the 5th every month for two years. Left the house cleaner than she "
    "found it. Any landlord would be lucky to have her.",
    "Reliable tenant, easy to reach on phone. Handled small repairs himself and told "
    "me about the bigger ones early.",
]


class Command(BaseCommand):
    help = "Load demo landlords, tenants, listings, tenancies and reviews."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(20240501)

        if options["flush"]:
            emails = [row[1] for row in LANDLORDS + TENANTS]
            User.objects.filter(email__in=emails).delete()
            self.stdout.write("Removed existing demo accounts.")

        landlords = [self._make_user(*row, role=User.Role.LANDLORD) for row in LANDLORDS]
        tenants = [self._make_user(*row, role=User.Role.TENANT) for row in TENANTS]

        listings = []
        for index, spec in enumerate(LISTINGS):
            landlord = landlords[index % len(landlords)]
            listings.append(self._make_listing(spec, landlord))

        self._make_tenancies_and_reviews(listings, tenants)
        self._make_saves(listings, tenants)
        self._ensure_superuser()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(landlords)} landlords, {len(tenants)} tenants and "
                f"{len(listings)} listings. Password for every demo account: {PASSWORD}"
            )
        )

    # -- users --------------------------------------------------------------

    def _make_user(self, full_name, email, phone, verified, *, role):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "phone": phone,
                "role": role,
                "preferred_area": "Ruaka" if role == User.Role.TENANT else "",
                "bio": (
                    "Manages a few units and answers the phone."
                    if role == User.Role.LANDLORD
                    else "Looking for a quiet place with reliable water."
                ),
            },
        )
        if created:
            user.set_password(PASSWORD)
            user.save(update_fields=["password"])

        status = VerificationStatus.APPROVED if verified else VerificationStatus.PENDING
        if role == User.Role.LANDLORD:
            LandlordVerification.objects.update_or_create(
                user=user,
                defaults={
                    "status": status,
                    "national_id_number": f"3{user.pk:07d}",
                    "national_id_front": self._doc_file(f"id-{user.pk}.png"),
                    "ownership_proof_type": LandlordVerification.OwnershipProofType.TITLE_DEED,
                    "ownership_document": self._doc_file(f"deed-{user.pk}.png"),
                    "property_address": "Demo property, Kenya",
                    "reviewed_at": timezone.now() if verified else None,
                },
            )
        else:
            TenantVerification.objects.update_or_create(
                user=user,
                defaults={
                    "status": status,
                    "national_id_number": f"2{user.pk:07d}",
                    "national_id_front": self._doc_file(f"id-{user.pk}.png"),
                    "employer_name": "Demo Employer Ltd",
                    "reviewed_at": timezone.now() if verified else None,
                },
            )
        return user

    # -- listings -----------------------------------------------------------

    def _make_listing(self, spec, landlord):
        listing, created = Listing.objects.get_or_create(
            landlord=landlord,
            title=spec["title"],
            defaults={
                "description": spec["description"],
                "property_type": spec["property_type"],
                "bedrooms": spec["bedrooms"],
                "bathrooms": spec["bathrooms"],
                "rent_amount": Decimal(spec["rent"]),
                "deposit_amount": Decimal(spec["rent"]),
                "county": spec["county"],
                "area": spec["area"],
                "landmark_description": spec["landmark_description"],
                "nearest_landmark": spec["nearest_landmark"],
                "walking_minutes_to_landmark": spec["walking_minutes_to_landmark"],
                "water_supply": spec["water_supply"],
                "available_from": timezone.localdate(),
                "view_count": random.randint(15, 480),
                **{name: True for name in spec["amenities"]},
            },
        )
        if not created:
            return listing

        for order, category in enumerate(
            [
                PhotoCategory.EXTERIOR,
                PhotoCategory.ENTRANCE,
                PhotoCategory.ROOM,
                PhotoCategory.METER,
                PhotoCategory.LANDMARK,
                PhotoCategory.OTHER,
            ]
        ):
            colour, caption = PHOTO_PALETTE[category][0]
            ListingPhoto.objects.create(
                listing=listing,
                category=category,
                caption=caption,
                sort_order=order,
                image=self._photo_file(
                    f"{listing.slug}-{category}.png", colour, caption, spec["area"]
                ),
            )

        # The unverified landlord's listing stays a draft, which is the point.
        if landlord.is_verified_landlord:
            listing.status = Listing.Status.PUBLISHED
            listing.published_at = timezone.now() - timedelta(days=random.randint(1, 30))
            listing.save(update_fields=["status", "published_at"])
        return listing

    # -- trust loop ---------------------------------------------------------

    def _make_tenancies_and_reviews(self, listings, tenants):
        published = [listing for listing in listings if listing.is_published]
        for index, listing in enumerate(published[:4]):
            tenant = tenants[index % len(tenants)]
            if listing.landlord_id == tenant.pk:
                continue

            started = timezone.localdate() - timedelta(days=random.randint(400, 900))
            ended = started + timedelta(days=random.randint(200, 380))
            tenancy, created = Tenancy.objects.get_or_create(
                listing=listing,
                tenant=tenant,
                started_on=started,
                defaults={
                    "landlord": listing.landlord,
                    "ended_on": ended,
                    "status": Tenancy.Status.ENDED,
                },
            )
            if not created:
                continue

            LandlordReview.objects.create(
                tenancy=tenancy,
                author=tenant,
                landlord=listing.landlord,
                responsiveness=random.randint(3, 5),
                deposit_fairness=random.randint(3, 5),
                listing_honesty=random.randint(4, 5),
                comment=random.choice(LANDLORD_COMMENTS),
            )
            # One tenancy is left unreviewed by the landlord so the dashboard
            # prompt has something to show.
            if index % 3 != 2:
                TenantReview.objects.create(
                    tenancy=tenancy,
                    author=listing.landlord,
                    tenant=tenant,
                    payment_reliability=random.randint(4, 5),
                    property_care=random.randint(3, 5),
                    communication=random.randint(3, 5),
                    comment=random.choice(TENANT_COMMENTS),
                )

    def _make_saves(self, listings, tenants):
        published = [listing for listing in listings if listing.is_published]
        for tenant in tenants[:2]:
            for listing in random.sample(published, min(2, len(published))):
                SavedListing.objects.get_or_create(user=tenant, listing=listing)

    def _ensure_superuser(self):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email="admin@mrentals.co.ke",
                password="admin12345",
                full_name="Mrentals Admin",
            )
            self.stdout.write("Created superuser admin@mrentals.co.ke / admin12345")

    # -- placeholder imagery ------------------------------------------------

    def _photo_file(self, name, colour, caption, area) -> ContentFile:
        image = Image.new("RGB", (960, 640), colour)
        draw = ImageDraw.Draw(image)
        draw.rectangle([40, 40, 920, 600], outline="#FFFFFF", width=4)
        draw.text((70, 500), caption, fill="#FFFFFF")
        draw.text((70, 530), area, fill="#FFFFFF")
        draw.text((70, 560), "Mrentals demo photo", fill="#FFFFFF")
        return self._to_file(image, name)

    def _doc_file(self, name) -> ContentFile:
        image = Image.new("RGB", (640, 400), "#E9EEF2")
        draw = ImageDraw.Draw(image)
        draw.rectangle([20, 20, 620, 380], outline="#1B9D80", width=3)
        draw.text((50, 180), "DEMO DOCUMENT: NOT A REAL ID", fill="#0F172A")
        return self._to_file(image, name)

    def _to_file(self, image: Image.Image, name: str) -> ContentFile:
        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        return ContentFile(buffer.getvalue(), name=name)
