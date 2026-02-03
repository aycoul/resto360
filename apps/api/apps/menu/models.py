from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from apps.core.managers import TenantManager
from apps.core.models import TenantModel


class Category(TenantModel):
    """Menu category for organizing items (e.g., Entrees, Drinks, Desserts)."""

    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class MenuItem(TenantModel):
    """A menu item with price and optional image."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField(
        help_text="Price in XOF (no decimals for CFA franc)"
    )
    image = models.ImageField(upload_to="menu_items/", blank=True, null=True)
    thumbnail = ImageSpecField(
        source="image",
        processors=[ResizeToFill(300, 300)],
        format="JPEG",
        options={"quality": 85},
    )
    is_available = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Modifier(TenantModel):
    """A modifier group for a menu item (e.g., Size, Extras, Toppings)."""

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="modifiers",
    )
    name = models.CharField(max_length=100)
    required = models.BooleanField(
        default=False,
        help_text="Customer must select at least one option",
    )
    max_selections = models.PositiveIntegerField(
        default=1,
        help_text="Maximum options customer can select (0 = unlimited)",
    )
    display_order = models.PositiveIntegerField(default=0)

    objects = TenantManager()

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.menu_item.name} - {self.name}"


class ModifierOption(TenantModel):
    """An option within a modifier (e.g., Small, Medium, Large for Size)."""

    modifier = models.ForeignKey(
        Modifier,
        on_delete=models.CASCADE,
        related_name="options",
    )
    name = models.CharField(max_length=100)
    price_adjustment = models.IntegerField(
        default=0,
        help_text="Price adjustment in XOF (can be negative for discounts)",
    )
    is_available = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    objects = TenantManager()

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.modifier.name} - {self.name}"
