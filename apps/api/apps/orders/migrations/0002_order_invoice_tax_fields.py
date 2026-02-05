# Migration for BIZ360 Order invoice and tax fields

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
        ("authentication", "0001_initial"),
    ]

    operations = [
        # Create InvoiceSequence model
        migrations.CreateModel(
            name="InvoiceSequence",
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
                ("year", models.PositiveIntegerField()),
                ("last_number", models.PositiveIntegerField(default=0)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invoice_sequences",
                        to="authentication.business",
                    ),
                ),
            ],
            options={
                "unique_together": {("business", "year")},
            },
        ),
        # Add invoice_number to Order
        migrations.AddField(
            model_name="order",
            name="invoice_number",
            field=models.CharField(
                blank=True,
                help_text="Sequential invoice number (BIZ-XXX-YYYY-NNNNNN)",
                max_length=50,
                null=True,
                unique=True,
            ),
        ),
        # Add customer fields
        migrations.AddField(
            model_name="order",
            name="customer_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="order",
            name="customer_tax_id",
            field=models.CharField(
                blank=True,
                help_text="Customer's NCC for B2B invoices",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="customer_address",
            field=models.TextField(blank=True),
        ),
        # Add tax fields
        migrations.AddField(
            model_name="order",
            name="tax_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=18.00,
                help_text="Tax rate applied (default: Ivory Coast VAT 18%)",
                max_digits=5,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="tax_amount",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Total tax amount in XOF",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="subtotal_ht",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Subtotal Hors Taxe (excluding tax) in XOF",
            ),
        ),
        # Add DGI fields
        migrations.AddField(
            model_name="order",
            name="dgi_submission_status",
            field=models.CharField(
                choices=[
                    ("not_required", "Not Required"),
                    ("pending", "Pending"),
                    ("submitted", "Submitted"),
                    ("accepted", "Accepted"),
                    ("rejected", "Rejected"),
                ],
                default="not_required",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="dgi_reference",
            field=models.CharField(
                blank=True,
                help_text="DGI unique identifier after submission",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="dgi_submitted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="dgi_qr_code",
            field=models.TextField(
                blank=True,
                help_text="QR code data for DGI verification",
            ),
        ),
        # Add indexes for invoice_number and dgi_submission_status
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["invoice_number"], name="orders_orde_invoice_idx"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["dgi_submission_status"], name="orders_orde_dgi_idx"
            ),
        ),
    ]
