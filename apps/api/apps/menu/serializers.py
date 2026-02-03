from rest_framework import serializers

from .models import Category, MenuItem, Modifier, ModifierOption


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


class MenuItemSerializer(serializers.ModelSerializer):
    """Serializer for menu items with nested modifiers (read-only nested)."""

    modifiers = ModifierSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = MenuItem
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
        ]

    def get_thumbnail_url(self, obj):
        """Return thumbnail URL if image exists."""
        if obj.image:
            try:
                return obj.thumbnail.url
            except Exception:
                return None
        return None


class MenuItemWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating menu items."""

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "image",
            "is_available",
        ]

    def validate_price(self, value):
        """Ensure price is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value

    def create(self, validated_data):
        """Set restaurant from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "restaurant"):
            validated_data["restaurant"] = request.user.restaurant
        return super().create(validated_data)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories with nested items (read-only nested)."""

    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "display_order", "is_visible", "items"]


class CategoryWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating categories."""

    class Meta:
        model = Category
        fields = ["id", "name", "display_order", "is_visible"]

    def create(self, validated_data):
        """Set restaurant from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "restaurant"):
            validated_data["restaurant"] = request.user.restaurant
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
        """Set restaurant from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "restaurant"):
            validated_data["restaurant"] = request.user.restaurant
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
        """Set restaurant from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "restaurant"):
            validated_data["restaurant"] = request.user.restaurant
        return super().create(validated_data)


class FullMenuSerializer(serializers.Serializer):
    """Serializer for the complete nested menu structure."""

    categories = CategorySerializer(many=True)
