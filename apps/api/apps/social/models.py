"""
Social Media Automation Models

Manage social media posts, templates, scheduling, and analytics.
"""

import secrets
from django.db import models
from django.utils import timezone

from apps.core.models import TenantModel


class SocialPlatform(models.TextChoices):
    """Supported social media platforms."""

    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"
    TIKTOK = "tiktok", "TikTok"
    TWITTER = "twitter", "Twitter/X"


class PostType(models.TextChoices):
    """Types of social media posts."""

    IMAGE = "image", "Image Post"
    CAROUSEL = "carousel", "Carousel"
    VIDEO = "video", "Video"
    STORY = "story", "Story"
    REEL = "reel", "Reel"


class PostStatus(models.TextChoices):
    """Post status choices."""

    DRAFT = "draft", "Draft"
    SCHEDULED = "scheduled", "Scheduled"
    PUBLISHING = "publishing", "Publishing"
    PUBLISHED = "published", "Published"
    FAILED = "failed", "Failed"


class SocialAccount(TenantModel):
    """
    Connected social media account.
    """

    platform = models.CharField(
        max_length=20,
        choices=SocialPlatform.choices,
    )
    account_name = models.CharField(max_length=100)
    account_id = models.CharField(max_length=100, blank=True)
    profile_picture_url = models.URLField(blank=True)

    # OAuth tokens (encrypted in production)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    connected_at = models.DateTimeField(default=timezone.now)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["restaurant", "platform", "account_id"]

    def __str__(self):
        return f"{self.get_platform_display()} - {self.account_name}"

    @property
    def is_token_expired(self) -> bool:
        """Check if the access token has expired."""
        if not self.token_expires_at:
            return False
        return timezone.now() >= self.token_expires_at


class PostTemplate(TenantModel):
    """
    Reusable post templates.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    post_type = models.CharField(
        max_length=20,
        choices=PostType.choices,
        default=PostType.IMAGE,
    )

    # Template content
    caption_template = models.TextField(
        blank=True,
        help_text="Use {item_name}, {price}, {description} as placeholders",
    )
    hashtags = models.TextField(
        blank=True,
        help_text="Hashtags to include (one per line)",
    )

    # Visual template settings
    background_color = models.CharField(max_length=7, default="#FFFFFF")
    text_color = models.CharField(max_length=7, default="#000000")
    accent_color = models.CharField(max_length=7, default="#10B981")
    font_style = models.CharField(max_length=50, default="modern")

    # Overlay settings
    show_price = models.BooleanField(default=True)
    show_logo = models.BooleanField(default=True)
    overlay_opacity = models.PositiveIntegerField(default=30)

    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "name"]

    def __str__(self):
        return self.name


class SocialPost(TenantModel):
    """
    Social media post.
    """

    # Content
    caption = models.TextField()
    hashtags = models.TextField(blank=True)

    post_type = models.CharField(
        max_length=20,
        choices=PostType.choices,
        default=PostType.IMAGE,
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
    )

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Template used
    template = models.ForeignKey(
        PostTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )

    # Menu item reference (for menu item posts)
    menu_item = models.ForeignKey(
        "menu.MenuItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="social_posts",
    )

    # Error tracking
    error_message = models.TextField(blank=True)

    # AI generated
    is_ai_generated = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_post_type_display()} - {self.caption[:50]}..."

    @property
    def full_caption(self) -> str:
        """Get caption with hashtags."""
        if self.hashtags:
            return f"{self.caption}\n\n{self.hashtags}"
        return self.caption


class PostMedia(TenantModel):
    """
    Media files for social posts.
    """

    post = models.ForeignKey(
        SocialPost,
        on_delete=models.CASCADE,
        related_name="media",
    )

    media_type = models.CharField(
        max_length=10,
        choices=[
            ("image", "Image"),
            ("video", "Video"),
        ],
        default="image",
    )

    file = models.FileField(upload_to="social/media/")
    thumbnail = models.ImageField(upload_to="social/thumbnails/", null=True, blank=True)

    # Generated image (for template-based posts)
    is_generated = models.BooleanField(default=False)

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"Media for {self.post_id}"


class PostPublish(TenantModel):
    """
    Record of a post published to a specific platform.
    """

    post = models.ForeignKey(
        SocialPost,
        on_delete=models.CASCADE,
        related_name="publishes",
    )
    account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="publishes",
    )

    platform_post_id = models.CharField(max_length=100, blank=True)
    platform_url = models.URLField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.SCHEDULED,
    )

    published_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Analytics
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    reach = models.PositiveIntegerField(default=0)
    engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    last_stats_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["post", "account"]

    def __str__(self):
        return f"{self.post_id} -> {self.account.platform}"


class ContentCalendar(TenantModel):
    """
    Content calendar for planning posts.
    """

    date = models.DateField()
    time_slot = models.TimeField(null=True, blank=True)

    post = models.ForeignKey(
        SocialPost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calendar_entries",
    )

    # Planning info (before post is created)
    planned_content = models.CharField(max_length=200, blank=True)
    content_type = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["date", "time_slot"]

    def __str__(self):
        return f"{self.date} - {self.planned_content or self.post}"


class AICaption(TenantModel):
    """
    AI-generated caption suggestions.
    """

    menu_item = models.ForeignKey(
        "menu.MenuItem",
        on_delete=models.CASCADE,
        related_name="ai_captions",
    )

    caption = models.TextField()
    hashtags = models.TextField(blank=True)
    tone = models.CharField(
        max_length=20,
        choices=[
            ("professional", "Professional"),
            ("casual", "Casual"),
            ("playful", "Playful"),
            ("elegant", "Elegant"),
            ("promotional", "Promotional"),
        ],
        default="casual",
    )
    language = models.CharField(max_length=5, default="en")

    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Caption for {self.menu_item.name}"


class SocialAnalytics(TenantModel):
    """
    Aggregated social media analytics.
    """

    account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="analytics",
    )
    date = models.DateField()

    # Metrics
    followers = models.PositiveIntegerField(default=0)
    followers_change = models.IntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    total_reach = models.PositiveIntegerField(default=0)
    total_impressions = models.PositiveIntegerField(default=0)
    engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ["account", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.account.platform} - {self.date}"
