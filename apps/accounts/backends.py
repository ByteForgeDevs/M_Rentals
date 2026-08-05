from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .validators import normalize_phone

UserModel = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    """Authenticate against either the email address or the phone number."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("email") or kwargs.get("phone")
        if identifier is None or password is None:
            return None

        identifier = str(identifier).strip()
        lookup = Q(email__iexact=identifier)
        normalized_phone = normalize_phone(identifier)
        if normalized_phone:
            lookup |= Q(phone=normalized_phone)

        try:
            user = UserModel.objects.get(lookup)
        except UserModel.DoesNotExist:
            # Equalise timing against the "user exists" branch to avoid leaking
            # which identifiers are registered.
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            user = UserModel.objects.filter(lookup).order_by("id").first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
