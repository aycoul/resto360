# Generated for BIZ360 transformation - multi-business type support and DGI compliance

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0003_restaurant_plan_type_branding"),
        ("locations", "0001_initial"),
    ]

    operations = [
        # Business type field (NEW for BIZ360)
        migrations.AddField(
            model_name="business",
            name="business_type",
            field=models.CharField(
                choices=[
                    ("restaurant", "Restaurant"),
                    ("cafe", "Café"),
                    ("bakery", "Bakery"),
                    ("retail", "Retail Shop"),
                    ("pharmacy", "Pharmacy"),
                    ("confectionery", "Confectionery"),
                    ("grocery", "Grocery Store"),
                    ("boutique", "Boutique"),
                    ("hardware", "Hardware Store"),
                    ("other", "Other"),
                ],
                default="restaurant",
                help_text="Type of business (determines UI and features)",
                max_length=20,
            ),
        ),
        # Ivory Coast DGI Tax compliance fields
        migrations.AddField(
            model_name="business",
            name="tax_id",
            field=models.CharField(
                blank=True,
                help_text="NCC (Numéro de Compte Contribuable) or RCC number",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="tax_regime",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "None"),
                    ("rne", "RNE (Registre Numérique des Encaissements)"),
                    ("fne", "FNE (Facture Normalisée Électronique)"),
                    ("simplified", "Régime Simplifié"),
                    ("real", "Régime Réel"),
                ],
                default="",
                help_text="Tax regime (RNE, FNE, etc.)",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="dgi_api_key",
            field=models.CharField(
                blank=True,
                help_text="DGI API key (encrypted in production)",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="dgi_api_secret",
            field=models.CharField(
                blank=True,
                help_text="DGI API secret (encrypted in production)",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="dgi_is_production",
            field=models.BooleanField(
                default=False,
                help_text="Use production DGI API (vs sandbox)",
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="default_tax_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=18.00,
                help_text="Default tax rate (Ivory Coast VAT is 18%)",
                max_digits=5,
            ),
        ),
        # Food-specific feature flags
        migrations.AddField(
            model_name="business",
            name="has_kitchen_display",
            field=models.BooleanField(
                default=False,
                help_text="Enable kitchen display system",
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="has_table_service",
            field=models.BooleanField(
                default=False,
                help_text="Enable table management",
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="has_delivery",
            field=models.BooleanField(
                default=False,
                help_text="Enable delivery features",
            ),
        ),
        # Multi-location support fields (ForeignKey to locations app - nullable)
        migrations.AddField(
            model_name="business",
            name="brand",
            field=models.ForeignKey(
                blank=True,
                help_text="Parent brand for chain businesses",
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="locations",
                to="locations.brand",
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="location_group",
            field=models.ForeignKey(
                blank=True,
                help_text="Group this location belongs to (region, city, etc.)",
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="locations",
                to="locations.locationgroup",
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="location_code",
            field=models.CharField(
                blank=True,
                help_text="Internal location code for the brand",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="is_flagship",
            field=models.BooleanField(
                default=False,
                help_text="Is this the flagship/main location for the brand",
            ),
        ),
    ]
