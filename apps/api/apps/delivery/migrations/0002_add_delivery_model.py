# Generated manually for 05-02 plan

import uuid

import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
import django_fsm
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_restaurant_location_fields"),
        ("delivery", "0001_initial"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Delivery",
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
                    "status",
                    django_fsm.FSMField(
                        choices=[
                            ("pending_assignment", "Pending Assignment"),
                            ("assigned", "Assigned"),
                            ("picked_up", "Picked Up"),
                            ("en_route", "En Route"),
                            ("delivered", "Delivered"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending_assignment",
                        max_length=50,
                        protected=True,
                    ),
                ),
                (
                    "pickup_address",
                    models.TextField(help_text="Restaurant address (copied at creation)"),
                ),
                (
                    "pickup_location",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, geography=True, null=True, srid=4326
                    ),
                ),
                (
                    "delivery_address",
                    models.TextField(help_text="Customer delivery address"),
                ),
                (
                    "delivery_location",
                    django.contrib.gis.db.models.fields.PointField(
                        geography=True,
                        help_text="Customer delivery coordinates",
                        srid=4326,
                    ),
                ),
                (
                    "delivery_notes",
                    models.TextField(
                        blank=True, help_text="Delivery instructions from customer"
                    ),
                ),
                (
                    "delivery_fee",
                    models.PositiveIntegerField(help_text="Delivery fee charged in XOF"),
                ),
                ("assigned_at", models.DateTimeField(blank=True, null=True)),
                ("picked_up_at", models.DateTimeField(blank=True, null=True)),
                ("en_route_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_reason", models.TextField(blank=True)),
                (
                    "estimated_delivery_time",
                    models.DateTimeField(
                        blank=True, help_text="Estimated time of delivery", null=True
                    ),
                ),
                (
                    "proof_type",
                    models.CharField(
                        choices=[
                            ("photo", "Photo"),
                            ("signature", "Signature"),
                            ("none", "None"),
                        ],
                        default="none",
                        max_length=20,
                    ),
                ),
                (
                    "proof_photo",
                    models.ImageField(
                        blank=True, null=True, upload_to="delivery_proofs/"
                    ),
                ),
                (
                    "proof_signature",
                    models.TextField(
                        blank=True, help_text="Base64-encoded signature image"
                    ),
                ),
                (
                    "recipient_name",
                    models.CharField(
                        blank=True,
                        help_text="Name of person who received delivery",
                        max_length=100,
                    ),
                ),
                ("customer_name", models.CharField(blank=True, max_length=100)),
                ("customer_phone", models.CharField(blank=True, max_length=20)),
                (
                    "driver",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="deliveries",
                        to="delivery.driver",
                    ),
                ),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delivery",
                        to="orders.order",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deliveries",
                        to="authentication.restaurant",
                    ),
                ),
                (
                    "zone",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="deliveries",
                        to="delivery.deliveryzone",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name_plural": "deliveries",
            },
        ),
    ]
