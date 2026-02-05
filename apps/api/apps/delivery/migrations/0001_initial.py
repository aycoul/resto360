# Generated manually for 05-01 plan

import uuid

import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("authentication", "0002_restaurant_location_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DeliveryZone",
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
                (
                    "polygon",
                    django.contrib.gis.db.models.fields.PolygonField(
                        geography=True, srid=4326
                    ),
                ),
                (
                    "delivery_fee",
                    models.PositiveIntegerField(help_text="Delivery fee in XOF"),
                ),
                (
                    "minimum_order",
                    models.PositiveIntegerField(
                        default=0, help_text="Minimum order amount in XOF"
                    ),
                ),
                (
                    "estimated_time_minutes",
                    models.PositiveIntegerField(
                        default=30, help_text="Base estimated delivery time in minutes"
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deliveryzones",
                        to="authentication.business",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Driver",
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
                (
                    "phone",
                    models.CharField(
                        help_text="Driver contact phone (may differ from user phone)",
                        max_length=20,
                    ),
                ),
                (
                    "vehicle_type",
                    models.CharField(
                        choices=[
                            ("motorcycle", "Motorcycle"),
                            ("bicycle", "Bicycle"),
                            ("car", "Car"),
                            ("foot", "On Foot"),
                        ],
                        default="motorcycle",
                        max_length=20,
                    ),
                ),
                (
                    "vehicle_plate",
                    models.CharField(
                        blank=True, help_text="License plate number", max_length=20
                    ),
                ),
                ("is_available", models.BooleanField(default=False)),
                ("went_online_at", models.DateTimeField(blank=True, null=True)),
                (
                    "current_location",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, geography=True, null=True, srid=4326
                    ),
                ),
                ("location_updated_at", models.DateTimeField(blank=True, null=True)),
                ("total_deliveries", models.PositiveIntegerField(default=0)),
                (
                    "average_rating",
                    models.DecimalField(decimal_places=2, default=5.0, max_digits=3),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drivers",
                        to="authentication.business",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        limit_choices_to={"role": "driver"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="driver_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["user__name"],
            },
        ),
    ]
