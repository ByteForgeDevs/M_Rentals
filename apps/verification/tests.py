"""Tests for the manual verification workflow."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.listings.tests import image_file

from .models import LandlordVerification, TenantVerification, VerificationStatus

User = get_user_model()


def landlord_payload(**overrides):
    return {
        "national_id_number": "12345678",
        "national_id_front": image_file("front.png"),
        "ownership_proof_type": LandlordVerification.OwnershipProofType.TITLE_DEED,
        "ownership_document": image_file("deed.png"),
        "property_address": "Sunrise Court, Ruaka, Kiambu",
    } | overrides


class LandlordVerificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="landlord@example.com",
            full_name="Test Landlord",
            password="pw12345678",
            role=User.Role.LANDLORD,
        )
        self.client.force_login(self.user)
        self.url = reverse("verification:landlord")

    def test_submission_creates_a_pending_request(self):
        response = self.client.post(self.url, landlord_payload())
        self.assertRedirects(response, reverse("verification:status"))

        verification = LandlordVerification.objects.get(user=self.user)
        self.assertEqual(verification.status, VerificationStatus.PENDING)
        self.assertFalse(self.user.is_verified_landlord)

    def test_document_is_required_unless_a_video_call_is_booked(self):
        self.client.post(
            self.url,
            landlord_payload(ownership_document="", ownership_proof_type="title_deed"),
        )
        self.assertFalse(LandlordVerification.objects.exists())

    def test_video_call_route_needs_a_slot(self):
        self.client.post(
            self.url,
            landlord_payload(
                ownership_document="",
                ownership_proof_type=LandlordVerification.OwnershipProofType.VIDEO_CALL,
            ),
        )
        self.assertFalse(LandlordVerification.objects.exists())

    def test_video_call_route_succeeds_with_a_slot(self):
        self.client.post(
            self.url,
            landlord_payload(
                ownership_document="",
                ownership_proof_type=LandlordVerification.OwnershipProofType.VIDEO_CALL,
                video_call_slot="2030-01-01 10:00",
            ),
        )
        self.assertTrue(LandlordVerification.objects.filter(user=self.user).exists())

    def test_approval_flips_the_users_verified_flag(self):
        verification = LandlordVerification.objects.create(
            user=self.user, **landlord_payload()
        )
        verification.approve(notes="Deed checked against the registry.")

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified_landlord)
        self.assertIsNotNone(verification.reviewed_at)

    def test_rejection_records_the_reason_and_allows_resubmission(self):
        verification = LandlordVerification.objects.create(
            user=self.user, **landlord_payload()
        )
        verification.reject(notes="The ID photo is too blurry to read.")
        self.assertTrue(verification.is_rejected)

        response = self.client.post(self.url, landlord_payload())
        self.assertRedirects(response, reverse("verification:status"))

        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.PENDING)
        self.assertIsNone(verification.reviewed_at)

    def test_an_approved_landlord_is_redirected_away_from_the_form(self):
        verification = LandlordVerification.objects.create(
            user=self.user, **landlord_payload()
        )
        verification.approve()

        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("verification:status"))

    def test_the_form_requires_a_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)


class TenantVerificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="tenant@example.com", full_name="Test Tenant", password="pw12345678"
        )
        self.client.force_login(self.user)

    def test_income_documents_are_optional(self):
        response = self.client.post(
            reverse("verification:tenant"),
            {"national_id_number": "87654321", "national_id_front": image_file("front.png")},
        )
        self.assertRedirects(response, reverse("verification:status"))
        self.assertTrue(TenantVerification.objects.filter(user=self.user).exists())

    def test_approval_flips_the_tenant_flag(self):
        verification = TenantVerification.objects.create(
            user=self.user,
            national_id_number="87654321",
            national_id_front=image_file("front.png"),
        )
        verification.approve()

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified_tenant)
