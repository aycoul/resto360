"""Django app configuration for delivery."""

from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    """Configuration for delivery app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.delivery"
    verbose_name = "Delivery"
