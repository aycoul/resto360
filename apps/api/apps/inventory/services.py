"""
Atomic stock operations for inventory management.

These services ensure thread-safe stock updates using:
- select_for_update() for database-level locking
- F() expressions for atomic increments/decrements
- Immutable StockMovement records for audit trail
"""

import logging
from datetime import date
from decimal import Decimal

from django.db import models as db_models
from django.db import transaction
from django.db.models import BooleanField, Case, Count, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce, TruncDate

from .models import MovementReason, MovementType, StockItem, StockMovement

logger = logging.getLogger(__name__)


class InsufficientStockError(Exception):
    """Raised when attempting to deduct more stock than available."""

    def __init__(self, stock_item, requested, available):
        self.stock_item = stock_item
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for '{stock_item.name}': "
            f"requested {requested}, available {available}"
        )


def add_stock(
    stock_item_id,
    quantity,
    reason,
    user,
    notes="",
    reference=None,
):
    """
    Add stock to an item atomically.

    Args:
        stock_item_id: UUID of the stock item
        quantity: Amount to add (must be positive)
        reason: MovementReason choice (e.g., 'purchase', 'initial')
        user: User performing the action
        notes: Optional notes for the movement
        reference: Optional tuple of (reference_type, reference_id) for linking

    Returns:
        Updated StockItem instance
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive for add_stock")

    with transaction.atomic():
        # Lock the row for update to prevent race conditions
        stock_item = StockItem.all_objects.select_for_update().get(id=stock_item_id)

        # Use F() expression for atomic increment
        StockItem.all_objects.filter(id=stock_item_id).update(
            current_quantity=F("current_quantity") + Decimal(str(quantity))
        )

        # Refresh to get updated value
        stock_item.refresh_from_db()

        # Clear low stock alert if now above threshold
        if stock_item.low_stock_alert_sent:
            if (
                stock_item.low_stock_threshold is None
                or stock_item.current_quantity > stock_item.low_stock_threshold
            ):
                stock_item.low_stock_alert_sent = False
                stock_item.save(update_fields=["low_stock_alert_sent"])

        # Create immutable movement record
        reference_type = ""
        reference_id = None
        if reference:
            reference_type, reference_id = reference

        StockMovement.all_objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=Decimal(str(quantity)),
            movement_type=MovementType.IN,
            reason=reason,
            notes=notes,
            reference_type=reference_type,
            reference_id=reference_id,
            balance_after=stock_item.current_quantity,
            created_by=user,
        )

        logger.info(
            f"Added {quantity} {stock_item.unit} to '{stock_item.name}' "
            f"(new balance: {stock_item.current_quantity})"
        )

        return stock_item


def deduct_stock(
    stock_item_id,
    quantity,
    reason,
    user,
    notes="",
    reference=None,
):
    """
    Deduct stock from an item atomically.

    Args:
        stock_item_id: UUID of the stock item
        quantity: Amount to deduct (must be positive)
        reason: MovementReason choice (e.g., 'order_usage', 'waste')
        user: User performing the action
        notes: Optional notes for the movement
        reference: Optional tuple of (reference_type, reference_id) for linking

    Returns:
        Updated StockItem instance

    Raises:
        InsufficientStockError: If not enough stock available
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive for deduct_stock")

    with transaction.atomic():
        # Lock the row for update to prevent race conditions
        stock_item = StockItem.all_objects.select_for_update().get(id=stock_item_id)

        # Check if sufficient stock available
        if stock_item.current_quantity < Decimal(str(quantity)):
            raise InsufficientStockError(
                stock_item=stock_item,
                requested=quantity,
                available=stock_item.current_quantity,
            )

        # Use F() expression for atomic decrement
        StockItem.all_objects.filter(id=stock_item_id).update(
            current_quantity=F("current_quantity") - Decimal(str(quantity))
        )

        # Refresh to get updated value
        stock_item.refresh_from_db()

        # Create immutable movement record
        reference_type = ""
        reference_id = None
        if reference:
            reference_type, reference_id = reference

        StockMovement.all_objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=-Decimal(str(quantity)),  # Negative for deduction
            movement_type=MovementType.OUT,
            reason=reason,
            notes=notes,
            reference_type=reference_type,
            reference_id=reference_id,
            balance_after=stock_item.current_quantity,
            created_by=user,
        )

        # Check for low stock alert
        _check_low_stock_alert(stock_item)

        logger.info(
            f"Deducted {quantity} {stock_item.unit} from '{stock_item.name}' "
            f"(new balance: {stock_item.current_quantity})"
        )

        return stock_item


