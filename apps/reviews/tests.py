"""Tests for the tenancy gate on two-way reviews."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.listings.models import Listing
from apps.listings.tests import make_landlord, make_listing

from .forms import RecordTenancyForm
from .models import LandlordReview, Tenancy, TenantReview

User = get_user_model()


def make_tenant(email="tenant@example.com", phone=None) -> User:
    return User.objects.create_user(
        email=email, phone=phone, full_name="Test Tenant", password="pw12345678"
    )


class RecordTenancyTests(TestCase):
    def setUp(self):
        self.landlord = make_landlord()
        self.listing = make_listing(self.landlord, status=Listing.Status.PUBLISHED)
        self.tenant = make_tenant(phone="+254712345678")
        self.url = reverse("reviews:record_tenancy", args=[self.listing.slug])

    def form(self, **overrides):
        data = {
            "tenant_identifier": "tenant@example.com",
            "started_on": "2023-01-01",
            "ended_on": "",
        } | overrides
        return RecordTenancyForm(data, listing=self.listing, landlord=self.landlord)

    def test_tenant_can_be_found_by_email(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().tenant, self.tenant)

    def test_tenant_can_be_found_by_local_phone_number(self):
        form = self.form(tenant_identifier="0712345678")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().tenant, self.tenant)

    def test_unknown_person_is_rejected(self):
        form = self.form(tenant_identifier="nobody@example.com")
        self.assertFalse(form.is_valid())
        self.assertIn("tenant_identifier", form.errors)

    def test_landlord_cannot_record_themselves(self):
        form = self.form(tenant_identifier=self.landlord.email)
        self.assertFalse(form.is_valid())

    def test_end_date_cannot_precede_start_date(self):
        form = self.form(started_on="2023-06-01", ended_on="2023-01-01")
        self.assertFalse(form.is_valid())
        self.assertIn("ended_on", form.errors)

    def test_duplicate_tenancy_is_rejected(self):
        self.form().save()
        self.assertFalse(self.form().is_valid())

    def test_only_the_listing_owner_may_record_a_tenancy(self):
        intruder = make_landlord("intruder@example.com")
        self.client.force_login(intruder)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


class ReviewGatingTests(TestCase):
    """Reviews exist only because a tenancy is on record."""

    def setUp(self):
        self.landlord = make_landlord()
        self.listing = make_listing(self.landlord, status=Listing.Status.PUBLISHED)
        self.tenant = make_tenant()
        self.outsider = make_tenant("outsider@example.com")
        self.tenancy = Tenancy.objects.create(
            listing=self.listing,
            landlord=self.landlord,
            tenant=self.tenant,
            started_on=timezone.localdate() - timedelta(days=400),
        )

    def landlord_review_payload(self):
        return {
            "responsiveness": 5,
            "deposit_fairness": 4,
            "listing_honesty": 5,
            "comment": "Repairs were handled quickly and the deposit came back in full.",
        }

    def tenant_review_payload(self):
        return {
            "payment_reliability": 5,
            "property_care": 4,
            "communication": 4,
            "comment": "Paid on time every month and looked after the house well.",
        }

    def test_tenant_on_the_tenancy_can_review_the_landlord(self):
        self.client.force_login(self.tenant)
        response = self.client.post(
            reverse("reviews:review_landlord", args=[self.tenancy.pk]),
            self.landlord_review_payload(),
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LandlordReview.objects.filter(tenancy=self.tenancy).exists())

    def test_an_outsider_cannot_review_the_landlord(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse("reviews:review_landlord", args=[self.tenancy.pk]),
            self.landlord_review_payload(),
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(LandlordReview.objects.exists())

    def test_the_landlord_cannot_review_themselves_as_the_tenant_side(self):
        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("reviews:review_landlord", args=[self.tenancy.pk]),
            self.landlord_review_payload(),
        )
        self.assertEqual(response.status_code, 403)

    def test_landlord_on_the_tenancy_can_review_the_tenant(self):
        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("reviews:review_tenant", args=[self.tenancy.pk]),
            self.tenant_review_payload(),
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TenantReview.objects.filter(tenancy=self.tenancy).exists())

    def test_a_second_review_of_the_same_tenancy_is_refused(self):
        self.client.force_login(self.tenant)
        url = reverse("reviews:review_landlord", args=[self.tenancy.pk])
        self.client.post(url, self.landlord_review_payload())
        self.client.post(url, self.landlord_review_payload())
        self.assertEqual(LandlordReview.objects.filter(tenancy=self.tenancy).count(), 1)

    def test_a_one_word_comment_is_refused(self):
        self.client.force_login(self.tenant)
        self.client.post(
            reverse("reviews:review_landlord", args=[self.tenancy.pk]),
            self.landlord_review_payload() | {"comment": "Good"},
        )
        self.assertFalse(LandlordReview.objects.exists())

    def test_model_level_authorship_check(self):
        review = LandlordReview(
            tenancy=self.tenancy,
            author=self.outsider,
            landlord=self.landlord,
            **{k: v for k, v in self.landlord_review_payload().items()},
        )
        with self.assertRaises(ValidationError):
            review.full_clean()


class OverallRatingTests(TestCase):
    def setUp(self):
        landlord = make_landlord()
        listing = make_listing(landlord, status=Listing.Status.PUBLISHED)
        self.tenancy = Tenancy.objects.create(
            listing=listing,
            landlord=landlord,
            tenant=make_tenant(),
            started_on=timezone.localdate() - timedelta(days=200),
        )
        self.landlord = landlord

    def test_overall_rating_is_the_mean_of_the_three_scores(self):
        review = LandlordReview.objects.create(
            tenancy=self.tenancy,
            author=self.tenancy.tenant,
            landlord=self.landlord,
            responsiveness=5,
            deposit_fairness=4,
            listing_honesty=3,
            comment="Mixed experience but broadly a fair and reachable landlord.",
        )
        self.assertEqual(review.overall_rating, 4)

    def test_tenancy_knows_which_reviews_exist(self):
        self.assertFalse(self.tenancy.has_landlord_review)
        LandlordReview.objects.create(
            tenancy=self.tenancy,
            author=self.tenancy.tenant,
            landlord=self.landlord,
            responsiveness=5,
            deposit_fairness=5,
            listing_honesty=5,
            comment="Everything about the listing was accurate, no surprises at all.",
        )
        self.tenancy.refresh_from_db()
        self.assertTrue(self.tenancy.has_landlord_review)
