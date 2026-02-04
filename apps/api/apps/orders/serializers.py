"""Order serializers for BIZ360 (formerly RESTO360)."""

from rest_framework import serializers

from apps.menu.models import Product, ModifierOption

from .models import Order, OrderItem, OrderItemModifier, OrderStatus, OrderType, DGISubmissionStatus, Table
from .services import get_next_order_number


class TableSerializer(serializers.ModelSerializer):
    """Serializer for tables."""

    class Meta:
        model = Table
        fields = ["id", "number", "capacity", "is_active"]

    def create(self, validated_data):
        """Set business from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "business"):
            validated_data["business"] = request.user.business
        return super().create(validated_data)


class OrderItemModifierSerializer(serializers.ModelSerializer):
    """Serializer for order item modifiers (read-only)."""

    class Meta:
        model = OrderItemModifier
        fields = ["id", "modifier_option", "name", "price_adjustment"]


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items (read-only)."""

    modifiers = OrderItemModifierSerializer(many=True, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "name",
            "unit_price",
            "quantity",
            "modifiers_total",
            "line_total",
            "notes",
            "modifiers",
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders (read)."""

    items = OrderItemSerializer(many=True, read_only=True)
    table_number = serializers.CharField(source="table.number", read_only=True)
    cashier_name = serializers.CharField(source="cashier.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_type_display = serializers.CharField(source="get_order_type_display", read_only=True)
    dgi_status_display = serializers.CharField(source="get_dgi_submission_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "invoice_number",
            "order_type",
            "order_type_display",
            "status",
            "status_display",
            "table",
            "table_number",
            "cashier",
            "cashier_name",
            "customer_name",
            "customer_phone",
            "customer_email",
            "customer_tax_id",
            "customer_address",
            "notes",
            "subtotal",
            "subtotal_ht",
            "tax_rate",
            "tax_amount",
            "discount",
            "total",
            # DGI compliance
            "dgi_submission_status",
            "dgi_status_display",
            "dgi_reference",
            "dgi_submitted_at",
            "dgi_qr_code",
            # Timestamps
            "created_at",
            "updated_at",
            "completed_at",
            "cancelled_at",
            "cancelled_reason",
            "items",
        ]


# --- Create serializers ---


class OrderItemModifierCreateSerializer(serializers.Serializer):
    """Serializer for creating order item modifiers."""

    modifier_option_id = serializers.UUIDField()


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items."""

    menu_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    modifiers = OrderItemModifierCreateSerializer(many=True, required=False, default=list)


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders."""

    order_type = serializers.ChoiceField(choices=OrderType.choices)
    table_id = serializers.UUIDField(required=False, allow_null=True)
    customer_name = serializers.CharField(required=False, allow_blank=True, default="")
    customer_phone = serializers.CharField(required=False, allow_blank=True, default="")
    customer_email = serializers.EmailField(required=False, allow_blank=True, default="")
    customer_tax_id = serializers.CharField(required=False, allow_blank=True, default="")
    customer_address = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    discount = serializers.IntegerField(min_value=0, default=0)
    items = OrderItemCreateSerializer(many=True, min_length=1)
    generate_invoice = serializers.BooleanField(default=False, required=False)

    def validate(self, data):
        """Validate order data."""
        # Require table for dine-in orders
        if data["order_type"] == "dine_in" and not data.get("table_id"):
            raise serializers.ValidationError({
                "table_id": "Table is required for dine-in orders."
            })

        # Validate table exists and belongs to business
        if data.get("table_id"):
            request = self.context.get("request")
            if request and hasattr(request.user, "business"):
                try:
                    table = Table.objects.get(
                        id=data["table_id"],
                        business=request.user.business,
                        is_active=True,
                    )
                    data["table"] = table
                except Table.DoesNotExist:
                    raise serializers.ValidationError({
                        "table_id": "Table not found or inactive."
                    })

        # Validate products exist and belong to business
        request = self.context.get("request")
        if request and hasattr(request.user, "business"):
            business = request.user.business
            for item_data in data["items"]:
                try:
                    product = Product.objects.get(
                        id=item_data["menu_item_id"],
                        business=business,
                    )
                    item_data["menu_item"] = product
                except Product.DoesNotExist:
                    raise serializers.ValidationError({
                        "items": f"Product {item_data['menu_item_id']} not found."
                    })

                # Validate modifier options
                for mod_data in item_data.get("modifiers", []):
                    try:
                        mod_option = ModifierOption.objects.get(
                            id=mod_data["modifier_option_id"],
                            business=business,
                        )
                        mod_data["modifier_option"] = mod_option
                    except ModifierOption.DoesNotExist:
                        raise serializers.ValidationError({
                            "items": f"Modifier option {mod_data['modifier_option_id']} not found."
                        })

        return data

    def create(self, validated_data):
        """Create order with items and modifiers."""
        request = self.context.get("request")
        business = request.user.business
        cashier = request.user

        # Get next order number
        order_number = get_next_order_number(business)

        # Create order
        order = Order.objects.create(
            business=business,
            order_number=order_number,
            order_type=validated_data["order_type"],
            table=validated_data.get("table"),
            cashier=cashier,
            customer_name=validated_data.get("customer_name", ""),
            customer_phone=validated_data.get("customer_phone", ""),
            customer_email=validated_data.get("customer_email", ""),
            customer_tax_id=validated_data.get("customer_tax_id", ""),
            customer_address=validated_data.get("customer_address", ""),
            notes=validated_data.get("notes", ""),
            discount=validated_data.get("discount", 0),
            tax_rate=business.default_tax_rate,
        )

        subtotal = 0

        # Create order items
        for item_data in validated_data["items"]:
            product = item_data["menu_item"]
            quantity = item_data["quantity"]

            # Calculate modifiers total for this item
            modifiers_total = 0
            for mod_data in item_data.get("modifiers", []):
                mod_option = mod_data["modifier_option"]
                modifiers_total += mod_option.price_adjustment

            line_total = max(0, (product.price + modifiers_total) * quantity)

            order_item = OrderItem.objects.create(
                business=business,
                order=order,
                menu_item=product,
                name=product.name,
                unit_price=product.price,
                quantity=quantity,
                modifiers_total=modifiers_total,
                line_total=line_total,
                notes=item_data.get("notes", ""),
            )

            # Create order item modifiers
            for mod_data in item_data.get("modifiers", []):
                mod_option = mod_data["modifier_option"]
                OrderItemModifier.objects.create(
                    business=business,
                    order_item=order_item,
                    modifier_option=mod_option,
                    name=mod_option.name,
                    price_adjustment=mod_option.price_adjustment,
                )

            subtotal += line_total

        # Update order totals (includes tax calculation)
        order.subtotal = subtotal
        order.calculate_totals()

        # Generate invoice number if requested or if DGI is enabled
        if validated_data.get("generate_invoice") or business.is_dgi_enabled:
            order.generate_invoice_number()
            if business.is_dgi_enabled:
                order.dgi_submission_status = DGISubmissionStatus.PENDING

        order.save()

        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status."""

    status = serializers.ChoiceField(choices=OrderStatus.choices)
    cancelled_reason = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        """Validate status transition."""
        order = self.context.get("order")
        new_status = data["status"]

        # Define valid status transitions
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
            OrderStatus.COMPLETED: [],  # Terminal state
            OrderStatus.CANCELLED: [],  # Terminal state
        }

        if new_status not in valid_transitions.get(order.status, []):
            raise serializers.ValidationError({
                "status": f"Cannot transition from {order.status} to {new_status}."
            })

        # Require reason for cancellation
        if new_status == OrderStatus.CANCELLED and not data.get("cancelled_reason"):
            raise serializers.ValidationError({
                "cancelled_reason": "Reason is required when cancelling an order."
            })

        return data

    def update(self, order, validated_data):
        """Update order status."""
        order.status = validated_data["status"]
        if validated_data.get("cancelled_reason"):
            order.cancelled_reason = validated_data["cancelled_reason"]
        order.save()
        return order


class GuestOrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating guest orders from public QR menu.
    No authentication required - uses business from context.
    """

    order_type = serializers.ChoiceField(choices=[
        ("dine_in", "Dine In"),
        ("takeaway", "Takeaway"),
        ("in_store", "In Store"),
    ])
    table = serializers.CharField(required=False, allow_blank=True, default="")
    customer_name = serializers.CharField(required=True, max_length=100)
    customer_phone = serializers.CharField(required=False, allow_blank=True, default="")
    customer_email = serializers.EmailField(required=False, allow_blank=True, default="")
    items = OrderItemCreateSerializer(many=True, min_length=1)

    def validate(self, data):
        """Validate guest order data."""
        # Require table info for dine-in orders
        if data["order_type"] == "dine_in" and not data.get("table"):
            raise serializers.ValidationError({
                "table": "Table number is required for dine-in orders."
            })

        # Get business from context
        business = self.context.get("business") or self.context.get("restaurant")
        if not business:
            raise serializers.ValidationError("Business context is required.")

        # Validate products exist and belong to business
        for item_data in data["items"]:
            try:
                product = Product.all_objects.get(
                    id=item_data["menu_item_id"],
                    business=business,
                    is_available=True,
                )
                item_data["menu_item"] = product
            except Product.DoesNotExist:
                raise serializers.ValidationError({
                    "items": f"Product {item_data['menu_item_id']} not found or unavailable."
                })

            # Validate modifier options
            for mod_data in item_data.get("modifiers", []):
                try:
                    mod_option = ModifierOption.all_objects.get(
                        id=mod_data["modifier_option_id"],
                        business=business,
                        is_available=True,
                    )
                    mod_data["modifier_option"] = mod_option
                except ModifierOption.DoesNotExist:
                    raise serializers.ValidationError({
                        "items": f"Modifier option {mod_data['modifier_option_id']} not found or unavailable."
                    })

        return data

    def create(self, validated_data):
        """Create guest order with items and modifiers."""
        business = self.context.get("business") or self.context.get("restaurant")

        # Get next order number
        order_number = get_next_order_number(business)

        # Create order (no cashier for guest orders)
        order = Order.objects.create(
            business=business,
            order_number=order_number,
            order_type=validated_data["order_type"],
            table=None,  # Guest orders use customer-provided table string in notes
            cashier=None,  # No cashier for guest orders
            customer_name=validated_data.get("customer_name", ""),
            customer_phone=validated_data.get("customer_phone", ""),
            customer_email=validated_data.get("customer_email", ""),
            notes=f"Table: {validated_data.get('table', '')}" if validated_data.get("table") else "",
            discount=0,
            tax_rate=business.default_tax_rate,
        )

        subtotal = 0

        # Create order items
        for item_data in validated_data["items"]:
            product = item_data["menu_item"]
            quantity = item_data["quantity"]

            # Calculate modifiers total for this item
            modifiers_total = 0
            for mod_data in item_data.get("modifiers", []):
                mod_option = mod_data["modifier_option"]
                modifiers_total += mod_option.price_adjustment

            line_total = max(0, (product.price + modifiers_total) * quantity)

            order_item = OrderItem.objects.create(
                business=business,
                order=order,
                menu_item=product,
                name=product.name,
                unit_price=product.price,
                quantity=quantity,
                modifiers_total=modifiers_total,
                line_total=line_total,
                notes=item_data.get("notes", ""),
            )

            # Create order item modifiers
            for mod_data in item_data.get("modifiers", []):
                mod_option = mod_data["modifier_option"]
                OrderItemModifier.objects.create(
                    business=business,
                    order_item=order_item,
                    modifier_option=mod_option,
                    name=mod_option.name,
                    price_adjustment=mod_option.price_adjustment,
                )

            subtotal += line_total

        # Update order totals (includes tax calculation)
        order.subtotal = subtotal
        order.calculate_totals()
        order.save()

        return order
