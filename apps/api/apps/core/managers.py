from django.db import models

from .context import get_current_business


class TenantManager(models.Manager):
    """Auto-filters queryset by current tenant (business)."""

    def get_queryset(self):
        qs = super().get_queryset()
        business = get_current_business()
        if business:
            return qs.filter(business=business)
        return qs
