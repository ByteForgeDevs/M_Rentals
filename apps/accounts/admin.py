from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["full_name", "email", "phone", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active", "is_staff", "created_at"]
    search_fields = ["full_name", "email", "phone"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "last_login"]

    fieldsets = (
        (None, {"fields": ("email", "phone", "password")}),
        (_("Profile"), {"fields": ("full_name", "role", "bio", "avatar", "preferred_area")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Dates"), {"fields": ("last_login", "created_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("full_name", "email", "phone", "role", "password1", "password2"),
            },
        ),
    )
