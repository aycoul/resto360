from decimal import Decimal

from rest_framework import serializers

from .models import MenuItemIngredient, MovementReason, StockItem, StockMovement


class StockItemSerializer(serializers.ModelSerializer):
    """Full serializer for StockItem (detail view)."""

    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockItem
        fields = [
            "id",
            "name",
            "sku",
            "unit",
            "current_quantity",
            "low_stock_threshold",
            "is_low_stock",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "current_quantity", "created_at", "updated_at"]

    def create(self, validated_data):
        """Set restaurant from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "restaurant"):
            validated_data["restaurant"] = request.user.restaurant
        return super().create(validated_data)


class StockItemListSerializer(serializers.ModelSerializer):
    """Condensed serializer for StockItem list views."""

    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockItem
        fields = [
            "id",
            "name",
            "sku",
            "unit",
            "current_quantity",
            "is_low_stock",
            "is_active",
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for StockMovement (read-only - created via services)."""

    stock_item_name = serializers.CharField(source="stock_item.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "stock_item",
            "stock_item_name",
            "quantity_change",
            "movement_type",
            "reason",
            "notes",
            "reference_type",
            "reference_id",
            "balance_after",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = fields  # All fields read-only

    def get_created_by_name(self, obj):
        """Return the name of the user who created the movement."""
        if obj.created_by:
            return obj.created_by.name
        return None


class AddStockSerializer(serializers.Serializer):
    """Serializer for add_stock action."""

    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        min_value=Decimal("0.0001"),
        help_text="Amount to add (must be positive)",
    )
    reason = serializers.ChoiceField(
        choices=[
            (MovementReason.PURCHASE, "Purchase"),
            (MovementReason.INITIAL, "Initial Stock"),
            (MovementReason.CORRECTION, "Correction"),
            (MovementReason.TRANSFER, "Transfer"),
        ],
        help_text="Reason for adding stock",
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional notes",
    )


class AdjustStockSerializer(serializers.Serializer):
    """Serializer for adjust stock action."""

    new_quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        min_value=Decimal("0"),
        help_text="New quantity to set (must be non-negative)",
    )
    reason = serializers.ChoiceField(
        choices=[
            (MovementReason.CORRECTION, "Correction"),
            (MovementReason.WASTE, "Waste"),
            (MovementReason.THEFT, "Theft"),
        ],
        help_text="Reason for adjustment",
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional notes explaining the adjustment",
    )


class MenuItemIngredientSerializer(serializers.ModelSerializer):
    """Serializer for recipe ingredient mapping."""

    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    stock_item_name = serializers.CharField(source="stock_item.name", read_only=True)
    stock_item_unit = serializers.CharField(source="stock_item.unit", read_only=True)

    class Meta:
        model = MenuItemIngredient
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "stock_item",
            "stock_item_name",
            "stock_item_unit",
            "quantity_required",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """Ensure menu_item and stock_item belong to same restaurant."""
        menu_item = data.get("menu_item")
        stock_item = data.get("stock_item")

        if menu_item and stock_item:
            if menu_item.restaurant_id != stock_item.restaurant_id:
                raise serializers.ValidationError(
                    "Menu item and stock item must belong to the same restaurant"
                )
        return data
