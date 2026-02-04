"""
Multi-location Support Serializers
"""

from rest_framework import serializers

from .models import (
    Brand,
    BrandAnnouncement,
    BrandManager,
    BrandReport,
    LocationGroup,
    LocationItemAvailability,
    LocationMenuSync,
    LocationPriceOverride,
    SharedMenu,
    SharedMenuCategory,
    SharedMenuItem,
)


class BrandSerializer(serializers.ModelSerializer):
    """Serializer for Brand model."""

    location_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "email",
            "phone",
            "website",
            "logo",
            "cover_image",
            "primary_color",
            "secondary_color",
            "default_timezone",
            "default_currency",
            "default_language",
            "plan_type",
            "max_locations",
            "owner_name",
            "owner_email",
            "owner_phone",
            "is_active",
            "location_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "location_count"]


class BrandCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a brand."""

    class Meta:
        model = Brand
        fields = [
            "name",
            "slug",
            "description",
            "email",
            "phone",
            "website",
            "logo",
            "primary_color",
            "secondary_color",
            "default_timezone",
            "default_currency",
            "default_language",
            "owner_name",
            "owner_email",
            "owner_phone",
        ]


class BrandManagerSerializer(serializers.ModelSerializer):
    """Serializer for brand managers."""

    user_name = serializers.CharField(source="user.name", read_only=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)

    class Meta:
        model = BrandManager
        fields = [
            "id",
            "brand",
            "brand_name",
            "user",
            "user_name",
            "user_phone",
            "role",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class LocationGroupSerializer(serializers.ModelSerializer):
    """Serializer for location groups."""

    location_count = serializers.SerializerMethodField()

    class Meta:
        model = LocationGroup
        fields = [
            "id",
            "brand",
            "name",
            "description",
            "display_order",
            "location_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_location_count(self, obj):
        return obj.locations.filter(is_active=True).count()


class LocationPriceOverrideSerializer(serializers.ModelSerializer):
    """Serializer for price overrides."""

    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    base_price = serializers.DecimalField(
        source="menu_item.price",
        max_digits=10,
        decimal_places=0,
        read_only=True,
    )

    class Meta:
        model = LocationPriceOverride
        fields = [
            "id",
            "restaurant",
            "restaurant_name",
            "menu_item",
            "menu_item_name",
            "base_price",
            "price",
            "is_active",
            "reason",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class LocationItemAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for item availability."""

    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = LocationItemAvailability
        fields = [
            "id",
            "restaurant",
            "restaurant_name",
            "menu_item",
            "menu_item_name",
            "is_available",
            "unavailable_until",
            "reason",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SharedMenuItemSerializer(serializers.ModelSerializer):
    """Serializer for shared menu items."""

    class Meta:
        model = SharedMenuItem
        fields = [
            "id",
            "category",
            "name",
            "description",
            "base_price",
            "image",
            "allergens",
            "dietary_tags",
            "calories",
            "preparation_time",
            "display_order",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SharedMenuCategorySerializer(serializers.ModelSerializer):
    """Serializer for shared menu categories."""

    items = SharedMenuItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = SharedMenuCategory
        fields = [
            "id",
            "shared_menu",
            "name",
            "description",
            "image",
            "display_order",
            "is_active",
            "items",
            "item_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_item_count(self, obj):
        return obj.items.filter(is_active=True).count()


class SharedMenuSerializer(serializers.ModelSerializer):
    """Serializer for shared menus."""

    categories = SharedMenuCategorySerializer(many=True, read_only=True)
    category_count = serializers.SerializerMethodField()
    synced_locations = serializers.SerializerMethodField()

    class Meta:
        model = SharedMenu
        fields = [
            "id",
            "brand",
            "name",
            "description",
            "is_default",
            "is_active",
            "categories",
            "category_count",
            "synced_locations",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_category_count(self, obj):
        return obj.categories.filter(is_active=True).count()

    def get_synced_locations(self, obj):
        return obj.location_syncs.filter(is_active=True).count()


class SharedMenuListSerializer(serializers.ModelSerializer):
    """Light serializer for shared menu list."""

    category_count = serializers.SerializerMethodField()
    synced_locations = serializers.SerializerMethodField()

    class Meta:
        model = SharedMenu
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "category_count",
            "synced_locations",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_category_count(self, obj):
        return obj.categories.filter(is_active=True).count()

    def get_synced_locations(self, obj):
        return obj.location_syncs.filter(is_active=True).count()


class LocationMenuSyncSerializer(serializers.ModelSerializer):
    """Serializer for menu syncs."""

    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    shared_menu_name = serializers.CharField(source="shared_menu.name", read_only=True)

    class Meta:
        model = LocationMenuSync
        fields = [
            "id",
            "restaurant",
            "restaurant_name",
            "shared_menu",
            "shared_menu_name",
            "last_synced_at",
            "auto_sync",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "last_synced_at"]


class BrandReportSerializer(serializers.ModelSerializer):
    """Serializer for brand reports."""

    brand_name = serializers.CharField(source="brand.name", read_only=True)

    class Meta:
        model = BrandReport
        fields = [
            "id",
            "brand",
            "brand_name",
            "date",
            "report_type",
            "total_orders",
            "total_revenue",
            "average_order_value",
            "total_customers",
            "location_breakdown",
            "top_items",
            "top_locations",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BrandAnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for brand announcements."""

    brand_name = serializers.CharField(source="brand.name", read_only=True)
    is_published = serializers.BooleanField(read_only=True)
    target_group_names = serializers.SerializerMethodField()

    class Meta:
        model = BrandAnnouncement
        fields = [
            "id",
            "brand",
            "brand_name",
            "title",
            "content",
            "priority",
            "target_groups",
            "target_group_names",
            "publish_at",
            "expires_at",
            "is_active",
            "is_published",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "is_published"]

    def get_target_group_names(self, obj):
        return list(obj.target_groups.values_list("name", flat=True))


class BrandLocationSerializer(serializers.Serializer):
    """Serializer for brand locations list."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    address = serializers.CharField()
    phone = serializers.CharField()
    location_code = serializers.CharField()
    location_group = serializers.CharField(
        source="location_group.name", allow_null=True
    )
    is_flagship = serializers.BooleanField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class BrandDashboardSerializer(serializers.Serializer):
    """Serializer for brand dashboard data."""

    brand = BrandSerializer()
    total_locations = serializers.IntegerField()
    active_locations = serializers.IntegerField()
    total_orders_today = serializers.IntegerField()
    total_revenue_today = serializers.DecimalField(max_digits=12, decimal_places=0)
    total_orders_month = serializers.IntegerField()
    total_revenue_month = serializers.DecimalField(max_digits=12, decimal_places=0)
    recent_announcements = BrandAnnouncementSerializer(many=True)
    top_locations = BrandLocationSerializer(many=True)
