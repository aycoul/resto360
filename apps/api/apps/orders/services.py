"""Order services for RESTO360."""

from django.db import transaction
from django.utils import timezone

from .models import DailySequence


def get_next_order_number(restaurant):
    """
    Get the next order number for a restaurant.

    Uses SELECT FOR UPDATE to ensure atomic increment even under
    concurrent order creation. Order numbers reset daily.

    Args:
        restaurant: Restaurant instance

    Returns:
        int: Next order number for today
    """
    today = timezone.localdate()

    with transaction.atomic():
        # Use select_for_update to lock the row
        sequence, created = DailySequence.objects.select_for_update().get_or_create(
            restaurant=restaurant,
            date=today,
            defaults={"last_number": 0},
        )

        sequence.last_number += 1
        sequence.save(update_fields=["last_number", "updated_at"])

        return sequence.last_number


def calculate_order_totals(order):
    """
    Calculate and update order subtotal and total.

    Args:
        order: Order instance
    """
    # First, recalculate each item's line total
    for item in order.items.all():
        item.calculate_line_total()
        item.save(update_fields=["modifiers_total", "line_total", "updated_at"])

    # Then calculate order totals
    order.calculate_totals()
    order.save(update_fields=["subtotal", "total", "updated_at"])
