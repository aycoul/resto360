"""Signal handlers for inventory integration with orders."""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="orders.Order")
def handle_order_completion(sender, instance, created, **kwargs):
    """
    Deduct ingredients from stock when order is completed.

    Only triggers when:
    1. Order status is 'completed'
    2. completed_at was just set (not a re-save of already completed order)
    """
    from apps.orders.models import OrderStatus

    # Skip if not completed
    if instance.status != OrderStatus.COMPLETED:
        return

    # Skip if completed_at is not set (shouldn't happen, but guard)
    if not instance.completed_at:
        return

    # Check if this is the transition TO completed
    # Use update_fields if available to detect what changed
    update_fields = kwargs.get("update_fields")
    if update_fields is not None:
        # If update_fields specified but doesn't include status/completed_at, skip
        if "status" not in update_fields and "completed_at" not in update_fields:
            return

    # Avoid duplicate processing: check if movements already exist for this order
    from apps.inventory.models import StockMovement

    if StockMovement.all_objects.filter(
        reference_type="Order", reference_id=instance.id
    ).exists():
        logger.debug(f"Order {instance.id} already processed for inventory deduction")
        return

    # Perform deduction
    from apps.inventory.services import deduct_ingredients_for_order

    logger.info(f"Processing inventory deduction for order {instance.id}")
    try:
        deduct_ingredients_for_order(instance)
    except Exception as e:
        # Log error but don't block order completion
        logger.error(f"Inventory deduction failed for order {instance.id}: {e}")
