"""Serializers for AI app."""

from rest_framework import serializers

from .models import AIJob, AIUsage, MenuImportBatch


class AIJobSerializer(serializers.ModelSerializer):
    """Serializer for AI job tracking."""

    class Meta:
        model = AIJob
        fields = [
            "id",
            "job_type",
            "status",
            "input_data",
            "output_data",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "output_data",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
        ]


class AIUsageSerializer(serializers.ModelSerializer):
    """Serializer for AI usage tracking."""

    class Meta:
        model = AIUsage
        fields = [
            "id",
            "job_type",
            "model_used",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "estimated_cost_cents",
            "created_at",
        ]
        read_only_fields = fields


class MenuImportBatchSerializer(serializers.ModelSerializer):
    """Serializer for menu import batches."""

    class Meta:
        model = MenuImportBatch
        fields = [
            "id",
            "source_type",
            "original_filename",
            "status",
            "items",
            "errors",
            "total_items",
            "valid_items",
            "created_items",
            "created_at",
            "confirmed_at",
        ]
        read_only_fields = [
            "id",
            "source_type",
            "original_filename",
            "errors",
            "total_items",
            "valid_items",
            "created_items",
            "created_at",
            "confirmed_at",
        ]


class GenerateDescriptionSerializer(serializers.Serializer):
    """Input for generating item description."""

    item_name = serializers.CharField(max_length=200)
    category = serializers.CharField(max_length=100)
    ingredients = serializers.CharField(required=False, allow_blank=True)
    cuisine_type = serializers.CharField(default="West African")
    language = serializers.ChoiceField(choices=[("en", "English"), ("fr", "French")], default="en")


class PhotoAnalysisSerializer(serializers.Serializer):
    """Input for photo analysis."""

    image = serializers.ImageField()


class MenuOCRSerializer(serializers.Serializer):
    """Input for menu OCR extraction."""

    image = serializers.ImageField()
    language = serializers.ChoiceField(choices=[("en", "English"), ("fr", "French")], default="en")


class BulkImportSerializer(serializers.Serializer):
    """Input for bulk menu import."""

    file = serializers.FileField()


class TranslateItemSerializer(serializers.Serializer):
    """Input for translating a menu item."""

    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    source_lang = serializers.ChoiceField(
        choices=[("en", "English"), ("fr", "French"), ("wo", "Wolof"), ("ar", "Arabic")],
    )
    target_lang = serializers.ChoiceField(
        choices=[("en", "English"), ("fr", "French"), ("wo", "Wolof"), ("ar", "Arabic")],
    )


class TranslateMenuSerializer(serializers.Serializer):
    """Input for translating entire menu."""

    source_lang = serializers.ChoiceField(
        choices=[("en", "English"), ("fr", "French"), ("wo", "Wolof"), ("ar", "Arabic")],
    )
    target_lang = serializers.ChoiceField(
        choices=[("en", "English"), ("fr", "French"), ("wo", "Wolof"), ("ar", "Arabic")],
    )
    items = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="If not provided, translates all menu items",
    )


class PriceSuggestionSerializer(serializers.Serializer):
    """Input for price suggestion."""

    item_name = serializers.CharField(max_length=200)
    category = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(default="Dakar, Senegal")
    currency = serializers.CharField(default="XOF")


class ImportConfirmSerializer(serializers.Serializer):
    """Confirm a menu import batch."""

    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="Items to import (can be modified from original)",
    )
    category_id = serializers.UUIDField(
        required=False,
        help_text="Default category for items without category",
    )
    create_categories = serializers.BooleanField(
        default=True,
        help_text="Auto-create categories from import data",
    )
