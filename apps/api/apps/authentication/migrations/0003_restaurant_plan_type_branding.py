# Generated for 05.5-01 plan - RESTO360 Lite

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_restaurant_location_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="restaurant",
            name="plan_type",
            field=models.CharField(
                choices=[("free", "Free"), ("pro", "Pro"), ("full", "Full Platform")],
                default="free",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="restaurant",
            name="logo",
            field=models.ImageField(
                blank=True, null=True, upload_to="restaurant_logos/"
            ),
        ),
        migrations.AddField(
            model_name="restaurant",
            name="primary_color",
            field=models.CharField(
                blank=True, help_text="Hex color code", max_length=7
            ),
        ),
        migrations.AddField(
            model_name="restaurant",
            name="show_branding",
            field=models.BooleanField(
                default=True, help_text="Show RESTO360 branding on free tier"
            ),
        ),
    ]
