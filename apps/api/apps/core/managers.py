from django.db import models

from .context import get_current_restaurant


class TenantManager(models.Manager):
    """Auto-filters queryset by current tenant."""

    def get_queryset(self):
        qs = super().get_queryset()
        restaurant = get_current_restaurant()
        if restaurant:
            return qs.filter(restaurant=restaurant)
        return qs
