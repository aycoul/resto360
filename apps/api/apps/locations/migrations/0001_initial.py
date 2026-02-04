# Generated manually for locations app

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("authentication", "0001_initial"),
        ("menu", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField(blank=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("website", models.URLField(blank=True)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="brand_logos/")),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="brand_covers/")),
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
                ("default_timezone", models.CharField(default="Africa/Abidjan", max_length=50)),
                ("default_currency", models.CharField(default="XOF", max_length=3)),
                ("default_language", models.CharField(default="fr", max_length=5)),
                (
                    "plan_type",
                    models.CharField(
                        choices=[("enterprise", "Enterprise"), ("franchise", "Franchise")],
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
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
        migrations.CreateModel(
            name="BrandManager",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("admin", "Brand Admin"),
                            ("manager", "Brand Manager"),
                            ("viewer", "Brand Viewer"),
                        ],
                        default="manager",
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="managers",
                        to="locations.brand",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="brand_management",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("brand", "user")},
            },
        ),
        migrations.CreateModel(
            name="SharedMenu",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("is_default", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shared_menus",
                        to="locations.brand",
                    ),
                ),
            ],
            options={
                "ordering": ["-is_default", "name"],
                "unique_together": {("brand", "name")},
            },
        ),
        migrations.CreateModel(
            name="SharedMenuCategory",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to="shared_menu/categories/")),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "shared_menu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="categories",
                        to="locations.sharedmenu",
                    ),
                ),
            ],
            options={
                "ordering": ["display_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="SharedMenuItem",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("base_price", models.DecimalField(decimal_places=0, max_digits=10)),
                ("image", models.ImageField(blank=True, null=True, upload_to="shared_menu/items/")),
                ("allergens", models.JSONField(blank=True, default=list)),
                ("dietary_tags", models.JSONField(blank=True, default=list)),
                ("calories", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "preparation_time",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Preparation time in minutes",
                        null=True,
                    ),
                ),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="locations.sharedmenucategory",
                    ),
                ),
            ],
            options={
                "ordering": ["display_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="LocationMenuSync",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_synced_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "auto_sync",
                    models.BooleanField(
                        default=True,
                        help_text="Automatically sync menu changes to this location",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="menu_syncs",
                        to="authentication.restaurant",
                    ),
                ),
                (
                    "shared_menu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="location_syncs",
                        to="locations.sharedmenu",
                    ),
                ),
            ],
            options={
                "unique_together": {("restaurant", "shared_menu")},
            },
        ),
        migrations.CreateModel(
            name="LocationPriceOverride",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("price", models.DecimalField(decimal_places=0, max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
                ("reason", models.CharField(blank=True, max_length=200)),
                (
                    "menu_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="location_overrides",
                        to="menu.menuitem",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="price_overrides",
                        to="authentication.restaurant",
                    ),
                ),
            ],
            options={
                "unique_together": {("restaurant", "menu_item")},
            },
        ),
        migrations.CreateModel(
            name="LocationItemAvailability",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_available", models.BooleanField(default=True)),
                ("unavailable_until", models.DateTimeField(blank=True, null=True)),
                ("reason", models.CharField(blank=True, max_length=200)),
                (
                    "menu_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="location_availability",
                        to="menu.menuitem",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="item_availability",
                        to="authentication.restaurant",
                    ),
                ),
            ],
            options={
                "unique_together": {("restaurant", "menu_item")},
            },
        ),
        migrations.CreateModel(
            name="BrandReport",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField()),
                (
                    "report_type",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                        ],
                        default="daily",
                        max_length=20,
                    ),
                ),
                ("total_orders", models.PositiveIntegerField(default=0)),
                ("total_revenue", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("average_order_value", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("total_customers", models.PositiveIntegerField(default=0)),
                (
                    "location_breakdown",
                    models.JSONField(
                        default=dict,
                        help_text="Revenue and orders by location",
                    ),
                ),
                (
                    "top_items",
                    models.JSONField(
                        default=list,
                        help_text="Top selling items across all locations",
                    ),
                ),
                (
                    "top_locations",
                    models.JSONField(
                        default=list,
                        help_text="Top performing locations",
                    ),
                ),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reports",
                        to="locations.brand",
                    ),
                ),
            ],
            options={
                "ordering": ["-date"],
                "unique_together": {("brand", "date", "report_type")},
            },
        ),
        migrations.CreateModel(
            name="BrandAnnouncement",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("content", models.TextField()),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("normal", "Normal"),
                            ("high", "High"),
                            ("urgent", "Urgent"),
                        ],
                        default="normal",
                        max_length=20,
                    ),
                ),
                ("publish_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="announcements",
                        to="locations.brand",
                    ),
                ),
                (
                    "target_groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Leave empty to target all locations",
                        related_name="announcements",
                        to="locations.locationgroup",
                    ),
                ),
            ],
            options={
                "ordering": ["-publish_at"],
            },
        ),
    ]
