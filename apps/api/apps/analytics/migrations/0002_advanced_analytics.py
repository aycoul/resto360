# Generated manually for advanced analytics models

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0001_initial"),
        ("authentication", "0001_initial"),
        ("menu", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DailySalesStats",
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
                ("date", models.DateField(db_index=True)),
                ("total_orders", models.PositiveIntegerField(default=0)),
                ("completed_orders", models.PositiveIntegerField(default=0)),
                ("cancelled_orders", models.PositiveIntegerField(default=0)),
                ("dine_in_orders", models.PositiveIntegerField(default=0)),
                ("takeaway_orders", models.PositiveIntegerField(default=0)),
                ("delivery_orders", models.PositiveIntegerField(default=0)),
                ("total_revenue", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("average_order_value", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("total_items_sold", models.PositiveIntegerField(default=0)),
                ("orders_by_hour", models.JSONField(blank=True, default=dict)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)ss",
                        to="authentication.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-date"],
                "verbose_name_plural": "Daily sales stats",
                "unique_together": {("business", "date")},
            },
        ),
        migrations.CreateModel(
            name="ItemPerformance",
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
                ("date", models.DateField(db_index=True)),
                ("quantity_sold", models.PositiveIntegerField(default=0)),
                ("revenue", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("rank_by_quantity", models.PositiveIntegerField(blank=True, null=True)),
                ("rank_by_revenue", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "menu_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="performance_stats",
                        to="menu.menuitem",
                    ),
                ),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)ss",
                        to="authentication.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "-quantity_sold"],
                "unique_together": {("business", "menu_item", "date")},
            },
        ),
        migrations.CreateModel(
            name="CategoryPerformance",
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
                ("date", models.DateField(db_index=True)),
                ("items_sold", models.PositiveIntegerField(default=0)),
                ("revenue", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("order_count", models.PositiveIntegerField(default=0)),
                ("revenue_percentage", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="performance_stats",
                        to="menu.category",
                    ),
                ),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)ss",
                        to="authentication.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "-revenue"],
                "unique_together": {("business", "category", "date")},
            },
        ),
        migrations.CreateModel(
            name="HourlyStats",
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
                ("date", models.DateField(db_index=True)),
                ("hour", models.PositiveSmallIntegerField()),
                ("order_count", models.PositiveIntegerField(default=0)),
                ("revenue", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("items_sold", models.PositiveIntegerField(default=0)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)ss",
                        to="authentication.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "hour"],
                "unique_together": {("business", "date", "hour")},
            },
        ),
        migrations.CreateModel(
            name="CustomerStats",
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
                ("date", models.DateField(db_index=True)),
                ("new_customers", models.PositiveIntegerField(default=0)),
                ("returning_customers", models.PositiveIntegerField(default=0)),
                ("total_customers", models.PositiveIntegerField(default=0)),
                ("menu_views", models.PositiveIntegerField(default=0)),
                ("orders_placed", models.PositiveIntegerField(default=0)),
                (
                    "conversion_rate",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Percentage of menu views that resulted in orders",
                        max_digits=5,
                    ),
                ),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)ss",
                        to="authentication.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-date"],
                "unique_together": {("business", "date")},
            },
        ),
        migrations.CreateModel(
            name="WeeklyReport",
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
                ("week_start", models.DateField(db_index=True)),
                ("week_end", models.DateField()),
                ("total_orders", models.PositiveIntegerField(default=0)),
                ("total_revenue", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("average_daily_revenue", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("average_order_value", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("orders_change_percent", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("revenue_change_percent", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("top_items", models.JSONField(blank=True, default=list)),
                ("peak_hours", models.JSONField(blank=True, default=dict)),
                ("report_html", models.TextField(blank=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("sent_to", models.JSONField(blank=True, default=list)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)ss",
                        to="authentication.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-week_start"],
                "unique_together": {("business", "week_start")},
            },
        ),
        migrations.CreateModel(
            name="ReportExport",
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
                    "export_type",
                    models.CharField(
                        choices=[
                            ("sales", "Sales Report"),
                            ("items", "Item Performance"),
                            ("categories", "Category Performance"),
                            ("customers", "Customer Analytics"),
                            ("hourly", "Hourly Breakdown"),
                            ("full", "Full Report"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "format",
                    models.CharField(
                        choices=[("csv", "CSV"), ("pdf", "PDF"), ("xlsx", "Excel")],
                        max_length=10,
                    ),
                ),
                ("date_from", models.DateField()),
                ("date_to", models.DateField()),
                ("file", models.FileField(blank=True, null=True, upload_to="analytics/exports/")),
                ("file_size", models.PositiveIntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                (
                    "requested_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="report_exports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)ss",
                        to="authentication.restaurant",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name="dailysalesstats",
            index=models.Index(fields=["business", "date"], name="analytics_d_bus_sales_idx"),
        ),
        migrations.AddIndex(
            model_name="itemperformance",
            index=models.Index(fields=["business", "date"], name="analytics_i_bus_item_idx"),
        ),
        migrations.AddIndex(
            model_name="itemperformance",
            index=models.Index(fields=["menu_item", "date"], name="analytics_i_menu_item_idx"),
        ),
        migrations.AddIndex(
            model_name="categoryperformance",
            index=models.Index(fields=["business", "date"], name="analytics_c_bus_cat_idx"),
        ),
        migrations.AddIndex(
            model_name="hourlystats",
            index=models.Index(fields=["business", "date"], name="analytics_h_bus_hour_idx"),
        ),
        migrations.AddIndex(
            model_name="customerstats",
            index=models.Index(fields=["business", "date"], name="analytics_cs_bus_idx"),
        ),
        migrations.AddIndex(
            model_name="weeklyreport",
            index=models.Index(fields=["business", "week_start"], name="analytics_w_bus_week_idx"),
        ),
    ]
