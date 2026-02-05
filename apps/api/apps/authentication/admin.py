from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Business, User


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    """Admin configuration for Business model."""

    list_display = [
        "name",
        "slug",
        "business_type",
        "phone",
        "timezone",
        "currency",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "currency", "business_type"]
    search_fields = ["name", "slug", "phone"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""

    list_display = ["phone", "name", "role", "business", "is_active", "is_staff"]
    list_filter = ["role", "is_active", "is_staff", "business"]
    search_fields = ["phone", "name", "email"]
    ordering = ["name"]

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal info", {"fields": ("name", "email", "language")}),
        ("Business", {"fields": ("business", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone",
                    "name",
                    "password1",
                    "password2",
                    "business",
                    "role",
                ),
            },
        ),
    )
