"""Models for the reviews app."""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import TenantModel


class ReviewStatus(models.TextChoices):
    """Status choices for reviews."""

    PENDING = "pending", "Pending Moderation"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    FLAGGED = "flagged", "Flagged for Review"


class ReviewSource(models.TextChoices):
    """Source of the review."""

    WEBSITE = "website", "Website"
    QR_CODE = "qr_code", "QR Code"
    EMAIL = "email", "Email Request"
    SMS = "sms", "SMS Request"
    GOOGLE = "google", "Google Reviews"


class Review(TenantModel):
    """
    Customer review for a restaurant.

    Stores star ratings, written reviews, and photos.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Rating (1-5 stars)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Star rating from 1 to 5",
    )

    # Review content
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True, help_text="Written review text")

    # Reviewer info
    reviewer_name = models.CharField(max_length=100)
    reviewer_email = models.EmailField(blank=True)
    reviewer_phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether reviewer made a verified order/reservation",
    )

    # Visit details
    visit_date = models.DateField(null=True, blank=True)
    order_id = models.UUIDField(null=True, blank=True, help_text="Related order if any")
    reservation_id = models.UUIDField(
        null=True, blank=True, help_text="Related reservation if any"
    )

    # Detailed ratings (optional sub-ratings)
    food_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    service_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    ambiance_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    value_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    # Status and moderation
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    source = models.CharField(
        max_length=20,
        choices=ReviewSource.choices,
        default=ReviewSource.WEBSITE,
    )

    # Moderation
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_notes = models.TextField(blank=True)

    # Visibility
    is_featured = models.BooleanField(default=False, help_text="Show prominently on menu")

    # External review ID (for Google Reviews sync)
    external_id = models.CharField(max_length=255, blank=True)
    external_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["restaurant", "status", "-created_at"]),
            models.Index(fields=["restaurant", "rating"]),
        ]

    def __str__(self):
        return f"{self.reviewer_name} - {self.rating} stars"

    @property
    def has_response(self):
        """Check if review has an owner response."""
        return hasattr(self, "response") and self.response is not None


class ReviewPhoto(TenantModel):
    """
    Photo attached to a review.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField(upload_to="review_photos/")
    caption = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Review Photo"
        verbose_name_plural = "Review Photos"
        ordering = ["display_order"]

    def __str__(self):
        return f"Photo for review {self.review_id}"


class ReviewResponse(TenantModel):
    """
    Owner response to a review.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name="response",
    )
    content = models.TextField(help_text="Response text")
    responder_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name to display (e.g., 'The Manager')",
    )

    class Meta:
        verbose_name = "Review Response"
        verbose_name_plural = "Review Responses"

    def __str__(self):
        return f"Response to {self.review.reviewer_name}'s review"


class FeedbackRequest(TenantModel):
    """
    Request for feedback sent to a customer.

    Triggered after an order or reservation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Customer info
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    # Related entities
    order_id = models.UUIDField(null=True, blank=True)
    reservation_id = models.UUIDField(null=True, blank=True)

    # Request details
    channel = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("sms", "SMS"),
        ],
        default="email",
    )

    # Status
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Token for secure feedback submission
    token = models.CharField(max_length=64, unique=True, editable=False)

    # Result
    review = models.OneToOneField(
        Review,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_request",
    )

    class Meta:
        verbose_name = "Feedback Request"
        verbose_name_plural = "Feedback Requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feedback request for {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.token:
            import secrets

            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


class ReviewSettings(TenantModel):
    """
    Restaurant review settings.
    """

    # Auto-moderation
    auto_approve = models.BooleanField(
        default=False,
        help_text="Automatically approve reviews (no moderation)",
    )
    min_rating_auto_approve = models.PositiveIntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Minimum rating for auto-approval",
    )

    # Feedback requests
    auto_request_feedback = models.BooleanField(
        default=True,
        help_text="Automatically request feedback after orders",
    )
    request_delay_hours = models.PositiveIntegerField(
        default=24,
        help_text="Hours after order/visit to send request",
    )
    request_channel = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("sms", "SMS"),
            ("both", "Both"),
        ],
        default="email",
    )

    # Display settings
    show_reviews_on_menu = models.BooleanField(
        default=True,
        help_text="Show reviews on public menu",
    )
    min_reviews_to_show = models.PositiveIntegerField(
        default=3,
        help_text="Minimum reviews before showing on menu",
    )
    show_average_rating = models.BooleanField(default=True)

    # Response template
    response_template = models.TextField(
        blank=True,
        help_text="Default template for owner responses",
    )

    class Meta:
        verbose_name = "Review Settings"
        verbose_name_plural = "Review Settings"

    def __str__(self):
        return f"Review Settings for {self.restaurant.name}"


class ReviewSummary(TenantModel):
    """
    Cached review summary statistics.

    Updated periodically for performance.
    """

    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0
    )
    rating_distribution = models.JSONField(
        default=dict,
        help_text="Distribution: {1: count, 2: count, ...}",
    )

    # Sub-ratings
    avg_food_rating = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    avg_service_rating = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    avg_ambiance_rating = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    avg_value_rating = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )

    # Response metrics
    response_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Percentage of reviews with responses",
    )

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Review Summary"
        verbose_name_plural = "Review Summaries"

    def __str__(self):
        return f"Review Summary for {self.restaurant.name}"

    def refresh(self):
        """Recalculate summary statistics."""
        from django.db.models import Avg, Count

        reviews = Review.objects.filter(
            restaurant=self.restaurant,
            status=ReviewStatus.APPROVED,
        )

        # Total and average
        stats = reviews.aggregate(
            total=Count("id"),
            avg_rating=Avg("rating"),
            avg_food=Avg("food_rating"),
            avg_service=Avg("service_rating"),
            avg_ambiance=Avg("ambiance_rating"),
            avg_value=Avg("value_rating"),
        )

        self.total_reviews = stats["total"] or 0
        self.average_rating = stats["avg_rating"] or 0
        self.avg_food_rating = stats["avg_food"]
        self.avg_service_rating = stats["avg_service"]
        self.avg_ambiance_rating = stats["avg_ambiance"]
        self.avg_value_rating = stats["avg_value"]

        # Distribution
        distribution = {}
        for i in range(1, 6):
            distribution[str(i)] = reviews.filter(rating=i).count()
        self.rating_distribution = distribution

        # Response rate
        if self.total_reviews > 0:
            responded = reviews.filter(response__isnull=False).count()
            self.response_rate = (responded / self.total_reviews) * 100

        self.save()
