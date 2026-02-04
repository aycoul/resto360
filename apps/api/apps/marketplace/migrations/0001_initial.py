# Generated manually for marketplace models

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("authentication", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # SupplierCategory
        migrations.CreateModel(
            name="SupplierCategory",
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
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
                ("icon", models.CharField(blank=True, max_length=50, help_text="Icon name or emoji")),
                ("image", models.ImageField(blank=True, null=True, upload_to="marketplace/categories/")),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subcategories",
                        to="marketplace.suppliercategory",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Supplier categories",
                "ordering": ["display_order", "name"],
            },
        ),
        # Supplier
        migrations.CreateModel(
            name="Supplier",
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
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("description", models.TextField(blank=True)),
                (
                    "supplier_type",
                    models.CharField(
                        choices=[
                            ("producer", "Producer/Farmer"),
                            ("wholesaler", "Wholesaler"),
                            ("distributor", "Distributor"),
                            ("manufacturer", "Manufacturer"),
                            ("importer", "Importer"),
                        ],
                        default="wholesaler",
                        max_length=20,
                    ),
                ),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=20)),
                ("website", models.URLField(blank=True)),
                ("whatsapp", models.CharField(blank=True, max_length=20)),
                ("address", models.TextField()),
                ("city", models.CharField(max_length=100)),
                ("region", models.CharField(blank=True, max_length=100)),
                ("country", models.CharField(default="Senegal", max_length=100)),
                ("postal_code", models.CharField(blank=True, max_length=20)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="suppliers/logos/")),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="suppliers/covers/")),
                (
                    "verification_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending Review"),
                            ("verified", "Verified"),
                            ("rejected", "Rejected"),
                            ("suspended", "Suspended"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("verification_notes", models.TextField(blank=True)),
                ("business_registration", models.CharField(blank=True, max_length=100)),
                ("tax_id", models.CharField(blank=True, max_length=50)),
                ("years_in_business", models.PositiveSmallIntegerField(default=0)),
                (
                    "minimum_order_value",
                    models.DecimalField(
                        decimal_places=0,
                        default=0,
                        help_text="Minimum order value in XOF",
                        max_digits=10,
                    ),
                ),
                (
                    "delivery_areas",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="List of cities/regions the supplier delivers to",
                    ),
                ),
                (
                    "delivery_days",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Days of the week for delivery (0=Monday, 6=Sunday)",
                    ),
                ),
                (
                    "lead_time_days",
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text="Number of days advance notice required for orders",
                    ),
                ),
                (
                    "accepted_payment_methods",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="List of accepted payment methods",
                    ),
                ),
                (
                    "payment_terms",
                    models.CharField(
                        blank=True,
                        help_text="e.g., 'Net 30', 'COD', 'Prepaid'",
                        max_length=50,
                    ),
                ),
                ("total_orders", models.PositiveIntegerField(default=0)),
                ("total_revenue", models.DecimalField(decimal_places=0, default=0, max_digits=14)),
                ("average_rating", models.DecimalField(decimal_places=2, default=0, max_digits=3)),
                ("review_count", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="owned_suppliers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-is_featured", "-average_rating", "name"],
            },
        ),
        # SupplierProduct
        migrations.CreateModel(
            name="SupplierProduct",
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
                ("slug", models.SlugField(max_length=220)),
                ("description", models.TextField(blank=True)),
                ("sku", models.CharField(blank=True, help_text="Supplier's SKU", max_length=50)),
                (
                    "unit",
                    models.CharField(
                        choices=[
                            ("piece", "Piece"),
                            ("kg", "Kilogram"),
                            ("g", "Gram"),
                            ("l", "Liter"),
                            ("ml", "Milliliter"),
                            ("box", "Box"),
                            ("case", "Case"),
                            ("pack", "Pack"),
                            ("dozen", "Dozen"),
                            ("pallet", "Pallet"),
                        ],
                        default="kg",
                        max_length=20,
                    ),
                ),
                (
                    "unit_size",
                    models.DecimalField(
                        decimal_places=2,
                        default=1,
                        help_text="Size per unit (e.g., 25 for a 25kg bag)",
                        max_digits=10,
                    ),
                ),
                ("price", models.DecimalField(decimal_places=0, help_text="Price per unit in XOF", max_digits=10)),
                (
                    "bulk_pricing",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="List of {min_quantity, price} objects for bulk discounts",
                    ),
                ),
                ("minimum_order_quantity", models.PositiveIntegerField(default=1, help_text="Minimum quantity per order")),
                ("order_increment", models.PositiveIntegerField(default=1, help_text="Quantity must be ordered in multiples of this")),
                ("is_available", models.BooleanField(default=True)),
                (
                    "stock_status",
                    models.CharField(
                        choices=[
                            ("in_stock", "In Stock"),
                            ("low_stock", "Low Stock"),
                            ("out_of_stock", "Out of Stock"),
                            ("made_to_order", "Made to Order"),
                        ],
                        default="in_stock",
                        max_length=20,
                    ),
                ),
                (
                    "lead_time_days",
                    models.PositiveSmallIntegerField(
                        default=0,
                        help_text="Additional lead time for this product (beyond supplier default)",
                    ),
                ),
                ("image", models.ImageField(blank=True, null=True, upload_to="marketplace/products/")),
                ("images", models.JSONField(blank=True, default=list, help_text="Additional product images")),
                ("origin", models.CharField(blank=True, help_text="Country/region of origin", max_length=100)),
                ("brand", models.CharField(blank=True, max_length=100)),
                (
                    "certifications",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="e.g., ['Organic', 'Halal', 'Fair Trade']",
                    ),
                ),
                ("times_ordered", models.PositiveIntegerField(default=0)),
                (
                    "category",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="products",
                        to="marketplace.suppliercategory",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="marketplace.supplier",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("supplier", "slug")},
            },
        ),
        # SupplierOrder
        migrations.CreateModel(
            name="SupplierOrder",
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
                ("order_number", models.CharField(max_length=50, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted"),
                            ("confirmed", "Confirmed"),
                            ("processing", "Processing"),
                            ("shipped", "Shipped"),
                            ("delivered", "Delivered"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "payment_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("partial", "Partially Paid"),
                            ("paid", "Paid"),
                            ("refunded", "Refunded"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("expected_delivery", models.DateField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("delivery_address", models.TextField()),
                ("delivery_instructions", models.TextField(blank=True)),
                ("subtotal", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("delivery_fee", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("tax", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("discount", models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ("total", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("amount_paid", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("payment_method", models.CharField(blank=True, max_length=50)),
                ("payment_reference", models.CharField(blank=True, max_length=100)),
                ("restaurant_notes", models.TextField(blank=True, help_text="Notes from restaurant to supplier")),
                ("supplier_notes", models.TextField(blank=True, help_text="Notes from supplier")),
                ("internal_notes", models.TextField(blank=True, help_text="Internal notes (not visible to other party)")),
                ("invoice_number", models.CharField(blank=True, max_length=50)),
                ("invoice_file", models.FileField(blank=True, null=True, upload_to="marketplace/invoices/")),
                (
                    "placed_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="placed_supplier_orders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="supplier_orders",
                        to="authentication.restaurant",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to="marketplace.supplier",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        # SupplierOrderItem
        migrations.CreateModel(
            name="SupplierOrderItem",
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
                ("product_name", models.CharField(max_length=200)),
                ("product_sku", models.CharField(blank=True, max_length=50)),
                ("unit", models.CharField(max_length=20)),
                ("unit_size", models.DecimalField(decimal_places=2, max_digits=10)),
                ("quantity", models.PositiveIntegerField()),
                ("quantity_received", models.PositiveIntegerField(default=0)),
                ("unit_price", models.DecimalField(decimal_places=0, max_digits=10)),
                ("line_total", models.DecimalField(decimal_places=0, max_digits=12)),
                ("notes", models.TextField(blank=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="marketplace.supplierorder",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_items",
                        to="marketplace.supplierproduct",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        # SupplierReview
        migrations.CreateModel(
            name="SupplierReview",
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
                ("overall_rating", models.PositiveSmallIntegerField()),
                ("quality_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("delivery_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("communication_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("value_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("title", models.CharField(blank=True, max_length=200)),
                ("comment", models.TextField()),
                ("supplier_response", models.TextField(blank=True)),
                ("response_at", models.DateTimeField(blank=True, null=True)),
                ("is_verified", models.BooleanField(default=False, help_text="Verified purchase")),
                ("is_published", models.BooleanField(default=True)),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviews",
                        to="marketplace.supplierorder",
                    ),
                ),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supplier_reviews",
                        to="authentication.restaurant",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="supplier_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="marketplace.supplier",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "unique_together": {("supplier", "restaurant", "order")},
            },
        ),
        # SupplierFavorite
        migrations.CreateModel(
            name="SupplierFavorite",
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
                ("notes", models.TextField(blank=True, help_text="Private notes about this supplier")),
                (
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="favorite_suppliers",
                        to="authentication.restaurant",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="favorited_by",
                        to="marketplace.supplier",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "unique_together": {("restaurant", "supplier")},
            },
        ),
        # Cart
        migrations.CreateModel(
            name="Cart",
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
                    "restaurant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supplier_carts",
                        to="authentication.restaurant",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="carts",
                        to="marketplace.supplier",
                    ),
                ),
            ],
            options={
                "unique_together": {("restaurant", "supplier")},
            },
        ),
        # CartItem
        migrations.CreateModel(
            name="CartItem",
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
                ("quantity", models.PositiveIntegerField(default=1)),
                (
                    "cart",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="marketplace.cart",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cart_items",
                        to="marketplace.supplierproduct",
                    ),
                ),
            ],
            options={
                "unique_together": {("cart", "product")},
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name="supplier",
            index=models.Index(fields=["verification_status", "is_active"], name="marketplace_supplier_verify_idx"),
        ),
        migrations.AddIndex(
            model_name="supplier",
            index=models.Index(fields=["city", "is_active"], name="marketplace_supplier_city_idx"),
        ),
        migrations.AddIndex(
            model_name="supplier",
            index=models.Index(fields=["average_rating"], name="marketplace_supplier_rating_idx"),
        ),
        migrations.AddIndex(
            model_name="supplierproduct",
            index=models.Index(fields=["supplier", "is_available"], name="marketplace_product_supplier_idx"),
        ),
        migrations.AddIndex(
            model_name="supplierproduct",
            index=models.Index(fields=["category", "is_available"], name="marketplace_product_category_idx"),
        ),
        migrations.AddIndex(
            model_name="supplierproduct",
            index=models.Index(fields=["price"], name="marketplace_product_price_idx"),
        ),
        migrations.AddIndex(
            model_name="supplierorder",
            index=models.Index(fields=["restaurant", "status"], name="marketplace_order_restaurant_idx"),
        ),
        migrations.AddIndex(
            model_name="supplierorder",
            index=models.Index(fields=["supplier", "status"], name="marketplace_order_supplier_idx"),
        ),
        migrations.AddIndex(
            model_name="supplierorder",
            index=models.Index(fields=["order_number"], name="marketplace_order_number_idx"),
        ),
        migrations.AddIndex(
            model_name="supplierorder",
            index=models.Index(fields=["expected_delivery"], name="marketplace_order_delivery_idx"),
        ),
        migrations.AddIndex(
            model_name="supplierreview",
            index=models.Index(fields=["supplier", "is_published"], name="marketplace_review_supplier_idx"),
        ),
        migrations.AddIndex(
            model_name="supplierreview",
            index=models.Index(fields=["overall_rating"], name="marketplace_review_rating_idx"),
        ),
    ]
