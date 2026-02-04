from django.db import models
from django.contrib.postgres.fields import ArrayField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from apps.core.managers import TenantManager
from apps.core.models import TenantModel


# Standard 14 major allergens (EU regulation)
ALLERGEN_CHOICES = [
    ("celery", "Celery"),
    ("gluten", "Gluten"),
    ("crustaceans", "Crustaceans"),
    ("eggs", "Eggs"),
    ("fish", "Fish"),
    ("lupin", "Lupin"),
    ("milk", "Milk"),
    ("molluscs", "Molluscs"),
    ("mustard", "Mustard"),
    ("nuts", "Tree Nuts"),
    ("peanuts", "Peanuts"),
    ("sesame", "Sesame"),
    ("soya", "Soya"),
    ("sulphites", "Sulphites"),
]

# Dietary tags
DIETARY_TAG_CHOICES = [
    ("vegan", "Vegan"),
    ("vegetarian", "Vegetarian"),
    ("gluten_free", "Gluten-Free"),
    ("dairy_free", "Dairy-Free"),
    ("halal", "Halal"),
    ("kosher", "Kosher"),
    ("keto", "Keto-Friendly"),
    ("low_carb", "Low Carb"),
    ("nut_free", "Nut-Free"),
    ("organic", "Organic"),
]

# Spice levels
SPICE_LEVEL_CHOICES = [
    (0, "Not Spicy"),
    (1, "Mild"),
    (2, "Medium"),
    (3, "Hot"),
    (4, "Very Hot"),
]


class Category(TenantModel):
    """Menu category for organizing items (e.g., Entrees, Drinks, Desserts)."""

    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(TenantModel):
    """
    Universal product model (formerly MenuItem).

    Supports all business types: restaurant menu items, retail products,
    pharmacy medications, etc. Food-specific fields are conditional on
    the business type.
    """

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
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    thumbnail = ImageSpecField(
        source="image",
        processors=[ResizeToFill(300, 300)],
        format="JPEG",
        options={"quality": 85},
    )
    is_available = models.BooleanField(default=True)

    # Universal product fields (NEW)
    sku = models.CharField(
        max_length=50,
        blank=True,
        help_text="Stock Keeping Unit - internal product code",
    )
    barcode = models.CharField(
        max_length=50,
        blank=True,
        help_text="Barcode (EAN, UPC, etc.) for scanning",
    )

    # Tax handling (NEW)
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        help_text="Tax rate for this product (default: Ivory Coast VAT 18%)",
    )
    is_tax_inclusive = models.BooleanField(
        default=True,
        help_text="Is the price inclusive of tax (TTC)?",
    )
    tax_exempt = models.BooleanField(
        default=False,
        help_text="Is this product exempt from tax?",
    )

    # QR Reorder feature (NEW)
    reorder_qr_enabled = models.BooleanField(
        default=False,
        help_text="Enable QR code reordering for this product",
    )
    reorder_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Default quantity for QR reorder",
    )

    # Food-specific fields (conditional on business_type)
    allergens = ArrayField(
        models.CharField(max_length=20, choices=ALLERGEN_CHOICES),
        blank=True,
        default=list,
        help_text="List of allergens present in this item (food only)",
    )
    dietary_tags = ArrayField(
        models.CharField(max_length=20, choices=DIETARY_TAG_CHOICES),
        blank=True,
        default=list,
        help_text="Dietary certifications/tags for this item (food only)",
    )
    spice_level = models.PositiveSmallIntegerField(
        choices=SPICE_LEVEL_CHOICES,
        default=0,
        help_text="Spice/heat level of the dish (food only)",
    )
    prep_time_minutes = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text="Estimated preparation time in minutes (food only)",
    )

    # Nutrition information (per serving, food only)
    calories = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Calories per serving (kcal)",
    )
    protein_grams = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Protein per serving (grams)",
    )
    carbs_grams = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Carbohydrates per serving (grams)",
    )
    fat_grams = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Fat per serving (grams)",
    )
    fiber_grams = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Fiber per serving (grams)",
    )
    sodium_mg = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Sodium per serving (milligrams)",
    )

    # Ingredients list (for display to customers)
    ingredients = models.TextField(
        blank=True,
        help_text="Comma-separated list of main ingredients",
    )

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.name

    @property
    def has_nutrition_info(self):
        """Check if any nutrition information is provided."""
        return any([
            self.calories,
            self.protein_grams,
            self.carbs_grams,
            self.fat_grams,
        ])

    @property
    def allergen_display(self):
        """Return human-readable allergen names."""
        allergen_map = dict(ALLERGEN_CHOICES)
        return [allergen_map.get(a, a) for a in self.allergens]

    @property
    def dietary_tag_display(self):
        """Return human-readable dietary tag names."""
        tag_map = dict(DIETARY_TAG_CHOICES)
        return [tag_map.get(t, t) for t in self.dietary_tags]

    @property
    def price_excluding_tax(self):
        """Calculate price excluding tax (HT) if price is tax-inclusive."""
        if self.tax_exempt or not self.is_tax_inclusive:
            return self.price
        from decimal import Decimal
        tax_divisor = 1 + (self.tax_rate / Decimal("100"))
        return int(Decimal(self.price) / tax_divisor)

    @property
    def tax_amount(self):
        """Calculate tax amount for this product."""
        if self.tax_exempt:
            return 0
        return self.price - self.price_excluding_tax


