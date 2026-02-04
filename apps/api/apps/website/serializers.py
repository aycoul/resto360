"""
Website Generator Serializers
"""

from rest_framework import serializers

from .models import (
    Website,
    WebsiteBusinessHours,
    WebsiteContactForm,
    WebsiteGalleryImage,
    WebsiteStatus,
    WebsiteTemplate,
)


class WebsiteGalleryImageSerializer(serializers.ModelSerializer):
    """Serializer for gallery images."""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = WebsiteGalleryImage
        fields = [
            "id",
            "image",
            "image_url",
            "caption",
            "alt_text",
            "display_order",
            "is_visible",
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class WebsiteBusinessHoursSerializer(serializers.ModelSerializer):
    """Serializer for business hours."""

    day_name = serializers.CharField(read_only=True)

    class Meta:
        model = WebsiteBusinessHours
        fields = [
            "id",
            "day_of_week",
            "day_name",
            "is_open",
            "open_time",
            "close_time",
            "note",
        ]


class WebsiteSerializer(serializers.ModelSerializer):
    """Full website serializer."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    template_display = serializers.CharField(source="get_template_display", read_only=True)
    public_url = serializers.CharField(read_only=True)
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    about_image_url = serializers.SerializerMethodField()
    gallery_images = WebsiteGalleryImageSerializer(many=True, read_only=True)
    business_hours = WebsiteBusinessHoursSerializer(many=True, read_only=True)

    class Meta:
        model = Website
        fields = [
            "id",
            "status",
            "status_display",
            "template",
            "template_display",
            "primary_color",
            "secondary_color",
            "background_color",
            "text_color",
            "logo",
            "logo_url",
            "favicon",
            "favicon_url",
            "cover_image",
            "cover_image_url",
            "hero_title",
            "hero_subtitle",
            "hero_cta_text",
            "hero_cta_link",
            "about_title",
            "about_text",
            "about_image",
            "about_image_url",
            "tagline",
            "description",
            "phone",
            "email",
            "address",
            "latitude",
            "longitude",
            "google_maps_embed",
            "facebook_url",
            "instagram_url",
            "twitter_url",
            "tiktok_url",
            "whatsapp_number",
            "show_menu",
            "show_reservations",
            "show_reviews",
            "show_about",
            "show_contact",
            "show_hours",
            "show_gallery",
            "show_map",
            "subdomain",
            "custom_domain",
            "custom_domain_verified",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "google_analytics_id",
            "facebook_pixel_id",
            "public_url",
            "gallery_images",
            "business_hours",
            "published_at",
            "created_at",
            "updated_at",
        ]

    def _get_url(self, obj, field_name):
        field = getattr(obj, field_name)
        if field:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(field.url)
            return field.url
        return None

    def get_logo_url(self, obj):
        return self._get_url(obj, "logo")

    def get_favicon_url(self, obj):
        return self._get_url(obj, "favicon")

    def get_cover_image_url(self, obj):
        return self._get_url(obj, "cover_image")

    def get_about_image_url(self, obj):
        return self._get_url(obj, "about_image")


class WebsiteUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating website settings."""

    class Meta:
        model = Website
        fields = [
            "template",
            "primary_color",
            "secondary_color",
            "background_color",
            "text_color",
            "logo",
            "favicon",
            "cover_image",
            "hero_title",
            "hero_subtitle",
            "hero_cta_text",
            "hero_cta_link",
            "about_title",
            "about_text",
            "about_image",
            "tagline",
            "description",
            "phone",
            "email",
            "address",
            "latitude",
            "longitude",
            "google_maps_embed",
            "facebook_url",
            "instagram_url",
            "twitter_url",
            "tiktok_url",
            "whatsapp_number",
            "show_menu",
            "show_reservations",
            "show_reviews",
            "show_about",
            "show_contact",
            "show_hours",
            "show_gallery",
            "show_map",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "google_analytics_id",
            "facebook_pixel_id",
        ]


class WebsiteContactFormSerializer(serializers.ModelSerializer):
    """Serializer for contact form submissions."""

    class Meta:
        model = WebsiteContactForm
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "subject",
            "message",
            "is_read",
            "read_at",
            "created_at",
        ]


class WebsiteContactFormCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contact form submissions."""

    class Meta:
        model = WebsiteContactForm
        fields = ["name", "email", "phone", "subject", "message"]


class PublicWebsiteSerializer(serializers.ModelSerializer):
    """Serializer for public website view."""

    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    restaurant_slug = serializers.CharField(source="restaurant.slug", read_only=True)
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    about_image_url = serializers.SerializerMethodField()
    gallery_images = WebsiteGalleryImageSerializer(many=True, read_only=True)
    business_hours = WebsiteBusinessHoursSerializer(many=True, read_only=True)

    class Meta:
        model = Website
        fields = [
            "template",
            "primary_color",
            "secondary_color",
            "background_color",
            "text_color",
            "logo_url",
            "favicon_url",
            "cover_image_url",
            "hero_title",
            "hero_subtitle",
            "hero_cta_text",
            "hero_cta_link",
            "about_title",
            "about_text",
            "about_image_url",
            "tagline",
            "description",
            "phone",
            "email",
            "address",
            "latitude",
            "longitude",
            "google_maps_embed",
            "facebook_url",
            "instagram_url",
            "twitter_url",
            "tiktok_url",
            "whatsapp_number",
            "show_menu",
            "show_reservations",
            "show_reviews",
            "show_about",
            "show_contact",
            "show_hours",
            "show_gallery",
            "show_map",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "gallery_images",
            "business_hours",
            "restaurant_name",
            "restaurant_slug",
        ]

    def _get_url(self, obj, field_name):
        field = getattr(obj, field_name)
        if field:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(field.url)
            return field.url
        return None

    def get_logo_url(self, obj):
        return self._get_url(obj, "logo")

    def get_favicon_url(self, obj):
        return self._get_url(obj, "favicon")

    def get_cover_image_url(self, obj):
        return self._get_url(obj, "cover_image")

    def get_about_image_url(self, obj):
        return self._get_url(obj, "about_image")


class TemplateChoicesSerializer(serializers.Serializer):
    """Serializer for template choices."""

    templates = serializers.ListField(child=serializers.DictField())
