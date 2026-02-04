"""
Website Generator Models

Auto-generate restaurant websites with customizable templates.
"""

import secrets

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TenantModel


class WebsiteTemplate(models.TextChoices):
    """Available website templates."""

    MODERN = "modern", "Modern"
    ELEGANT = "elegant", "Elegant"
    CASUAL = "casual", "Casual"
    MINIMAL = "minimal", "Minimal"
    VIBRANT = "vibrant", "Vibrant"


class WebsiteStatus(models.TextChoices):
    """Website publication status."""

    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    MAINTENANCE = "maintenance", "Maintenance"


class Website(TenantModel):
    """
    Restaurant website configuration.

    Stores all website settings, content, and customization options.
    """

    # Status
    status = models.CharField(
        max_length=20,
        choices=WebsiteStatus.choices,
        default=WebsiteStatus.DRAFT,
    )

    # Template & Design
    template = models.CharField(
        max_length=20,
        choices=WebsiteTemplate.choices,
        default=WebsiteTemplate.MODERN,
    )
    primary_color = models.CharField(max_length=7, default="#10B981")
    secondary_color = models.CharField(max_length=7, default="#6366F1")
    background_color = models.CharField(max_length=7, default="#FFFFFF")
    text_color = models.CharField(max_length=7, default="#1F2937")

    # Branding
    logo = models.ImageField(upload_to="website/logos/", null=True, blank=True)
    favicon = models.ImageField(upload_to="website/favicons/", null=True, blank=True)
    cover_image = models.ImageField(upload_to="website/covers/", null=True, blank=True)

    # Content - Hero Section
    hero_title = models.CharField(max_length=200, blank=True)
    hero_subtitle = models.TextField(blank=True)
    hero_cta_text = models.CharField(max_length=50, blank=True)
    hero_cta_link = models.CharField(max_length=200, blank=True)

    # Content - About Section
    about_title = models.CharField(max_length=200, blank=True)
    about_text = models.TextField(blank=True)
    about_image = models.ImageField(upload_to="website/about/", null=True, blank=True)

    # Business Info
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    google_maps_embed = models.TextField(blank=True)

    # Social Media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)

    # Features Toggle
    show_menu = models.BooleanField(default=True)
    show_reservations = models.BooleanField(default=True)
    show_reviews = models.BooleanField(default=True)
    show_about = models.BooleanField(default=True)
    show_contact = models.BooleanField(default=True)
    show_hours = models.BooleanField(default=True)
    show_gallery = models.BooleanField(default=True)
    show_map = models.BooleanField(default=True)

    # Domain
    subdomain = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$",
                message="Subdomain must be lowercase alphanumeric, may contain hyphens",
            )
        ],
    )
    custom_domain = models.CharField(max_length=200, blank=True)
    custom_domain_verified = models.BooleanField(default=False)

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)

    # Timestamps
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Website"
        verbose_name_plural = "Websites"

    def __str__(self):
        return f"Website - {self.restaurant.name}"

    def save(self, *args, **kwargs):
        if not self.subdomain:
            self.subdomain = self._generate_subdomain()
        super().save(*args, **kwargs)

    def _generate_subdomain(self):
        """Generate a unique subdomain based on restaurant name."""
        import re

        base = re.sub(r"[^a-z0-9]", "-", self.restaurant.name.lower())
        base = re.sub(r"-+", "-", base).strip("-")[:40]

        subdomain = base
        counter = 1
        while Website.objects.filter(subdomain=subdomain).exists():
            subdomain = f"{base}-{counter}"
            counter += 1

        return subdomain

    def publish(self):
        """Publish the website."""
        self.status = WebsiteStatus.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def unpublish(self):
        """Unpublish the website."""
        self.status = WebsiteStatus.DRAFT
        self.save(update_fields=["status", "updated_at"])

    @property
    def public_url(self) -> str:
        """Get the public URL for this website."""
        if self.custom_domain and self.custom_domain_verified:
            return f"https://{self.custom_domain}"
        if self.subdomain:
            return f"https://{self.subdomain}.resto360.com"
        return ""


class WebsiteGalleryImage(TenantModel):
    """
    Gallery images for restaurant website.
    """

    website = models.ForeignKey(
        Website,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image = models.ImageField(upload_to="website/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"Gallery Image - {self.caption or self.id}"


class WebsiteBusinessHours(TenantModel):
    """
    Business hours display for website.
    """

    website = models.ForeignKey(
        Website,
        on_delete=models.CASCADE,
        related_name="business_hours",
    )
    day_of_week = models.PositiveIntegerField(
        choices=[
            (0, "Monday"),
            (1, "Tuesday"),
            (2, "Wednesday"),
            (3, "Thursday"),
            (4, "Friday"),
            (5, "Saturday"),
            (6, "Sunday"),
        ]
    )
    is_open = models.BooleanField(default=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    note = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["day_of_week"]
        unique_together = ["website", "day_of_week"]

    @property
    def day_name(self) -> str:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[self.day_of_week]


class WebsiteContactForm(TenantModel):
    """
    Contact form submissions from website visitors.
    """

    website = models.ForeignKey(
        Website,
        on_delete=models.CASCADE,
        related_name="contact_submissions",
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Contact from {self.name}"

    def mark_read(self):
        """Mark submission as read."""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at", "updated_at"])