def adjust_stock(
    stock_item_id,
    new_quantity,
    reason,
    user,
    notes="",
):
    """
    Adjust stock to a specific quantity atomically.

    This is used for inventory corrections where the actual count
    differs from the system count.

    Args:
        stock_item_id: UUID of the stock item
        new_quantity: New quantity to set (must be non-negative)
        reason: MovementReason choice (typically 'correction')
        user: User performing the action
        notes: Optional notes explaining the adjustment

    Returns:
        Updated StockItem instance
    """
    if new_quantity < 0:
        raise ValueError("New quantity cannot be negative")

    with transaction.atomic():
        # Lock the row for update to prevent race conditions
        stock_item = StockItem.all_objects.select_for_update().get(id=stock_item_id)

        old_quantity = stock_item.current_quantity
        quantity_change = Decimal(str(new_quantity)) - old_quantity

        if quantity_change == 0:
            # No change needed
            return stock_item

        # Update to new quantity
        stock_item.current_quantity = Decimal(str(new_quantity))
        stock_item.save(update_fields=["current_quantity", "updated_at"])

        # Create immutable movement record
        StockMovement.all_objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=quantity_change,
            movement_type=MovementType.ADJUSTMENT,
            reason=reason,
            notes=notes,
            reference_type="",
            reference_id=None,
            balance_after=stock_item.current_quantity,
            created_by=user,
        )

        # Check for low stock alert
        _check_low_stock_alert(stock_item)

        logger.info(
            f"Adjusted '{stock_item.name}' from {old_quantity} to {new_quantity} "
            f"(change: {quantity_change:+})"
        )

        return stock_item


def _check_low_stock_alert(stock_item):
    """
    Check and update low stock alert status.

    Sets alert_sent=True if below threshold and not already sent.
    Triggers async Celery task for notification.
    Clears alert_sent if above threshold.

    Args:
        stock_item: StockItem instance (must be refreshed)
    """
    if stock_item.low_stock_threshold is None:
        return

    if stock_item.current_quantity <= stock_item.low_stock_threshold:
        if not stock_item.low_stock_alert_sent:
            # Mark alert as sent to prevent spam
            StockItem.objects.filter(id=stock_item.id).update(low_stock_alert_sent=True)

            # Trigger async notification
            from apps.inventory.tasks import send_low_stock_alert

            send_low_stock_alert.delay(
                stock_item_id=str(stock_item.id),
                current_quantity=float(stock_item.current_quantity),
                threshold=float(stock_item.low_stock_threshold),
            )

            logger.warning(
                f"Low stock alert: '{stock_item.name}' at {stock_item.current_quantity} "
                f"(threshold: {stock_item.low_stock_threshold})"
            )
    else:
        # Stock above threshold - clear alert flag if set
        if stock_item.low_stock_alert_sent:
            StockItem.objects.filter(id=stock_item.id).update(low_stock_alert_sent=False)


