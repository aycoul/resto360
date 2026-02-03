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
    """Abstract base for tenant-scoped models."""

    restaurant = models.ForeignKey(
        "authentication.Restaurant",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True
