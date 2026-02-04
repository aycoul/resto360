"""
Social Media Automation Serializers
"""

from rest_framework import serializers

from .models import (
    AICaption,
    ContentCalendar,
    PostMedia,
    PostPublish,
    PostTemplate,
    SocialAccount,
    SocialAnalytics,
    SocialPost,
)


class SocialAccountSerializer(serializers.ModelSerializer):
    """Serializer for social accounts."""

    platform_display = serializers.CharField(source="get_platform_display", read_only=True)
    is_token_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = SocialAccount
        fields = [
            "id",
            "platform",
            "platform_display",
            "account_name",
            "account_id",
            "profile_picture_url",
            "is_active",
            "is_token_expired",
            "connected_at",
            "last_sync_at",
        ]


class PostTemplateSerializer(serializers.ModelSerializer):
    """Serializer for post templates."""

    post_type_display = serializers.CharField(source="get_post_type_display", read_only=True)

    class Meta:
        model = PostTemplate
        fields = [
            "id",
            "name",
            "description",
            "post_type",
            "post_type_display",
            "caption_template",
            "hashtags",
            "background_color",
            "text_color",
            "accent_color",
            "font_style",
            "show_price",
            "show_logo",
            "overlay_opacity",
            "is_default",
            "created_at",
        ]


class PostTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating templates."""

    class Meta:
        model = PostTemplate
        fields = [
            "name",
            "description",
            "post_type",
            "caption_template",
            "hashtags",
            "background_color",
            "text_color",
            "accent_color",
            "font_style",
            "show_price",
            "show_logo",
            "overlay_opacity",
            "is_default",
        ]


class PostMediaSerializer(serializers.ModelSerializer):
    """Serializer for post media."""

    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia
        fields = [
            "id",
            "media_type",
            "file",
            "file_url",
            "thumbnail",
            "thumbnail_url",
            "is_generated",
            "display_order",
        ]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None


class PostPublishSerializer(serializers.ModelSerializer):
    """Serializer for post publishes."""

    platform = serializers.CharField(source="account.platform", read_only=True)
    platform_display = serializers.CharField(source="account.get_platform_display", read_only=True)
    account_name = serializers.CharField(source="account.account_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PostPublish
        fields = [
            "id",
            "account",
            "platform",
            "platform_display",
            "account_name",
            "platform_post_id",
            "platform_url",
            "status",
            "status_display",
            "published_at",
            "error_message",
            "likes",
            "comments",
            "shares",
            "views",
            "reach",
            "engagement_rate",
            "last_stats_update",
        ]


class SocialPostListSerializer(serializers.ModelSerializer):
    """Serializer for post list view."""

    post_type_display = serializers.CharField(source="get_post_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True, allow_null=True)
    media_count = serializers.SerializerMethodField()
    platforms = serializers.SerializerMethodField()

    class Meta:
        model = SocialPost
        fields = [
            "id",
            "caption",
            "post_type",
            "post_type_display",
            "status",
            "status_display",
            "scheduled_at",
            "published_at",
            "menu_item",
            "menu_item_name",
            "is_ai_generated",
            "media_count",
            "platforms",
            "created_at",
        ]

    def get_media_count(self, obj):
        return obj.media.count()

    def get_platforms(self, obj):
        return list(obj.publishes.values_list("account__platform", flat=True).distinct())


class SocialPostSerializer(serializers.ModelSerializer):
    """Full serializer for social posts."""

    post_type_display = serializers.CharField(source="get_post_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True, allow_null=True)
    template_name = serializers.CharField(source="template.name", read_only=True, allow_null=True)
    full_caption = serializers.CharField(read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)
    publishes = PostPublishSerializer(many=True, read_only=True)

    class Meta:
        model = SocialPost
        fields = [
            "id",
            "caption",
            "hashtags",
            "full_caption",
            "post_type",
            "post_type_display",
            "status",
            "status_display",
            "scheduled_at",
            "published_at",
            "template",
            "template_name",
            "menu_item",
            "menu_item_name",
            "is_ai_generated",
            "error_message",
            "media",
            "publishes",
            "created_at",
            "updated_at",
        ]


class SocialPostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts."""

    account_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = SocialPost
        fields = [
            "caption",
            "hashtags",
            "post_type",
            "scheduled_at",
            "template",
            "menu_item",
            "account_ids",
        ]


class ContentCalendarSerializer(serializers.ModelSerializer):
    """Serializer for content calendar."""

    post_data = SocialPostListSerializer(source="post", read_only=True)

    class Meta:
        model = ContentCalendar
        fields = [
            "id",
            "date",
            "time_slot",
            "post",
            "post_data",
            "planned_content",
            "content_type",
            "notes",
        ]


class ContentCalendarCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating calendar entries."""

    class Meta:
        model = ContentCalendar
        fields = [
            "date",
            "time_slot",
            "post",
            "planned_content",
            "content_type",
            "notes",
        ]


class AICaptionSerializer(serializers.ModelSerializer):
    """Serializer for AI captions."""

    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = AICaption
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "caption",
            "hashtags",
            "tone",
            "language",
            "is_used",
            "created_at",
        ]


class GenerateCaptionSerializer(serializers.Serializer):
    """Serializer for generating AI captions."""

    menu_item_id = serializers.UUIDField()
    tone = serializers.ChoiceField(
        choices=[
            ("professional", "Professional"),
            ("casual", "Casual"),
            ("playful", "Playful"),
            ("elegant", "Elegant"),
            ("promotional", "Promotional"),
        ],
        default="casual",
    )
    language = serializers.ChoiceField(
        choices=[("en", "English"), ("fr", "French")],
        default="en",
    )
    include_hashtags = serializers.BooleanField(default=True)


class SocialAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for social analytics."""

    platform = serializers.CharField(source="account.platform", read_only=True)
    platform_display = serializers.CharField(source="account.get_platform_display", read_only=True)

    class Meta:
        model = SocialAnalytics
        fields = [
            "id",
            "account",
            "platform",
            "platform_display",
            "date",
            "followers",
            "followers_change",
            "posts_count",
            "total_likes",
            "total_comments",
            "total_shares",
            "total_reach",
            "total_impressions",
            "engagement_rate",
        ]


class SocialDashboardSerializer(serializers.Serializer):
    """Serializer for social dashboard."""

    total_posts = serializers.IntegerField()
    scheduled_posts = serializers.IntegerField()
    published_this_month = serializers.IntegerField()
    total_engagement = serializers.IntegerField()
    accounts = SocialAccountSerializer(many=True)
    recent_posts = SocialPostListSerializer(many=True)
    top_performing = SocialPostListSerializer(many=True)


class SchedulePostSerializer(serializers.Serializer):
    """Serializer for scheduling a post."""

    scheduled_at = serializers.DateTimeField()
    account_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )
