"""AI models for tracking jobs and usage."""

import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.core.models import TenantModel


class AIJobStatus(models.TextChoices):
    """Status choices for AI jobs."""

    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class AIJobType(models.TextChoices):
    """Types of AI jobs."""

    DESCRIPTION = "description", "Generate Description"
    PHOTO_ANALYSIS = "photo_analysis", "Photo Analysis"
    MENU_OCR = "menu_ocr", "Menu OCR Import"
    BULK_IMPORT = "bulk_import", "Bulk Import"
    TRANSLATION = "translation", "Translation"
    PRICE_SUGGESTION = "price_suggestion", "Price Suggestion"


class AIJob(TenantModel):
    """
    Track AI processing jobs.

    Allows async processing via Celery and provides job status to frontend.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_type = models.CharField(max_length=20, choices=AIJobType.choices)
    status = models.CharField(
        max_length=20,
        choices=AIJobStatus.choices,
        default=AIJobStatus.PENDING,
    )

    # Input data (JSON)
    input_data = models.JSONField(default=dict, blank=True)

    # Output data (JSON) - filled when completed
    output_data = models.JSONField(default=dict, blank=True)

    # Error message if failed
    error_message = models.TextField(blank=True)

    # Processing metadata
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Celery task ID for tracking
    celery_task_id = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "AI Job"
        verbose_name_plural = "AI Jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.job_type} - {self.status}"


class AIUsage(TenantModel):
    """
    Track AI API usage for billing/quotas.

    Records each AI API call with token counts and costs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        AIJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usage_records",
    )
    job_type = models.CharField(max_length=20, choices=AIJobType.choices)

    # API details
    model_used = models.CharField(max_length=50)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)

    # Cost tracking (in USD cents)
    estimated_cost_cents = models.IntegerField(default=0)

    class Meta:
        verbose_name = "AI Usage"
        verbose_name_plural = "AI Usage Records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.job_type} - {self.total_tokens} tokens"


class MenuImportBatch(TenantModel):
    """
    Track bulk menu imports.

    Stores imported items before they are confirmed and added to menu.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_type = models.CharField(
        max_length=20,
        choices=[
            ("csv", "CSV File"),
            ("excel", "Excel File"),
            ("ocr", "Menu Photo OCR"),
            ("manual", "Manual Entry"),
        ],
    )

    # Original file info
    original_filename = models.CharField(max_length=255, blank=True)

    # Import status
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending Review"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
    )

    # Imported items (JSON array)
    items = models.JSONField(default=list)

    # Errors during import
    errors = ArrayField(models.TextField(), default=list, blank=True)

    # Stats
    total_items = models.IntegerField(default=0)
    valid_items = models.IntegerField(default=0)
    created_items = models.IntegerField(default=0)

    # Confirmed by user
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Menu Import Batch"
        verbose_name_plural = "Menu Import Batches"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_type} import - {self.total_items} items"