# Backwards compatibility alias
MenuItem = Product


# Phase 8: Menu Theme/Template Choices
MENU_TEMPLATE_CHOICES = [
    ("minimalist", "Minimalist"),
    ("elegant", "Elegant"),
    ("modern", "Modern"),
    ("casual", "Casual"),
    ("fine_dining", "Fine Dining"),
    ("vibrant", "Vibrant"),
]

FONT_CHOICES = [
    ("inter", "Inter"),
    ("playfair", "Playfair Display"),
    ("roboto", "Roboto"),
    ("lato", "Lato"),
    ("montserrat", "Montserrat"),
    ("merriweather", "Merriweather"),
    ("open_sans", "Open Sans"),
    ("poppins", "Poppins"),
]


class MenuTheme(TenantModel):
    """Theme configuration for public menu display."""

    is_active = models.BooleanField(
        default=True,
        help_text="Only one theme can be active per restaurant",
    )

    # Template selection
    template = models.CharField(
        max_length=20,
        choices=MENU_TEMPLATE_CHOICES,
        default="minimalist",
    )

    # Colors (hex codes)
    primary_color = models.CharField(
        max_length=7,
        default="#059669",
        help_text="Primary brand color (hex, e.g., #059669)",
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#14b8a6",
        help_text="Secondary color for accents",
    )
    background_color = models.CharField(
        max_length=7,
        default="#ffffff",
        help_text="Page background color",
    )
    text_color = models.CharField(
        max_length=7,
        default="#111827",
        help_text="Main text color",
    )

    # Typography
    heading_font = models.CharField(
        max_length=20,
        choices=FONT_CHOICES,
        default="inter",
    )
    body_font = models.CharField(
        max_length=20,
        choices=FONT_CHOICES,
        default="inter",
    )

    # Logo and Images
    logo = models.ImageField(
        upload_to="menu_themes/logos/",
        blank=True,
        null=True,
    )
    cover_image = models.ImageField(
        upload_to="menu_themes/covers/",
        blank=True,
        null=True,
        help_text="Hero image for menu header",
    )
    logo_position = models.CharField(
        max_length=10,
        choices=[
            ("left", "Left"),
            ("center", "Center"),
            ("right", "Right"),
        ],
        default="center",
    )

    # Layout options
    show_prices = models.BooleanField(default=True)
    show_descriptions = models.BooleanField(default=True)
    show_images = models.BooleanField(default=True)
    compact_mode = models.BooleanField(
        default=False,
        help_text="Display items in a more compact format",
    )

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        verbose_name = "Menu Theme"
        verbose_name_plural = "Menu Themes"

    def __str__(self):
        return f"{self.business.name} - {self.template}"

    def save(self, *args, **kwargs):
        # Ensure only one active theme per business
        if self.is_active:
            MenuTheme.all_objects.filter(
                business=self.business, is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


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

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
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

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.modifier.name} - {self.name}"
