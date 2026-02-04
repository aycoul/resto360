# Generated manually for Phase 7: Menu Metadata

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0002_alter_category_managers_alter_menuitem_managers_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='allergens',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[
                        ('celery', 'Celery'),
                        ('gluten', 'Gluten'),
                        ('crustaceans', 'Crustaceans'),
                        ('eggs', 'Eggs'),
                        ('fish', 'Fish'),
                        ('lupin', 'Lupin'),
                        ('milk', 'Milk'),
                        ('molluscs', 'Molluscs'),
                        ('mustard', 'Mustard'),
                        ('nuts', 'Tree Nuts'),
                        ('peanuts', 'Peanuts'),
                        ('sesame', 'Sesame'),
                        ('soya', 'Soya'),
                        ('sulphites', 'Sulphites'),
                    ],
                    max_length=20,
                ),
                blank=True,
                default=list,
                help_text='List of allergens present in this item',
                size=None,
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='dietary_tags',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[
                        ('vegan', 'Vegan'),
                        ('vegetarian', 'Vegetarian'),
                        ('gluten_free', 'Gluten-Free'),
                        ('dairy_free', 'Dairy-Free'),
                        ('halal', 'Halal'),
                        ('kosher', 'Kosher'),
                        ('keto', 'Keto-Friendly'),
                        ('low_carb', 'Low Carb'),
                        ('nut_free', 'Nut-Free'),
                        ('organic', 'Organic'),
                    ],
                    max_length=20,
                ),
                blank=True,
                default=list,
                help_text='Dietary certifications/tags for this item',
                size=None,
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='spice_level',
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, 'Not Spicy'),
                    (1, 'Mild'),
                    (2, 'Medium'),
                    (3, 'Hot'),
                    (4, 'Very Hot'),
                ],
                default=0,
                help_text='Spice/heat level of the dish',
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='prep_time_minutes',
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text='Estimated preparation time in minutes',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='calories',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Calories per serving (kcal)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='protein_grams',
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text='Protein per serving (grams)',
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='carbs_grams',
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text='Carbohydrates per serving (grams)',
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='fat_grams',
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text='Fat per serving (grams)',
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='fiber_grams',
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text='Fiber per serving (grams)',
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='sodium_mg',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Sodium per serving (milligrams)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='ingredients',
            field=models.TextField(
                blank=True,
                help_text='Comma-separated list of main ingredients',
            ),
        ),
    ]
