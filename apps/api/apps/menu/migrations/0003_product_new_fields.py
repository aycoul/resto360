# Migration to add new Product fields (formerly MenuItem)
# Supports BIZ360 transformation: SKU, barcode, tax handling, QR reorder,
# food-specific fields, and nutrition information.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0002_alter_category_managers_alter_menuitem_managers_and_more"),
    ]

    operations = [
        # Universal product fields
        migrations.AddField(
            model_name="product",
            name="sku",
            field=models.CharField(
                blank=True,
                help_text="Stock Keeping Unit - internal product code",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="barcode",
            field=models.CharField(
                blank=True,
                help_text="Barcode (EAN, UPC, etc.) for scanning",
                max_length=50,
            ),
        ),
        # Tax handling fields
        migrations.AddField(
            model_name="product",
            name="tax_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=18.00,
                help_text="Tax rate for this product (default: Ivory Coast VAT 18%)",
                max_digits=5,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="is_tax_inclusive",
            field=models.BooleanField(
                default=True,
                help_text="Is the price inclusive of tax (TTC)?",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="tax_exempt",
            field=models.BooleanField(
                default=False,
                help_text="Is this product exempt from tax?",
            ),
        ),
        # QR Reorder feature fields
        migrations.AddField(
            model_name="product",
            name="reorder_qr_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Enable QR code reordering for this product",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="reorder_quantity",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Default quantity for QR reorder",
            ),
        ),
        # Food-specific fields
        migrations.AddField(
            model_name="product",
            name="allergens",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="List of allergens present in this item (food only)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="dietary_tags",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Dietary certifications/tags for this item (food only)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="spice_level",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "Not Spicy"),
                    (1, "Mild"),
                    (2, "Medium"),
                    (3, "Hot"),
                    (4, "Very Hot"),
                ],
                default=0,
                help_text="Spice/heat level of the dish (food only)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="prep_time_minutes",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Estimated preparation time in minutes (food only)",
                null=True,
            ),
        ),
        # Nutrition fields
        migrations.AddField(
            model_name="product",
            name="calories",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Calories per serving (kcal)",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="protein_grams",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text="Protein per serving (grams)",
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="carbs_grams",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text="Carbohydrates per serving (grams)",
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="fat_grams",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text="Fat per serving (grams)",
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="fiber_grams",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text="Fiber per serving (grams)",
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="sodium_mg",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Sodium per serving (milligrams)",
                null=True,
            ),
        ),
        # Ingredients list
        migrations.AddField(
            model_name="product",
            name="ingredients",
            field=models.TextField(
                blank=True,
                help_text="Comma-separated list of main ingredients",
            ),
        ),
        # Update image upload path
        migrations.AlterField(
            model_name="product",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="products/",
            ),
        ),
        # Update model options for Product name
        migrations.AlterModelOptions(
            name="product",
            options={
                "ordering": ["name"],
                "verbose_name": "Product",
                "verbose_name_plural": "Products",
            },
        ),
    ]
