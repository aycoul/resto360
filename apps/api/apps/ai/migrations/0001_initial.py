# Generated manually for Phase 9: AI Menu Builder

import django.contrib.postgres.fields
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
            name='AIJob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('job_type', models.CharField(choices=[
                    ('description', 'Generate Description'),
                    ('photo_analysis', 'Photo Analysis'),
                    ('menu_ocr', 'Menu OCR Import'),
                    ('bulk_import', 'Bulk Import'),
                    ('translation', 'Translation'),
                    ('price_suggestion', 'Price Suggestion'),
                ], max_length=20)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed'),
                ], default='pending', max_length=20)),
                ('input_data', models.JSONField(blank=True, default=dict)),
                ('output_data', models.JSONField(blank=True, default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('celery_task_id', models.CharField(blank=True, max_length=255)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_jobs', to='authentication.restaurant')),
            ],
            options={
                'verbose_name': 'AI Job',
                'verbose_name_plural': 'AI Jobs',
                'ordering': ['-created_at'],
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='AIUsage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('job_type', models.CharField(choices=[
                    ('description', 'Generate Description'),
                    ('photo_analysis', 'Photo Analysis'),
                    ('menu_ocr', 'Menu OCR Import'),
                    ('bulk_import', 'Bulk Import'),
                    ('translation', 'Translation'),
                    ('price_suggestion', 'Price Suggestion'),
                ], max_length=20)),
                ('model_used', models.CharField(max_length=50)),
                ('prompt_tokens', models.IntegerField(default=0)),
                ('completion_tokens', models.IntegerField(default=0)),
                ('total_tokens', models.IntegerField(default=0)),
                ('estimated_cost_cents', models.IntegerField(default=0)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usage_records', to='ai.aijob')),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_usage', to='authentication.restaurant')),
            ],
            options={
                'verbose_name': 'AI Usage',
                'verbose_name_plural': 'AI Usage Records',
                'ordering': ['-created_at'],
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='MenuImportBatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source_type', models.CharField(choices=[
                    ('csv', 'CSV File'),
                    ('excel', 'Excel File'),
                    ('ocr', 'Menu Photo OCR'),
                    ('manual', 'Manual Entry'),
                ], max_length=20)),
                ('original_filename', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending Review'),
                    ('confirmed', 'Confirmed'),
                    ('cancelled', 'Cancelled'),
                ], default='pending', max_length=20)),
                ('items', models.JSONField(default=list)),
                ('errors', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, default=list, size=None)),
                ('total_items', models.IntegerField(default=0)),
                ('valid_items', models.IntegerField(default=0)),
                ('created_items', models.IntegerField(default=0)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='menu_imports', to='authentication.restaurant')),
            ],
            options={
                'verbose_name': 'Menu Import Batch',
                'verbose_name_plural': 'Menu Import Batches',
                'ordering': ['-created_at'],
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
