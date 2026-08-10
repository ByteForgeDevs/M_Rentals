from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import User
from .validators import normalize_phone, validate_kenyan_phone

TEXT_INPUT_CLASS = (
    "w-full min-h-[44px] rounded-lg border border-slate-300 bg-white px-3 py-2.5 "
    "text-slate-900 shadow-sm transition duration-150 placeholder:text-slate-400 "
    "hover:border-slate-400 focus:border-brand focus:outline-none focus:ring-2 "
    "focus:ring-brand/30"
)

CHECKBOX_CLASS = (
    "mt-0.5 h-5 w-5 shrink-0 rounded border-slate-300 text-brand transition "
    "focus:ring-2 focus:ring-brand/40 focus:ring-offset-0"
)


class StyledFormMixin:
    """Apply the Mrentals input styling to every widget in a form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} {CHECKBOX_CLASS}".strip()
                continue
            if isinstance(widget, forms.RadioSelect):
                continue
            if isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault(
                    "class",
                    "w-full text-sm text-slate-600 file:mr-3 file:cursor-pointer "
                    "file:rounded-lg file:border-0 file:bg-brand file:px-4 file:py-2 "
                    "file:font-semibold file:text-white hover:file:bg-brand-600",
                )
                continue
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {TEXT_INPUT_CLASS}".strip()


class SignUpForm(StyledFormMixin, UserCreationForm):
    """Sign up with an email address, a phone number, or both."""

    email = forms.EmailField(
        required=False,
        label=_("Email address"),
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
    )
    phone = forms.CharField(
        required=False,
        label=_("Phone number"),
        widget=forms.TextInput(attrs={"placeholder": "0712 345 678", "autocomplete": "tel"}),
        help_text=_("We use this so landlords can reach you. Format: 0712 345 678."),
    )

    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "role"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": _("e.g. Achieng Otieno")}),
            "role": forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = User.Role.choices
        self.fields["password1"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["password2"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["password2"].label = _("Confirm password")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email already exists."))
        return email or None

    def clean_phone(self):
        raw = (self.cleaned_data.get("phone") or "").strip()
        if not raw:
            return None
        phone = normalize_phone(raw)
        validate_kenyan_phone(phone)
        if User.objects.filter(phone=phone).exists():
            raise ValidationError(_("An account with this phone number already exists."))
        return phone

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("email") and not cleaned.get("phone"):
            raise ValidationError(
                _("Give us at least one way to reach you: an email address or a phone number.")
            )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email") or None
        user.phone = self.cleaned_data.get("phone") or None
        if commit:
            user.save()
        return user


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(
        label=_("Email or phone number"),
        widget=forms.TextInput(
            attrs={"placeholder": _("you@example.com or 0712 345 678"), "autofocus": True}
        ),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("That email/phone and password combination is not correct."),
    }


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "bio", "preferred_area", "avatar"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "preferred_area": forms.TextInput(
                attrs={"placeholder": _("e.g. Ruaka, Kiambu")}
            ),
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and (
            User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()
        ):
            raise ValidationError(_("An account with this email already exists."))
        return email or None

    def clean_phone(self):
        raw = (self.cleaned_data.get("phone") or "").strip()
        if not raw:
            return None
        phone = normalize_phone(raw)
        validate_kenyan_phone(phone)
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("An account with this phone number already exists."))
        return phone

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("email") and not cleaned.get("phone"):
            raise ValidationError(
                _("Keep at least one contact method: an email address or a phone number.")
            )
        return cleaned


class RoleSwitchForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["role"]
        widgets = {"role": forms.RadioSelect}
