"""Serializers for reviews app."""

from rest_framework import serializers

from .models import (
    FeedbackRequest,
    Review,
    ReviewPhoto,
    ReviewResponse,
    ReviewSettings,
    ReviewStatus,
    ReviewSummary,
)


class ReviewPhotoSerializer(serializers.ModelSerializer):
    """Serializer for review photos."""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ReviewPhoto
        fields = ["id", "image", "image_url", "caption", "display_order"]
        read_only_fields = ["id", "image_url"]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ReviewResponseSerializer(serializers.ModelSerializer):
    """Serializer for review responses."""

    class Meta:
        model = ReviewResponse
        fields = ["id", "content", "responder_name", "created_at"]
        read_only_fields = ["id", "created_at"]


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviews."""

    photos = ReviewPhotoSerializer(many=True, read_only=True)
    response = ReviewResponseSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    has_response = serializers.BooleanField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "rating",
            "title",
            "content",
            "reviewer_name",
            "reviewer_email",
            "is_verified",
            "visit_date",
            "food_rating",
            "service_rating",
            "ambiance_rating",
            "value_rating",
            "status",
            "status_display",
            "source",
            "source_display",
            "is_featured",
            "photos",
            "response",
            "has_response",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "is_verified",
            "status",
            "source",
            "is_featured",
            "created_at",
        ]


class PublicReviewSerializer(serializers.ModelSerializer):
    """Serializer for public review display (limited fields)."""

    photos = ReviewPhotoSerializer(many=True, read_only=True)
    response = ReviewResponseSerializer(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "rating",
            "title",
            "content",
            "reviewer_name",
            "is_verified",
            "visit_date",
            "food_rating",
            "service_rating",
            "ambiance_rating",
            "value_rating",
            "is_featured",
            "photos",
            "response",
            "created_at",
        ]


class CreateReviewSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""

    class Meta:
        model = Review
        fields = [
            "rating",
            "title",
            "content",
            "reviewer_name",
            "reviewer_email",
            "reviewer_phone",
            "visit_date",
            "food_rating",
            "service_rating",
            "ambiance_rating",
            "value_rating",
        ]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class CreateReviewResponseSerializer(serializers.ModelSerializer):
    """Serializer for creating review responses."""

    class Meta:
        model = ReviewResponse
        fields = ["content", "responder_name"]


class ModerateReviewSerializer(serializers.Serializer):
    """Serializer for moderating reviews."""

    status = serializers.ChoiceField(choices=ReviewStatus.choices)
    moderation_notes = serializers.CharField(required=False, allow_blank=True)


class ReviewSettingsSerializer(serializers.ModelSerializer):
    """Serializer for review settings."""

    class Meta:
        model = ReviewSettings
        fields = [
            "auto_approve",
            "min_rating_auto_approve",
            "auto_request_feedback",
            "request_delay_hours",
            "request_channel",
            "show_reviews_on_menu",
            "min_reviews_to_show",
            "show_average_rating",
            "response_template",
        ]


class ReviewSummarySerializer(serializers.ModelSerializer):
    """Serializer for review summary."""

    class Meta:
        model = ReviewSummary
        fields = [
            "total_reviews",
            "average_rating",
            "rating_distribution",
            "avg_food_rating",
            "avg_service_rating",
            "avg_ambiance_rating",
            "avg_value_rating",
            "response_rate",
            "last_updated",
        ]


class FeedbackRequestSerializer(serializers.ModelSerializer):
    """Serializer for feedback requests."""

    class Meta:
        model = FeedbackRequest
        fields = [
            "id",
            "customer_name",
            "customer_email",
            "customer_phone",
            "channel",
            "sent_at",
            "opened_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "sent_at",
            "opened_at",
            "completed_at",
            "created_at",
        ]


class CreateFeedbackRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating feedback requests."""

    class Meta:
        model = FeedbackRequest
        fields = [
            "customer_name",
            "customer_email",
            "customer_phone",
            "order_id",
            "reservation_id",
            "channel",
        ]

    def validate(self, data):
        if not data.get("customer_email") and not data.get("customer_phone"):
            raise serializers.ValidationError(
                "Either email or phone must be provided"
            )
        if data.get("channel") == "email" and not data.get("customer_email"):
            raise serializers.ValidationError(
                {"customer_email": "Email required for email channel"}
            )
        if data.get("channel") == "sms" and not data.get("customer_phone"):
            raise serializers.ValidationError(
                {"customer_phone": "Phone required for SMS channel"}
            )
        return data


class SubmitFeedbackSerializer(serializers.Serializer):
    """Serializer for submitting feedback via token."""

    token = serializers.CharField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    food_rating = serializers.IntegerField(
        min_value=1, max_value=5, required=False, allow_null=True
    )
    service_rating = serializers.IntegerField(
        min_value=1, max_value=5, required=False, allow_null=True
    )
    ambiance_rating = serializers.IntegerField(
        min_value=1, max_value=5, required=False, allow_null=True
    )
    value_rating = serializers.IntegerField(
        min_value=1, max_value=5, required=False, allow_null=True
    )
