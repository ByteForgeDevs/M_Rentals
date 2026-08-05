from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .validators import normalize_phone, validate_kenyan_phone


class UserManager(BaseUserManager):
    """Manager that accepts an email address, a phone number, or both."""

    use_in_migrations = True

    def _create_user(self, password, email=None, phone=None, **extra_fields):
        email = self.normalize_email(email) if email else None
        phone = normalize_phone(phone)
        if not email and not phone:
            raise ValueError("Users must have either an email address or a phone number.")
        user = self.model(email=email or None, phone=phone or None, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_user(self, password=None, email=None, phone=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(password, email=email, phone=phone, **extra_fields)

    def create_superuser(self, password=None, email=None, phone=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("full_name", "Mrentals Admin")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(password, email=email, phone=phone, **extra_fields)


class User(AbstractUser):
    """Account that can act as a tenant or a landlord/agent.

    Kenya is phone-first, but agents and property managers work over email, so
    either identifier can be used to sign in as long as at least one is present.
    """

    class Role(models.TextChoices):
        TENANT = "tenant", _("Tenant")
        LANDLORD = "landlord", _("Landlord / Agent")

    username = None
    first_name = None
    last_name = None

    email = models.EmailField(
        _("email address"),
        unique=True,
        null=True,
        blank=True,
        validators=[EmailValidator()],
    )
    phone = models.CharField(
        _("phone number"),
        max_length=16,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_kenyan_phone],
        help_text=_("Kenyan mobile number, e.g. 0712 345 678."),
    )
    full_name = models.CharField(_("full name"), max_length=120)
    role = models.CharField(
        _("primary role"), max_length=16, choices=Role.choices, default=Role.TENANT
    )
    bio = models.TextField(_("about"), blank=True, max_length=600)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    preferred_area = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(phone__isnull=False),
                name="user_has_email_or_phone",
            )
        ]

    def __str__(self):
        return self.full_name or self.login_identifier or f"User #{self.pk}"

    def clean(self):
        super().clean()
        self.phone = normalize_phone(self.phone) or None
        self.email = self.email.lower().strip() if self.email else None
        if not self.email and not self.phone:
            raise ValidationError(
                _("Provide at least an email address or a phone number."),
                code="missing_identifier",
            )

    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone) or None
        self.email = self.email.lower().strip() if self.email else None
        super().save(*args, **kwargs)

    @property
    def login_identifier(self) -> str:
        return self.email or self.phone or ""

    @property
    def is_landlord(self) -> bool:
        return self.role == self.Role.LANDLORD

    @property
    def is_tenant(self) -> bool:
        return self.role == self.Role.TENANT

    @property
    def display_initials(self) -> str:
        parts = [p for p in (self.full_name or "").split() if p]
        return "".join(p[0].upper() for p in parts[:2]) or "M"

    @property
    def is_verified_landlord(self) -> bool:
        verification = getattr(self, "landlord_verification", None)
        return bool(verification and verification.is_approved)

    @property
    def is_verified_tenant(self) -> bool:
        verification = getattr(self, "tenant_verification", None)
        return bool(verification and verification.is_approved)

    @property
    def is_verified(self) -> bool:
        return self.is_verified_landlord if self.is_landlord else self.is_verified_tenant

    def get_absolute_url(self):
        return reverse("accounts:public_profile", kwargs={"pk": self.pk})
