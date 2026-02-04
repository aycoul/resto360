from rest_framework import serializers

from .models import (
    Category,
    Product,
    MenuItem,  # Backwards compatibility alias
    MenuTheme,
    Modifier,
    ModifierOption,
    ALLERGEN_CHOICES,
    DIETARY_TAG_CHOICES,
    SPICE_LEVEL_CHOICES,
    MENU_TEMPLATE_CHOICES,
    FONT_CHOICES,
)


class ModifierOptionSerializer(serializers.ModelSerializer):
    """Serializer for modifier options (read-only nested)."""

    class Meta:
        model = ModifierOption
        fields = ["id", "name", "price_adjustment", "is_available", "display_order"]


class ModifierSerializer(serializers.ModelSerializer):
    """Serializer for modifiers with nested options (read-only nested)."""

    options = ModifierOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Modifier
        fields = [
            "id",
            "name",
            "required",
            "max_selections",
            "display_order",
            "options",
        ]


class NutritionSerializer(serializers.Serializer):
    """Nested serializer for nutrition information."""

    calories = serializers.IntegerField(allow_null=True)
    protein_grams = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    carbs_grams = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    fat_grams = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    fiber_grams = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    sodium_mg = serializers.IntegerField(allow_null=True)


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products (formerly menu items) with nested modifiers."""

    modifiers = ModifierSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)

    # Menu Metadata fields
    allergen_display = serializers.ListField(child=serializers.CharField(), read_only=True)
    dietary_tag_display = serializers.ListField(child=serializers.CharField(), read_only=True)
    spice_level_display = serializers.SerializerMethodField()
    nutrition = serializers.SerializerMethodField()
    has_nutrition_info = serializers.BooleanField(read_only=True)

    # Tax fields (computed)
    price_excluding_tax = serializers.IntegerField(read_only=True)
    tax_amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "price",
            "image",
            "thumbnail_url",
            "is_available",
            "modifiers",
            # Universal product fields
            "sku",
            "barcode",
            # Tax fields
            "tax_rate",
            "is_tax_inclusive",
            "tax_exempt",
            "price_excluding_tax",
            "tax_amount",
            # QR Reorder
            "reorder_qr_enabled",
            "reorder_quantity",
            # Food-specific Menu Metadata
            "allergens",
            "allergen_display",
            "dietary_tags",
            "dietary_tag_display",
            "spice_level",
            "spice_level_display",
            "prep_time_minutes",
            "ingredients",
            "nutrition",
            "has_nutrition_info",
        ]

    def get_thumbnail_url(self, obj):
        """Return thumbnail URL if image exists."""
        if obj.image:
            try:
                return obj.thumbnail.url
            except Exception:
                return None
        return None

    def get_spice_level_display(self, obj):
        """Return human-readable spice level."""
        spice_map = dict(SPICE_LEVEL_CHOICES)
        return spice_map.get(obj.spice_level, "Unknown")

    def get_nutrition(self, obj):
        """Return nutrition info as nested object."""
        if not obj.has_nutrition_info:
            return None
        return {
            "calories": obj.calories,
            "protein_grams": float(obj.protein_grams) if obj.protein_grams else None,
            "carbs_grams": float(obj.carbs_grams) if obj.carbs_grams else None,
            "fat_grams": float(obj.fat_grams) if obj.fat_grams else None,
            "fiber_grams": float(obj.fiber_grams) if obj.fiber_grams else None,
            "sodium_mg": obj.sodium_mg,
        }


# Backwards compatibility alias
MenuItemSerializer = ProductSerializer


class ProductWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products (formerly menu items)."""

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "image",
            "is_available",
            # Universal product fields
            "sku",
            "barcode",
            # Tax fields
            "tax_rate",
            "is_tax_inclusive",
            "tax_exempt",
            # QR Reorder
            "reorder_qr_enabled",
            "reorder_quantity",
            # Food-specific Menu Metadata
            "allergens",
            "dietary_tags",
            "spice_level",
            "prep_time_minutes",
            "ingredients",
            "calories",
            "protein_grams",
            "carbs_grams",
            "fat_grams",
            "fiber_grams",
            "sodium_mg",
        ]

    def validate_price(self, value):
        """Ensure price is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value

    def validate_allergens(self, value):
        """Validate allergen values."""
        valid_allergens = [choice[0] for choice in ALLERGEN_CHOICES]
        for allergen in value:
            if allergen not in valid_allergens:
                raise serializers.ValidationError(
                    f"Invalid allergen: {allergen}. Valid options: {valid_allergens}"
                )
        return value

    def validate_dietary_tags(self, value):
        """Validate dietary tag values."""
        valid_tags = [choice[0] for choice in DIETARY_TAG_CHOICES]
        for tag in value:
            if tag not in valid_tags:
                raise serializers.ValidationError(
                    f"Invalid dietary tag: {tag}. Valid options: {valid_tags}"
                )
        return value

    def validate_spice_level(self, value):
        """Validate spice level."""
        valid_levels = [choice[0] for choice in SPICE_LEVEL_CHOICES]
        if value not in valid_levels:
            raise serializers.ValidationError(
                f"Invalid spice level: {value}. Valid options: {valid_levels}"
            )
        return value

    def create(self, validated_data):
        """Set business from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "business"):
            validated_data["business"] = request.user.business
        return super().create(validated_data)


