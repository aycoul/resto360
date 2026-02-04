import uuid

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Abstract base for all models with UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(BaseModel):
    """
    Abstract base for tenant-scoped models.

    All models that belong to a specific business should inherit from this.
    The 'business' field provides multi-tenant isolation via TenantManager.

    Note: The 'restaurant' property is provided for backwards compatibility
    during the transition from RESTO360 to BIZ360.
    """

    business = models.ForeignKey(
        "authentication.Business",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True

    @property
    def restaurant(self):
        """Backwards compatibility: alias for business."""
        return self.business

    @restaurant.setter
    def restaurant(self, value):
        """Backwards compatibility: alias for business."""
        self.business = value
