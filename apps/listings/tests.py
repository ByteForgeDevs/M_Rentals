"""Tests for listing publication gating, search and saving."""

from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.verification.models import LandlordVerification, VerificationStatus

from .models import Listing, ListingPhoto, PhotoCategory, SavedListing
from .selectors import search_listings

User = get_user_model()

REQUIRED_CATEGORIES = [
    PhotoCategory.EXTERIOR,
    PhotoCategory.ENTRANCE,
    PhotoCategory.ROOM,
    PhotoCategory.METER,
    PhotoCategory.LANDMARK,
]


def image_file(name="photo.png") -> ContentFile:
    buffer = BytesIO()
    Image.new("RGB", (40, 40), "#1B9D80").save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=name)


def make_landlord(email="landlord@example.com", *, verified=True) -> User:
    user = User.objects.create_user(
        email=email, full_name="Test Landlord", password="pw12345678", role=User.Role.LANDLORD
    )
    LandlordVerification.objects.create(
        user=user,
        status=VerificationStatus.APPROVED if verified else VerificationStatus.PENDING,
        national_id_number="12345678",
        national_id_front=image_file("id.png"),
        ownership_proof_type=LandlordVerification.OwnershipProofType.TITLE_DEED,
        ownership_document=image_file("deed.png"),
        property_address="Somewhere",
    )
    return user


def make_listing(landlord, **overrides) -> Listing:
    defaults = {
        "title": "Neat 2 bedroom in Ruaka",
        "description": "A clean two bedroom close to the shops and the stage.",
        "bedrooms": 2,
        "bathrooms": 1,
        "rent_amount": Decimal("32000"),
        "county": "Kiambu",
        "area": "Ruaka",
        "landmark_description": "200m from Quickmart Ruaka, blue gate, third building.",
        "nearest_landmark": "Quickmart Ruaka",
        "walking_minutes_to_landmark": 4,
    }
    return Listing.objects.create(landlord=landlord, **(defaults | overrides))


def add_photos(listing, categories=REQUIRED_CATEGORIES):
    for category in categories:
        ListingPhoto.objects.create(
            listing=listing, category=category, image=image_file(f"{category}.png")
        )


class PublicationGatingTests(TestCase):
    """A listing may only go live with a verified landlord and a full photo set."""

    def test_missing_photos_block_publication(self):
        listing = make_listing(make_landlord())
        add_photos(listing, [PhotoCategory.EXTERIOR, PhotoCategory.ROOM])

        self.assertFalse(listing.has_complete_photo_set)
        self.assertFalse(listing.can_publish)
        self.assertIn(PhotoCategory.METER, listing.missing_photo_categories())

    def test_unverified_landlord_blocks_publication(self):
        listing = make_listing(make_landlord(verified=False))
        add_photos(listing)

        self.assertTrue(listing.has_complete_photo_set)
        self.assertFalse(listing.can_publish)
        self.assertTrue(any("verif" in blocker.lower() for blocker in listing.publication_blockers()))

    def test_verified_landlord_with_full_photo_set_can_publish(self):
        listing = make_listing(make_landlord())
        add_photos(listing)

        self.assertEqual(listing.publication_blockers(), [])
        self.assertTrue(listing.can_publish)

    def test_publish_view_refuses_an_incomplete_listing(self):
        landlord = make_landlord()
        listing = make_listing(landlord)
        add_photos(listing, [PhotoCategory.EXTERIOR])

        self.client.force_login(landlord)
        self.client.post(reverse("listings:publish", args=[listing.slug]))

        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.DRAFT)

    def test_publish_view_publishes_a_complete_listing(self):
        landlord = make_landlord()
        listing = make_listing(landlord)
        add_photos(listing)

        self.client.force_login(landlord)
        self.client.post(reverse("listings:publish", args=[listing.slug]))

        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.PUBLISHED)
        self.assertIsNotNone(listing.published_at)

    def test_a_landlord_cannot_manage_someone_elses_listing(self):
        listing = make_listing(make_landlord("owner@example.com"))
        intruder = make_landlord("intruder@example.com")

        self.client.force_login(intruder)
        response = self.client.get(reverse("listings:manage", args=[listing.slug]))
        self.assertEqual(response.status_code, 403)


