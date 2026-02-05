# Generated for multi-location support

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        # Brand model - parent for chain businesses
        migrations.CreateModel(
            name="Brand",
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
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField(blank=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("website", models.URLField(blank=True)),
                (
                    "logo",
                    models.ImageField(
                        blank=True, null=True, upload_to="brand_logos/"
                    ),
                ),
                (
                    "cover_image",
                    models.ImageField(
                        blank=True, null=True, upload_to="brand_covers/"
                    ),
                ),
                (
                    "primary_color",
                    models.CharField(
                        default="#10B981",
                        help_text="Hex color code",
                        max_length=7,
                    ),
                ),
                (
                    "secondary_color",
                    models.CharField(
                        default="#059669",
                        help_text="Hex color code",
                        max_length=7,
                    ),
                ),
                (
                    "default_timezone",
                    models.CharField(default="Africa/Abidjan", max_length=50),
                ),
                ("default_currency", models.CharField(default="XOF", max_length=3)),
                ("default_language", models.CharField(default="fr", max_length=5)),
                (
                    "plan_type",
                    models.CharField(
                        choices=[
                            ("enterprise", "Enterprise"),
                            ("franchise", "Franchise"),
                        ],
                        default="enterprise",
                        max_length=20,
                    ),
                ),
                ("max_locations", models.PositiveIntegerField(default=10)),
                ("owner_name", models.CharField(blank=True, max_length=200)),
                ("owner_email", models.EmailField(blank=True, max_length=254)),
                ("owner_phone", models.CharField(blank=True, max_length=20)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        # LocationGroup model - group locations by region/city
        migrations.CreateModel(
            name="LocationGroup",
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
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="location_groups",
                        to="locations.brand",
                    ),
                ),
            ],
            options={
                "ordering": ["display_order", "name"],
                "unique_together": {("brand", "name")},
            },
        ),
    ]
