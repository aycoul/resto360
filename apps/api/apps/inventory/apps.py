from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """Configuration for the inventory app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inventory"
    verbose_name = "Inventory Management"

    def ready(self):
        """Register signal handlers when app is ready."""
        import apps.inventory.signals  # noqa: F401