class VisibilityTests(TestCase):
    def test_drafts_are_hidden_from_search(self):
        landlord = make_landlord()
        make_listing(landlord, title="Draft house")
        published = make_listing(landlord, title="Live house")
        published.status = Listing.Status.PUBLISHED
        published.save()

        titles = list(Listing.objects.published().values_list("title", flat=True))
        self.assertEqual(titles, ["Live house"])

    def test_detail_page_of_a_draft_is_404_for_strangers(self):
        listing = make_listing(make_landlord())
        response = self.client.get(listing.get_absolute_url())
        self.assertEqual(response.status_code, 404)


class SearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.verified = make_landlord("verified@example.com")
        cls.unverified = make_landlord("unverified@example.com", verified=False)

        cls.cheap = make_listing(
            cls.verified,
            title="Bedsitter in Juja",
            area="Juja",
            bedrooms=0,
            rent_amount=Decimal("9000"),
            nearest_landmark="JKUAT Main Gate",
            status=Listing.Status.PUBLISHED,
        )
        cls.mid = make_listing(
            cls.verified,
            title="2 bedroom in Ruaka",
            rent_amount=Decimal("32000"),
            status=Listing.Status.PUBLISHED,
        )
        cls.big = make_listing(
            cls.unverified,
            title="4 bedroom in Nyali",
            county="Mombasa",
            area="Nyali",
            bedrooms=4,
            rent_amount=Decimal("95000"),
            nearest_landmark="Nyali Cinemax",
            status=Listing.Status.PUBLISHED,
        )

    def search(self, **filters):
        return list(search_listings(Listing.objects.published(), filters))

    def test_free_text_matches_the_landmark(self):
        self.assertEqual(self.search(q="JKUAT"), [self.cheap])

    def test_price_range_filter(self):
        results = self.search(min_price=10000, max_price=50000)
        self.assertEqual(results, [self.mid])

    def test_county_filter(self):
        self.assertEqual(self.search(county="Mombasa"), [self.big])

    def test_bedroom_filter_treats_three_as_three_or_more(self):
        self.assertEqual(self.search(bedrooms="3"), [self.big])

    def test_bedroom_filter_matches_bedsitters_exactly(self):
        self.assertEqual(self.search(bedrooms="0"), [self.cheap])

    def test_verified_only_filter_excludes_unverified_landlords(self):
        results = self.search(verified_only=True)
        self.assertNotIn(self.big, results)
        self.assertCountEqual(results, [self.cheap, self.mid])

    def test_cheapest_first_sort(self):
        results = self.search(sort="price_asc")
        self.assertEqual([listing.rent_amount for listing in results],
                         sorted(listing.rent_amount for listing in results))

    def test_search_view_renders_the_partial_for_htmx(self):
        response = self.client.get(reverse("listings:search"), {"q": "Ruaka"}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/partials/results.html")
        self.assertTemplateNotUsed(response, "listings/search.html")


class SaveListingTests(TestCase):
    def setUp(self):
        self.listing = make_listing(make_landlord(), status=Listing.Status.PUBLISHED)
        self.tenant = User.objects.create_user(
            email="tenant@example.com", full_name="Test Tenant", password="pw12345678"
        )
        self.client.force_login(self.tenant)
        self.url = reverse("listings:toggle_save", args=[self.listing.slug])

    def test_toggle_save_adds_then_removes(self):
        self.client.post(self.url)
        self.assertTrue(SavedListing.objects.filter(user=self.tenant).exists())

        self.client.post(self.url)
        self.assertFalse(SavedListing.objects.filter(user=self.tenant).exists())

    def test_anonymous_users_are_sent_to_login(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
