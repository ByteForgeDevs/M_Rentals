"""Tests for the dual email/phone identity model."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .validators import normalize_phone, validate_kenyan_phone

User = get_user_model()


class PhoneNormalisationTests(TestCase):
    def test_local_formats_normalise_to_e164(self):
        for raw in ["0712345678", "0712 345 678", "+254712345678", "254712345678", "712345678"]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_phone(raw), "+254712345678")

    def test_safaricom_and_airtel_prefixes_are_valid(self):
        for raw in ["+254712345678", "+254110345678", "+254733123456"]:
            with self.subTest(raw=raw):
                validate_kenyan_phone(raw)

    def test_obviously_wrong_numbers_are_rejected(self):
        for raw in ["+2547123", "+1234567890123"]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValidationError):
                    validate_kenyan_phone(normalize_phone(raw))


class UserModelTests(TestCase):
    def test_user_can_be_created_with_only_a_phone(self):
        user = User.objects.create_user(
            email=None, phone="+254712345678", full_name="Phone Only", password="pw12345678"
        )
        self.assertIsNone(user.email)
        self.assertEqual(user.phone, "+254712345678")

    def test_user_needs_at_least_one_contact_method(self):
        with self.assertRaises((ValueError, IntegrityError, ValidationError)):
            User.objects.create_user(
                email=None, phone=None, full_name="Nobody", password="pw12345678"
            )

    def test_multiple_users_may_have_no_email(self):
        """Nullable-unique must not collide across rows."""
        User.objects.create_user(
            email=None, phone="+254712345678", full_name="A", password="pw12345678"
        )
        User.objects.create_user(
            email=None, phone="+254712345679", full_name="B", password="pw12345678"
        )
        self.assertEqual(User.objects.filter(email__isnull=True).count(), 2)


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="Achieng@Example.com",
            phone="+254712345678",
            full_name="Achieng Otieno",
            password="pw12345678",
        )

    def test_login_with_email_is_case_insensitive(self):
        self.assertTrue(
            self.client.login(username="achieng@example.com", password="pw12345678")
        )

    def test_login_with_phone_in_local_format(self):
        self.assertTrue(self.client.login(username="0712345678", password="pw12345678"))

    def test_login_with_wrong_password_fails(self):
        self.assertFalse(self.client.login(username="0712345678", password="nope12345"))


class SignUpViewTests(TestCase):
    url = reverse("accounts:signup")

    def test_signup_with_phone_only_creates_account(self):
        response = self.client.post(
            self.url,
            {
                "full_name": "Wanjiru Njoroge",
                "email": "",
                "phone": "0722000111",
                "role": User.Role.TENANT,
                "password1": "SafeHouse2024!",
                "password2": "SafeHouse2024!",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(phone="+254722000111")
        self.assertIsNone(user.email)

    def test_signup_without_email_or_phone_is_rejected(self):
        response = self.client.post(
            self.url,
            {
                "full_name": "Ghost",
                "email": "",
                "phone": "",
                "role": User.Role.TENANT,
                "password1": "SafeHouse2024!",
                "password2": "SafeHouse2024!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(full_name="Ghost").exists())

    def test_landlord_signup_redirects_to_verification(self):
        response = self.client.post(
            self.url,
            {
                "full_name": "Peter Kamau",
                "email": "peter@example.com",
                "phone": "",
                "role": User.Role.LANDLORD,
                "password1": "SafeHouse2024!",
                "password2": "SafeHouse2024!",
            },
        )
        self.assertRedirects(response, reverse("verification:landlord"))
