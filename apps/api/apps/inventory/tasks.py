"""Celery tasks for inventory notifications."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_low_stock_alert(self, stock_item_id: str, current_quantity: float, threshold: float):
    """
    Send low stock alert notification.

    This is a placeholder that logs the alert. In production, this would:
    - Send email to business managers
    - Push notification via WebSocket
    - Send SMS if critical

    Args:
        stock_item_id: UUID of the stock item
        current_quantity: Current stock level
        threshold: Configured threshold
    """
    from apps.inventory.models import StockItem

    try:
        stock_item = StockItem.all_objects.select_related("business").get(id=stock_item_id)

        alert_message = (
            f"LOW STOCK ALERT: {stock_item.name} at {stock_item.business.name}\n"
            f"Current: {current_quantity} {stock_item.unit}\n"
            f"Threshold: {threshold} {stock_item.unit}"
        )

        # Log the alert (replace with actual notification in production)
        logger.warning(alert_message)

        # Future: Send to managers via email/push
        # Future: Broadcast via WebSocket to dashboard

        return {"status": "sent", "stock_item": str(stock_item_id)}

    except StockItem.DoesNotExist:
        logger.error(f"Stock item {stock_item_id} not found for alert")
        return {"status": "error", "reason": "stock_item_not_found"}
    except Exception as e:
        logger.error(f"Failed to send low stock alert: {e}")
        self.retry(exc=e)
