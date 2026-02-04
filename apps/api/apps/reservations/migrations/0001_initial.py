# Generated manually for Phase 10: Reservations System

import django.db.models.deletion
import django.db.models.manager
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TableConfiguration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text="Table identifier (e.g., 'Table 1', 'Booth A')", max_length=50)),
                ('capacity', models.PositiveIntegerField(help_text='Maximum number of guests')),
                ('min_capacity', models.PositiveIntegerField(default=1, help_text='Minimum number of guests')),
                ('location', models.CharField(blank=True, help_text="Location in restaurant (e.g., 'Indoor', 'Terrace')", max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='table_configurations', to='authentication.restaurant')),
            ],
            options={
                'verbose_name': 'Table',
                'verbose_name_plural': 'Tables',
                'ordering': ['display_order', 'name'],
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='ReservationSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('min_advance_hours', models.PositiveIntegerField(default=1, help_text='Minimum hours in advance')),
                ('max_advance_days', models.PositiveIntegerField(default=30, help_text='Maximum days in advance')),
                ('slot_duration_minutes', models.PositiveIntegerField(default=30, help_text='Duration of each time slot')),
                ('default_dining_duration_minutes', models.PositiveIntegerField(default=90, help_text='Default dining duration')),
                ('max_party_size', models.PositiveIntegerField(default=10, help_text='Maximum party size')),
                ('require_phone', models.BooleanField(default=True)),
                ('require_email', models.BooleanField(default=False)),
                ('confirmation_required', models.BooleanField(default=False)),
                ('cancellation_hours', models.PositiveIntegerField(default=2)),
                ('no_show_threshold', models.PositiveIntegerField(default=3)),
                ('confirmation_message', models.TextField(blank=True)),
                ('reminder_hours', models.PositiveIntegerField(default=24)),
                ('restaurant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='reservation_settings', to='authentication.restaurant')),
            ],
            options={
                'verbose_name': 'Reservation Settings',
                'verbose_name_plural': 'Reservation Settings',
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='BusinessHours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('day_of_week', models.PositiveIntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')])),
                ('is_open', models.BooleanField(default=True)),
                ('open_time', models.TimeField(blank=True, null=True)),
                ('close_time', models.TimeField(blank=True, null=True)),
                ('last_seating_time', models.TimeField(blank=True, help_text='Last time reservations accepted', null=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='business_hours', to='authentication.restaurant')),
            ],
            options={
                'verbose_name': 'Business Hours',
                'verbose_name_plural': 'Business Hours',
                'ordering': ['day_of_week', 'open_time'],
                'unique_together': {('restaurant', 'day_of_week', 'open_time')},
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='SpecialHours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('is_closed', models.BooleanField(default=False)),
                ('open_time', models.TimeField(blank=True, null=True)),
                ('close_time', models.TimeField(blank=True, null=True)),
                ('reason', models.CharField(blank=True, max_length=100)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='special_hours', to='authentication.restaurant')),
            ],
            options={
                'verbose_name': 'Special Hours',
                'verbose_name_plural': 'Special Hours',
                'ordering': ['date'],
                'unique_together': {('restaurant', 'date')},
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('time', models.TimeField()),
                ('duration_minutes', models.PositiveIntegerField(default=90)),
                ('party_size', models.PositiveIntegerField()),
                ('customer_name', models.CharField(max_length=100)),
                ('customer_phone', models.CharField(blank=True, max_length=20)),
                ('customer_email', models.EmailField(blank=True, max_length=254)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending Confirmation'),
                    ('confirmed', 'Confirmed'),
                    ('seated', 'Seated'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled'),
                    ('no_show', 'No Show'),
                ], default='pending', max_length=20)),
                ('source', models.CharField(choices=[
                    ('online', 'Online Booking'),
                    ('phone', 'Phone'),
                    ('walk_in', 'Walk-in'),
                    ('third_party', 'Third Party'),
                ], default='online', max_length=20)),
                ('special_requests', models.TextField(blank=True)),
                ('occasion', models.CharField(blank=True, max_length=50)),
                ('confirmation_code', models.CharField(editable=False, max_length=10, unique=True)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('seated_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('cancellation_reason', models.TextField(blank=True)),
                ('reminder_sent', models.BooleanField(default=False)),
                ('confirmation_sent', models.BooleanField(default=False)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='authentication.restaurant')),
                ('table', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservations', to='reservations.tableconfiguration')),
            ],
            options={
                'verbose_name': 'Reservation',
                'verbose_name_plural': 'Reservations',
                'ordering': ['date', 'time'],
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddIndex(
            model_name='reservation',
            index=models.Index(fields=['restaurant', 'date', 'status'], name='reservation_restaur_9e2f3c_idx'),
        ),
        migrations.AddIndex(
            model_name='reservation',
            index=models.Index(fields=['confirmation_code'], name='reservation_confirm_d4c1e2_idx'),
        ),
        migrations.CreateModel(
            name='Waitlist',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer_name', models.CharField(max_length=100)),
                ('customer_phone', models.CharField(max_length=20)),
                ('party_size', models.PositiveIntegerField()),
                ('is_notified', models.BooleanField(default=False)),
                ('is_seated', models.BooleanField(default=False)),
                ('is_cancelled', models.BooleanField(default=False)),
                ('estimated_wait_minutes', models.PositiveIntegerField(blank=True, null=True)),
                ('notified_at', models.DateTimeField(blank=True, null=True)),
                ('seated_at', models.DateTimeField(blank=True, null=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='waitlist_entries', to='authentication.restaurant')),
                ('reservation', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='waitlist_entry', to='reservations.reservation')),
            ],
            options={
                'verbose_name': 'Waitlist Entry',
                'verbose_name_plural': 'Waitlist',
                'ordering': ['created_at'],
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
