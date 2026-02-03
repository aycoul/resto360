from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from apps.core.models import BaseModel


class UserManager(BaseUserManager):
    """Manager for custom User model with phone as username."""

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Users must have a phone number")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "owner")
        return self.create_user(phone, password, **extra_fields)


class Restaurant(BaseModel):
    """A restaurant tenant in the system."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default="Africa/Abidjan")
    currency = models.CharField(max_length=3, default="XOF")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """Custom user with phone number as username."""

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("manager", "Manager"),
        ("cashier", "Cashier"),
        ("kitchen", "Kitchen"),
        ("driver", "Driver"),
    ]

    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=150)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="staff",
        null=True,
        blank=True,  # Null for superusers without restaurant
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="cashier")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default="fr")

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def get_permissions_list(self):
        """Return list of permissions based on role."""
        base_permissions = ["view_menu", "view_orders"]
        role_permissions = {
            "owner": [
                "manage_restaurant",
                "manage_staff",
                "manage_menu",
                "view_reports",
                "manage_orders",
            ],
            "manager": ["manage_menu", "view_reports", "manage_orders"],
            "cashier": ["create_orders", "manage_orders"],
            "kitchen": ["update_order_status"],
            "driver": ["view_deliveries", "update_delivery_status"],
        }
        return base_permissions + role_permissions.get(self.role, [])
