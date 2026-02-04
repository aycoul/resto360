# Generated manually for social app

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("menu", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SocialAccount",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "platform",
                    models.CharField(
                        choices=[
                            ("instagram", "Instagram"),
                            ("facebook", "Facebook"),
                            ("tiktok", "TikTok"),
                            ("twitter", "Twitter/X"),
                        ],
                        max_length=20,
                    ),
                ),
                ("account_name", models.CharField(max_length=100)),
                ("account_id", models.CharField(blank=True, max_length=100)),
                ("profile_picture_url", models.URLField(blank=True)),
                ("access_token", models.TextField(blank=True)),
                ("refresh_token", models.TextField(blank=True)),
                ("token_expires_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("connected_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="social_accounts",
                        to="core.restaurant",
                    ),
                ),
            ],
            options={
                "unique_together": {("restaurant", "platform", "account_id")},
            },
        ),
        migrations.CreateModel(
            name="PostTemplate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                (
                    "post_type",
                    models.CharField(
                        choices=[
                            ("image", "Image Post"),
                            ("carousel", "Carousel"),
                            ("video", "Video"),
                            ("story", "Story"),
                            ("reel", "Reel"),
                        ],
                        default="image",
                        max_length=20,
                    ),
                ),
                (
                    "caption_template",
                    models.TextField(
                        blank=True,
                        help_text="Use {item_name}, {price}, {description} as placeholders",
                    ),
                ),
                (
                    "hashtags",
                    models.TextField(blank=True, help_text="Hashtags to include (one per line)"),
                ),
                ("background_color", models.CharField(default="#FFFFFF", max_length=7)),
                ("text_color", models.CharField(default="#000000", max_length=7)),
                ("accent_color", models.CharField(default="#10B981", max_length=7)),
                ("font_style", models.CharField(default="modern", max_length=50)),
                ("show_price", models.BooleanField(default=True)),
                ("show_logo", models.BooleanField(default=True)),
                ("overlay_opacity", models.PositiveIntegerField(default=30)),
                ("is_default", models.BooleanField(default=False)),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="post_templates",
                        to="core.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-is_default", "name"],
            },
        ),
        migrations.CreateModel(
            name="SocialPost",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("caption", models.TextField()),
                ("hashtags", models.TextField(blank=True)),
                (
                    "post_type",
                    models.CharField(
                        choices=[
                            ("image", "Image Post"),
                            ("carousel", "Carousel"),
                            ("video", "Video"),
                            ("story", "Story"),
                            ("reel", "Reel"),
                        ],
                        default="image",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("scheduled", "Scheduled"),
                            ("publishing", "Publishing"),
                            ("published", "Published"),
                            ("failed", "Failed"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("scheduled_at", models.DateTimeField(blank=True, null=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("is_ai_generated", models.BooleanField(default=False)),
                (
                    "menu_item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="social_posts",
                        to="menu.menuitem",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="social_posts",
                        to="core.restaurant",
                    ),
                ),
                (
                    "template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="posts",
                        to="social.posttemplate",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PostMedia",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "media_type",
                    models.CharField(
                        choices=[("image", "Image"), ("video", "Video")],
                        default="image",
                        max_length=10,
                    ),
                ),
                ("file", models.FileField(upload_to="social/media/")),
                (
                    "thumbnail",
                    models.ImageField(blank=True, null=True, upload_to="social/thumbnails/"),
                ),
                ("is_generated", models.BooleanField(default=False)),
                ("display_order", models.PositiveIntegerField(default=0)),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="media",
                        to="social.socialpost",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="post_media",
                        to="core.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["display_order"],
            },
        ),
        migrations.CreateModel(
            name="PostPublish",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("platform_post_id", models.CharField(blank=True, max_length=100)),
                ("platform_url", models.URLField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("scheduled", "Scheduled"),
                            ("publishing", "Publishing"),
                            ("published", "Published"),
                            ("failed", "Failed"),
                        ],
                        default="scheduled",
                        max_length=20,
                    ),
                ),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("likes", models.PositiveIntegerField(default=0)),
                ("comments", models.PositiveIntegerField(default=0)),
                ("shares", models.PositiveIntegerField(default=0)),
                ("views", models.PositiveIntegerField(default=0)),
                ("reach", models.PositiveIntegerField(default=0)),
                (
                    "engagement_rate",
                    models.DecimalField(decimal_places=2, default=0, max_digits=5),
                ),
                ("last_stats_update", models.DateTimeField(blank=True, null=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="publishes",
                        to="social.socialaccount",
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="publishes",
                        to="social.socialpost",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="post_publishes",
                        to="core.restaurant",
                    ),
                ),
            ],
            options={
                "unique_together": {("post", "account")},
            },
        ),
        migrations.CreateModel(
            name="ContentCalendar",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField()),
                ("time_slot", models.TimeField(blank=True, null=True)),
                ("planned_content", models.CharField(blank=True, max_length=200)),
                ("content_type", models.CharField(blank=True, max_length=50)),
                ("notes", models.TextField(blank=True)),
                (
                    "post",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="calendar_entries",
                        to="social.socialpost",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="content_calendar",
                        to="core.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["date", "time_slot"],
            },
        ),
        migrations.CreateModel(
            name="AICaption",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("caption", models.TextField()),
                ("hashtags", models.TextField(blank=True)),
                (
                    "tone",
                    models.CharField(
                        choices=[
                            ("professional", "Professional"),
                            ("casual", "Casual"),
                            ("playful", "Playful"),
                            ("elegant", "Elegant"),
                            ("promotional", "Promotional"),
                        ],
                        default="casual",
                        max_length=20,
                    ),
                ),
                ("language", models.CharField(default="en", max_length=5)),
                ("is_used", models.BooleanField(default=False)),
                (
                    "menu_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_captions",
                        to="menu.menuitem",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_captions",
                        to="core.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SocialAnalytics",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField()),
                ("followers", models.PositiveIntegerField(default=0)),
                ("followers_change", models.IntegerField(default=0)),
                ("posts_count", models.PositiveIntegerField(default=0)),
                ("total_likes", models.PositiveIntegerField(default=0)),
                ("total_comments", models.PositiveIntegerField(default=0)),
                ("total_shares", models.PositiveIntegerField(default=0)),
                ("total_reach", models.PositiveIntegerField(default=0)),
                ("total_impressions", models.PositiveIntegerField(default=0)),
                (
                    "engagement_rate",
                    models.DecimalField(decimal_places=2, default=0, max_digits=5),
                ),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analytics",
                        to="social.socialaccount",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="social_analytics",
                        to="core.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-date"],
                "unique_together": {("account", "date")},
            },
        ),
    ]
