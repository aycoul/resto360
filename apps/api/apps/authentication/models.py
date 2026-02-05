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


class Business(BaseModel):
    """
    Multi-type business tenant model (formerly Restaurant).

    Supports restaurants, retail shops, bakeries, pharmacies, confectioneries, etc.
    This is the core tenant model for the BIZ360 platform.
    """

    BUSINESS_TYPE_CHOICES = [
        ("restaurant", "Restaurant"),
        ("cafe", "Café"),
        ("bakery", "Bakery"),
        ("retail", "Retail Shop"),
        ("pharmacy", "Pharmacy"),
        ("confectionery", "Confectionery"),
        ("grocery", "Grocery Store"),
        ("boutique", "Boutique"),
        ("hardware", "Hardware Store"),
        ("other", "Other"),
    ]

    PLAN_TYPE_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
        ("full", "Full Platform"),
    ]

    TAX_REGIME_CHOICES = [
        ("", "None"),
        ("rne", "RNE (Registre Numérique des Encaissements)"),
        ("fne", "FNE (Facture Normalisée Électronique)"),
        ("simplified", "Régime Simplifié"),
        ("real", "Régime Réel"),
    ]

    # Basic information
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default="Africa/Abidjan")
    currency = models.CharField(max_length=3, default="XOF")
    is_active = models.BooleanField(default=True)

    # Business type (NEW)
    business_type = models.CharField(
        max_length=20,
        choices=BUSINESS_TYPE_CHOICES,
        default="restaurant",
        help_text="Type of business (determines UI and features)",
    )

    # Location for delivery zone calculations
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    # Plan type for freemium model
    plan_type = models.CharField(
        max_length=10, choices=PLAN_TYPE_CHOICES, default="free"
    )

    # Branding options
    logo = models.ImageField(upload_to="business_logos/", blank=True, null=True)
    primary_color = models.CharField(
        max_length=7, blank=True, help_text="Hex color code"
    )
    show_branding = models.BooleanField(
        default=True, help_text="Show BIZ360 branding on free tier"
    )

    # Tax compliance - Ivory Coast DGI (NEW)
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="NCC (Numéro de Compte Contribuable) or RCC number",
    )
    tax_regime = models.CharField(
        max_length=20,
        choices=TAX_REGIME_CHOICES,
        blank=True,
        default="",
        help_text="Tax regime (RNE, FNE, etc.)",
    )
    dgi_api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="DGI API key (encrypted in production)",
    )
    dgi_api_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="DGI API secret (encrypted in production)",
    )
    dgi_is_production = models.BooleanField(
        default=False,
        help_text="Use production DGI API (vs sandbox)",
    )
    default_tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        help_text="Default tax rate (Ivory Coast VAT is 18%)",
    )

    # Food-specific features (only for restaurants/cafes/bakeries)
    has_kitchen_display = models.BooleanField(
        default=False,
        help_text="Enable kitchen display system",
    )
    has_table_service = models.BooleanField(
        default=False,
        help_text="Enable table management",
    )
    has_delivery = models.BooleanField(
        default=False,
        help_text="Enable delivery features",
    )

    # Multi-location support
    brand = models.ForeignKey(
        "locations.Brand",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locations",
        help_text="Parent brand for chain businesses",
    )
    location_group = models.ForeignKey(
        "locations.LocationGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locations",
        help_text="Group this location belongs to (region, city, etc.)",
    )
    location_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Internal location code for the brand",
    )
    is_flagship = models.BooleanField(
        default=False,
        help_text="Is this the flagship/main location for the brand",
    )

    class Meta:
        db_table = "authentication_restaurant"  # Keep old table name for compatibility
        ordering = ["name"]
        verbose_name = "Business"
        verbose_name_plural = "Businesses"

    def __str__(self):
        return self.name

    @property
    def is_part_of_chain(self) -> bool:
        """Check if this business is part of a brand/chain."""
        return self.brand is not None

    @property
    def is_food_business(self) -> bool:
        """Check if this is a food-related business (restaurant, cafe, bakery)."""
        return self.business_type in ("restaurant", "cafe", "bakery", "confectionery")

    @property
    def requires_kitchen(self) -> bool:
        """Check if this business type typically requires a kitchen."""
        return self.business_type in ("restaurant", "cafe", "bakery")

    @property
    def is_dgi_enabled(self) -> bool:
        """Check if DGI electronic invoicing is configured."""
        return bool(self.tax_id and self.tax_regime and self.dgi_api_key)


# Backwards compatibility alias
Restaurant = Business


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
    # Use Business as the ForeignKey (Restaurant is an alias for backwards compatibility)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="staff",
        null=True,
        blank=True,  # Null for superusers without business
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

    @property
    def restaurant(self):
        """Backwards compatibility: alias for business."""
        return self.business

    @restaurant.setter
    def restaurant(self, value):
        """Backwards compatibility: alias for business."""
        self.business = value

    def get_permissions_list(self):
        """Return list of permissions based on role."""
        base_permissions = ["view_menu", "view_orders"]
        role_permissions = {
            "owner": [
                "manage_business",
                "manage_staff",
                "manage_menu",
                "view_reports",
                "manage_orders",
                "manage_invoices",
                "manage_tax",
            ],
            "manager": ["manage_menu", "view_reports", "manage_orders", "view_invoices"],
            "cashier": ["create_orders", "manage_orders", "create_invoices"],
            "kitchen": ["update_order_status"],
            "driver": ["view_deliveries", "update_delivery_status"],
        }
        return base_permissions + role_permissions.get(self.role, [])
