"""
Multi-location Support Models

Manage restaurant chains with multiple locations, shared menus,
and centralized brand settings.
"""

import uuid
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class Brand(BaseModel):
    """
    A brand represents a restaurant chain/franchise.
    Brands can have multiple locations (restaurants).
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # Brand contact info
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Brand visual identity
    logo = models.ImageField(upload_to="brand_logos/", blank=True, null=True)
    cover_image = models.ImageField(upload_to="brand_covers/", blank=True, null=True)
    primary_color = models.CharField(
        max_length=7, default="#10B981", help_text="Hex color code"
    )
    secondary_color = models.CharField(
        max_length=7, default="#059669", help_text="Hex color code"
    )

    # Brand settings
    default_timezone = models.CharField(max_length=50, default="Africa/Abidjan")
    default_currency = models.CharField(max_length=3, default="XOF")
    default_language = models.CharField(max_length=5, default="fr")

    # Plan and billing (for multi-location)
    plan_type = models.CharField(
        max_length=20,
        choices=[
            ("enterprise", "Enterprise"),
            ("franchise", "Franchise"),
        ],
        default="enterprise",
    )
    max_locations = models.PositiveIntegerField(default=10)

    # Owner info
    owner_name = models.CharField(max_length=200, blank=True)
    owner_email = models.EmailField(blank=True)
    owner_phone = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def location_count(self) -> int:
        """Count of active locations."""
        return self.locations.filter(is_active=True).count()


class BrandManager(BaseModel):
    """
    Users who can manage a brand across all locations.
    """

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="managers",
    )
    user = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="brand_management",
    )
    role = models.CharField(
        max_length=20,
        choices=[
            ("admin", "Brand Admin"),
            ("manager", "Brand Manager"),
            ("viewer", "Brand Viewer"),
        ],
        default="manager",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["brand", "user"]

    def __str__(self):
        return f"{self.user.name} - {self.brand.name}"


class LocationGroup(BaseModel):
    """
    Group locations by region, city, or custom grouping.
    """

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="location_groups",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        unique_together = ["brand", "name"]

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class LocationPriceOverride(BaseModel):
    """
    Price overrides for menu items at specific locations.
    """

    restaurant = models.ForeignKey(
        "authentication.Restaurant",
        on_delete=models.CASCADE,
        related_name="price_overrides",
    )
    menu_item = models.ForeignKey(
        "menu.MenuItem",
        on_delete=models.CASCADE,
        related_name="location_overrides",
    )
    price = models.DecimalField(max_digits=10, decimal_places=0)
    is_active = models.BooleanField(default=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ["restaurant", "menu_item"]

    def __str__(self):
        return f"{self.restaurant.name} - {self.menu_item.name}: {self.price}"


class LocationItemAvailability(BaseModel):
    """
    Control item availability at specific locations.
    """

    restaurant = models.ForeignKey(
        "authentication.Restaurant",
        on_delete=models.CASCADE,
        related_name="item_availability",
    )
    menu_item = models.ForeignKey(
        "menu.MenuItem",
        on_delete=models.CASCADE,
        related_name="location_availability",
    )
    is_available = models.BooleanField(default=True)
    unavailable_until = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ["restaurant", "menu_item"]

    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.restaurant.name} - {self.menu_item.name}: {status}"


class SharedMenu(BaseModel):
    """
    A menu template that can be shared across locations.
    """

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="shared_menus",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_default", "name"]
        unique_together = ["brand", "name"]

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class SharedMenuCategory(BaseModel):
    """
    Categories in a shared menu.
    """

    shared_menu = models.ForeignKey(
        SharedMenu,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="shared_menu/categories/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.shared_menu.name} - {self.name}"


class SharedMenuItem(BaseModel):
    """
    Items in a shared menu category.
    """

    category = models.ForeignKey(
        SharedMenuCategory,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=0)
    image = models.ImageField(upload_to="shared_menu/items/", blank=True, null=True)

    # Metadata
    allergens = models.JSONField(default=list, blank=True)
    dietary_tags = models.JSONField(default=list, blank=True)
    calories = models.PositiveIntegerField(null=True, blank=True)
    preparation_time = models.PositiveIntegerField(
        null=True, blank=True, help_text="Preparation time in minutes"
    )

    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.category.shared_menu.name} - {self.name}"


class LocationMenuSync(BaseModel):
    """
    Track which shared menus are synced to which locations.
    """

    restaurant = models.ForeignKey(
        "authentication.Restaurant",
        on_delete=models.CASCADE,
        related_name="menu_syncs",
    )
    shared_menu = models.ForeignKey(
        SharedMenu,
        on_delete=models.CASCADE,
        related_name="location_syncs",
    )
    last_synced_at = models.DateTimeField(default=timezone.now)
    auto_sync = models.BooleanField(
        default=True,
        help_text="Automatically sync menu changes to this location",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["restaurant", "shared_menu"]

    def __str__(self):
        return f"{self.restaurant.name} <- {self.shared_menu.name}"


class BrandReport(BaseModel):
    """
    Aggregated reports across all brand locations.
    """

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    date = models.DateField()
    report_type = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        default="daily",
    )

    # Aggregate metrics
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    total_customers = models.PositiveIntegerField(default=0)

    # Per-location breakdown (JSON)
    location_breakdown = models.JSONField(
        default=dict,
        help_text="Revenue and orders by location",
    )

    # Top performers
    top_items = models.JSONField(
        default=list,
        help_text="Top selling items across all locations",
    )
    top_locations = models.JSONField(
        default=list,
        help_text="Top performing locations",
    )

    class Meta:
        ordering = ["-date"]
        unique_together = ["brand", "date", "report_type"]

    def __str__(self):
        return f"{self.brand.name} - {self.date} ({self.report_type})"


class BrandAnnouncement(BaseModel):
    """
    Announcements from brand to all locations.
    """

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="announcements",
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        default="normal",
    )
    target_groups = models.ManyToManyField(
        LocationGroup,
        blank=True,
        related_name="announcements",
        help_text="Leave empty to target all locations",
    )
    publish_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-publish_at"]

    def __str__(self):
        return f"{self.brand.name} - {self.title}"

    @property
    def is_published(self) -> bool:
        """Check if announcement is currently published."""
        now = timezone.now()
        if self.publish_at > now:
            return False
        if self.expires_at and self.expires_at < now:
            return False
        return self.is_active
