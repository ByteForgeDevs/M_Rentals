"""Reusable validators shared across Mrentals apps."""

import re

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

KENYAN_PHONE_RE = re.compile(r"^\+254(7|1)\d{8}$")


def normalize_phone(raw: str | None) -> str | None:
    """Normalize common Kenyan phone formats to E.164 (+2547XXXXXXXX)."""
    if not raw:
        return None
    digits = re.sub(r"[\s\-().]", "", str(raw))
    if digits.startswith("+"):
        candidate = digits
    elif digits.startswith("254"):
        candidate = f"+{digits}"
    elif digits.startswith("0"):
        candidate = f"+254{digits[1:]}"
    elif len(digits) == 9 and digits[0] in {"7", "1"}:
        candidate = f"+254{digits}"
    else:
        candidate = digits
    return candidate


def validate_kenyan_phone(value: str) -> None:
    if not KENYAN_PHONE_RE.match(value or ""):
        raise ValidationError(
            _("Enter a valid Kenyan phone number, for example 0712 345 678."),
            code="invalid_phone",
        )


def validate_file_size(max_bytes: int):
    """Build a validator that rejects uploads larger than ``max_bytes``."""
    return MaxFileSizeValidator(max_bytes)


@deconstructible
class MaxFileSizeValidator:
    """Reject uploads larger than ``max_bytes`` (migration-serializable)."""

    def __init__(self, max_bytes: int):
        self.max_bytes = max_bytes

    def __call__(self, file_obj):
        if file_obj and file_obj.size > self.max_bytes:
            raise ValidationError(
                _("File is too large. Keep it under %(limit)s MB.")
                % {"limit": round(self.max_bytes / (1024 * 1024))},
                code="file_too_large",
            )

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_bytes == other.max_bytes
