# Generated manually for Phase 8: Menu Templates & Theming

import django.db.models.manager
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
        ('menu', '0003_add_menu_metadata'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuTheme',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True, help_text='Only one theme can be active per restaurant')),
                ('template', models.CharField(
                    choices=[
                        ('minimalist', 'Minimalist'),
                        ('elegant', 'Elegant'),
                        ('modern', 'Modern'),
                        ('casual', 'Casual'),
                        ('fine_dining', 'Fine Dining'),
                        ('vibrant', 'Vibrant'),
                    ],
                    default='minimalist',
                    max_length=20,
                )),
                ('primary_color', models.CharField(default='#059669', help_text='Primary brand color (hex, e.g., #059669)', max_length=7)),
                ('secondary_color', models.CharField(default='#14b8a6', help_text='Secondary color for accents', max_length=7)),
                ('background_color', models.CharField(default='#ffffff', help_text='Page background color', max_length=7)),
                ('text_color', models.CharField(default='#111827', help_text='Main text color', max_length=7)),
                ('heading_font', models.CharField(
                    choices=[
                        ('inter', 'Inter'),
                        ('playfair', 'Playfair Display'),
                        ('roboto', 'Roboto'),
                        ('lato', 'Lato'),
                        ('montserrat', 'Montserrat'),
                        ('merriweather', 'Merriweather'),
                        ('open_sans', 'Open Sans'),
                        ('poppins', 'Poppins'),
                    ],
                    default='inter',
                    max_length=20,
                )),
                ('body_font', models.CharField(
                    choices=[
                        ('inter', 'Inter'),
                        ('playfair', 'Playfair Display'),
                        ('roboto', 'Roboto'),
                        ('lato', 'Lato'),
                        ('montserrat', 'Montserrat'),
                        ('merriweather', 'Merriweather'),
                        ('open_sans', 'Open Sans'),
                        ('poppins', 'Poppins'),
                    ],
                    default='inter',
                    max_length=20,
                )),
                ('logo', models.ImageField(blank=True, null=True, upload_to='menu_themes/logos/')),
                ('cover_image', models.ImageField(blank=True, help_text='Hero image for menu header', null=True, upload_to='menu_themes/covers/')),
                ('logo_position', models.CharField(
                    choices=[('left', 'Left'), ('center', 'Center'), ('right', 'Right')],
                    default='center',
                    max_length=10,
                )),
                ('show_prices', models.BooleanField(default=True)),
                ('show_descriptions', models.BooleanField(default=True)),
                ('show_images', models.BooleanField(default=True)),
                ('compact_mode', models.BooleanField(default=False, help_text='Display items in a more compact format')),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='menu_themes', to='authentication.restaurant')),
            ],
            options={
                'verbose_name': 'Menu Theme',
                'verbose_name_plural': 'Menu Themes',
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