# Backwards compatibility alias
MenuItemWriteSerializer = ProductWriteSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories with nested items (read-only nested)."""

    items = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "display_order", "is_visible", "items"]


class CategoryWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating categories."""

    class Meta:
        model = Category
        fields = ["id", "name", "display_order", "is_visible"]

    def create(self, validated_data):
        """Set business from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "business"):
            validated_data["business"] = request.user.business
        return super().create(validated_data)


class ModifierWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating modifiers."""

    class Meta:
        model = Modifier
        fields = [
            "id",
            "menu_item",
            "name",
            "required",
            "max_selections",
            "display_order",
        ]

    def create(self, validated_data):
        """Set business from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "business"):
            validated_data["business"] = request.user.business
        return super().create(validated_data)


class ModifierOptionWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating modifier options."""

    class Meta:
        model = ModifierOption
        fields = [
            "id",
            "modifier",
            "name",
            "price_adjustment",
            "is_available",
            "display_order",
        ]

    def create(self, validated_data):
        """Set business from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "business"):
            validated_data["business"] = request.user.business
        return super().create(validated_data)


class FullMenuSerializer(serializers.Serializer):
    """Serializer for the complete nested menu structure."""

    categories = CategorySerializer(many=True)


class MenuMetadataChoicesSerializer(serializers.Serializer):
    """Serializer for available menu metadata options (allergens, dietary tags, etc.)."""

    allergens = serializers.SerializerMethodField()
    dietary_tags = serializers.SerializerMethodField()
    spice_levels = serializers.SerializerMethodField()

    def get_allergens(self, obj):
        """Return list of allergen choices."""
        return [{"value": choice[0], "label": choice[1]} for choice in ALLERGEN_CHOICES]

    def get_dietary_tags(self, obj):
        """Return list of dietary tag choices."""
        return [{"value": choice[0], "label": choice[1]} for choice in DIETARY_TAG_CHOICES]

    def get_spice_levels(self, obj):
        """Return list of spice level choices."""
        return [{"value": choice[0], "label": choice[1]} for choice in SPICE_LEVEL_CHOICES]


# Phase 8: Menu Theme Serializers
class MenuThemeSerializer(serializers.ModelSerializer):
    """Serializer for menu themes (read)."""

    logo_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    template_display = serializers.SerializerMethodField()
    heading_font_display = serializers.SerializerMethodField()
    body_font_display = serializers.SerializerMethodField()

    class Meta:
        model = MenuTheme
        fields = [
            "id",
            "is_active",
            "template",
            "template_display",
            "primary_color",
            "secondary_color",
            "background_color",
            "text_color",
            "heading_font",
            "heading_font_display",
            "body_font",
            "body_font_display",
            "logo",
            "logo_url",
            "cover_image",
            "cover_image_url",
            "logo_position",
            "show_prices",
            "show_descriptions",
            "show_images",
            "compact_mode",
        ]

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        return None

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def get_template_display(self, obj):
        return dict(MENU_TEMPLATE_CHOICES).get(obj.template, obj.template)

    def get_heading_font_display(self, obj):
        return dict(FONT_CHOICES).get(obj.heading_font, obj.heading_font)

    def get_body_font_display(self, obj):
        return dict(FONT_CHOICES).get(obj.body_font, obj.body_font)


class MenuThemeWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating menu themes."""

    class Meta:
        model = MenuTheme
        fields = [
            "id",
            "is_active",
            "template",
            "primary_color",
            "secondary_color",
            "background_color",
            "text_color",
            "heading_font",
            "body_font",
            "logo",
            "cover_image",
            "logo_position",
            "show_prices",
            "show_descriptions",
            "show_images",
            "compact_mode",
        ]

    def validate_primary_color(self, value):
        """Validate hex color format."""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be a valid hex code (e.g., #059669)")
        return value

    validate_secondary_color = validate_primary_color
    validate_background_color = validate_primary_color
    validate_text_color = validate_primary_color

    def create(self, validated_data):
        """Set business from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "business"):
            validated_data["business"] = request.user.business
        return super().create(validated_data)


class ThemeChoicesSerializer(serializers.Serializer):
    """Serializer for available theme options."""

    templates = serializers.SerializerMethodField()
    fonts = serializers.SerializerMethodField()

    def get_templates(self, obj):
        return [{"value": choice[0], "label": choice[1]} for choice in MENU_TEMPLATE_CHOICES]

    def get_fonts(self, obj):
        return [{"value": choice[0], "label": choice[1]} for choice in FONT_CHOICES]