def deduct_ingredients_for_order(order):
    """
    Deduct all ingredients for a completed order.
    Processes each order item's recipe ingredients.

    Does NOT raise exceptions - logs warnings for insufficient stock
    but allows order completion to proceed.

    Args:
        order: Order instance with items to process
    """
    from apps.inventory.models import MenuItemIngredient

    with transaction.atomic():
        for order_item in order.items.select_related("menu_item"):
            if not order_item.menu_item:
                continue  # Menu item was deleted

            # Get recipe ingredients for this menu item
            ingredients = MenuItemIngredient.all_objects.filter(
                menu_item=order_item.menu_item,
                restaurant=order.restaurant,
            ).select_related("stock_item")

            if not ingredients.exists():
                logger.debug(
                    f"No ingredients mapped for menu item {order_item.menu_item.name} "
                    f"in order {order.id}"
                )
                continue

            for ingredient in ingredients:
                # Calculate quantity needed: required_per_unit * quantity_ordered
                quantity_needed = ingredient.quantity_required * order_item.quantity

                try:
                    deduct_stock(
                        stock_item_id=ingredient.stock_item_id,
                        quantity=quantity_needed,
                        reason=MovementReason.ORDER_USAGE,
                        user=order.cashier,
                        notes=f"Order #{order.order_number}",
                        reference=("Order", order.id),
                    )
                except InsufficientStockError:
                    # Log warning but continue - don't block order completion.
                    # Note: We do NOT create a movement record here because the
                    # database has a CHECK constraint preventing negative stock.
                    # The warning log serves as the audit trail for discrepancies.
                    # Managers should perform inventory reconciliation to fix counts.
                    logger.warning(
                        f"Insufficient stock for order {order.id}: "
                        f"{ingredient.stock_item.name} needed {quantity_needed}, "
                        f"available {ingredient.stock_item.current_quantity}. "
                        f"Skipping deduction - manual inventory adjustment required."
                    )


# =============================================================================
# Inventory Report Services
# =============================================================================


def get_current_stock_report(restaurant, include_inactive=False, low_stock_only=False):
    """
    Get current stock levels for all items.

    Args:
        restaurant: Restaurant instance
        include_inactive: Include inactive stock items
        low_stock_only: Only return items at or below threshold

    Returns:
        QuerySet of StockItems annotated with is_low_stock boolean
    """
    queryset = StockItem.objects.filter(restaurant=restaurant)

    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    # Annotate with low stock status
    queryset = queryset.annotate(
        is_low_stock=Case(
            When(
                low_stock_threshold__isnull=False,
                current_quantity__lte=F("low_stock_threshold"),
                then=Value(True),
            ),
            default=Value(False),
            output_field=BooleanField(),
        )
    )

    if low_stock_only:
        queryset = queryset.filter(is_low_stock=True)

    return queryset.order_by("name")


def get_movement_report(
    restaurant, start_date: date, end_date: date, stock_item_id=None
):
    """
    Generate stock movement report for date range.

    Args:
        restaurant: Restaurant instance
        start_date: Report start date (inclusive)
        end_date: Report end date (inclusive)
        stock_item_id: Optional - filter to specific stock item

    Returns:
        Dict with summary and daily breakdown
    """
    queryset = StockMovement.objects.filter(
        restaurant=restaurant,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    if stock_item_id:
        queryset = queryset.filter(stock_item_id=stock_item_id)

    # Summary by movement type
    summary = queryset.values("movement_type").annotate(
        total_quantity=Coalesce(Sum("quantity_change"), Value(Decimal("0"))),
        movement_count=Count("id"),
    )

    # Daily breakdown
    daily = (
        queryset.annotate(day=TruncDate("created_at"))
        .values("day", "movement_type")
        .annotate(
            total_quantity=Sum("quantity_change"),
            movement_count=Count("id"),
        )
        .order_by("day", "movement_type")
    )

    # By stock item
    by_item = (
        queryset.values(
            "stock_item__id",
            "stock_item__name",
            "stock_item__unit",
        )
        .annotate(
            total_in=Coalesce(
                Sum("quantity_change", filter=Q(movement_type="in")),
                Value(Decimal("0")),
            ),
            total_out=Coalesce(
                Sum("quantity_change", filter=Q(movement_type="out")),
                Value(Decimal("0")),
            ),
            net_change=Coalesce(Sum("quantity_change"), Value(Decimal("0"))),
            movement_count=Count("id"),
        )
        .order_by("stock_item__name")
    )

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "summary": list(summary),
        "daily": list(daily),
        "by_item": list(by_item),
    }


def get_stock_item_movement_history(stock_item, limit=100, offset=0):
    """
    Get movement history for a specific stock item.

    Args:
        stock_item: StockItem instance
        limit: Max records to return
        offset: Starting offset

    Returns:
        QuerySet of movements
    """
    movements = (
        StockMovement.objects.filter(stock_item=stock_item)
        .select_related("created_by")
        .order_by("-created_at")[offset : offset + limit]
    )

    return movements
