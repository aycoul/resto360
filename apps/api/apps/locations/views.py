"""
Multi-location Support Views
"""

from django.db import models
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import Restaurant

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
from .serializers import (
    BrandAnnouncementSerializer,
    BrandCreateSerializer,
    BrandDashboardSerializer,
    BrandLocationSerializer,
    BrandManagerSerializer,
    BrandReportSerializer,
    BrandSerializer,
    LocationGroupSerializer,
    LocationItemAvailabilitySerializer,
    LocationMenuSyncSerializer,
    LocationPriceOverrideSerializer,
    SharedMenuCategorySerializer,
    SharedMenuItemSerializer,
    SharedMenuListSerializer,
    SharedMenuSerializer,
)


class BrandPermissionMixin:
    """Mixin to check brand access permissions."""

    def get_brand(self):
        """Get the brand from the user's restaurant or brand manager access."""
        user = self.request.user

        # Check if user's restaurant belongs to a brand
        if hasattr(user, "restaurant") and user.restaurant and user.restaurant.brand:
            return user.restaurant.brand

        # Check if user is a brand manager
        brand_access = BrandManager.objects.filter(
            user=user, is_active=True
        ).first()
        if brand_access:
            return brand_access.brand

        return None

    def check_brand_access(self, brand):
        """Check if user has access to the brand."""
        user = self.request.user

        # Superusers have access to all brands
        if user.is_superuser:
            return True

        # Check restaurant brand
        if hasattr(user, "restaurant") and user.restaurant:
            if user.restaurant.brand == brand:
                return True

        # Check brand manager access
        return BrandManager.objects.filter(
            user=user, brand=brand, is_active=True
        ).exists()


class BrandDashboardView(BrandPermissionMixin, APIView):
    """Brand dashboard with aggregate metrics."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        brand = self.get_brand()
        if not brand:
            return Response(
                {"detail": "No brand access"},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Get brand locations
        locations = Restaurant.objects.filter(brand=brand)
        total_locations = locations.count()
        active_locations = locations.filter(is_active=True).count()

        # Get recent announcements
        recent_announcements = BrandAnnouncement.objects.filter(
            brand=brand,
            is_active=True,
            publish_at__lte=now,
        ).order_by("-publish_at")[:5]

        # Top locations by revenue (placeholder - would need order data)
        top_locations = locations.filter(is_active=True)[:5]

        data = {
            "brand": brand,
            "total_locations": total_locations,
            "active_locations": active_locations,
            "total_orders_today": 0,  # Would aggregate from orders
            "total_revenue_today": 0,
            "total_orders_month": 0,
            "total_revenue_month": 0,
            "recent_announcements": recent_announcements,
            "top_locations": top_locations,
        }

        serializer = BrandDashboardSerializer(data)
        return Response(serializer.data)


class BrandViewSet(BrandPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for brands."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Superusers see all brands
        if user.is_superuser:
            return Brand.objects.all()

        # Get brands user has access to
        brand_ids = []

        # Check restaurant brand
        if hasattr(user, "restaurant") and user.restaurant and user.restaurant.brand:
            brand_ids.append(user.restaurant.brand_id)

        # Check brand manager access
        manager_brands = BrandManager.objects.filter(
            user=user, is_active=True
        ).values_list("brand_id", flat=True)
        brand_ids.extend(manager_brands)

        return Brand.objects.filter(id__in=brand_ids)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BrandCreateSerializer
        return BrandSerializer

    @action(detail=True, methods=["get"])
    def locations(self, request, pk=None):
        """List all locations for a brand."""
        brand = self.get_object()
        locations = Restaurant.objects.filter(brand=brand)

        # Filter by active status
        is_active = request.query_params.get("is_active")
        if is_active is not None:
            locations = locations.filter(is_active=is_active.lower() == "true")

        # Filter by group
        group_id = request.query_params.get("group")
        if group_id:
            locations = locations.filter(location_group_id=group_id)

        serializer = BrandLocationSerializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def reports(self, request, pk=None):
        """Get brand reports."""
        brand = self.get_object()
        report_type = request.query_params.get("type", "daily")
        days = int(request.query_params.get("days", 30))

        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)

        reports = BrandReport.objects.filter(
            brand=brand,
            report_type=report_type,
            date__gte=start_date,
            date__lte=end_date,
        )

        serializer = BrandReportSerializer(reports, many=True)
        return Response(serializer.data)


class BrandManagerViewSet(BrandPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for brand managers."""

    permission_classes = [IsAuthenticated]
    serializer_class = BrandManagerSerializer

    def get_queryset(self):
        brand = self.get_brand()
        if not brand:
            return BrandManager.objects.none()
        return BrandManager.objects.filter(brand=brand)

    def perform_create(self, serializer):
        brand = self.get_brand()
        if brand:
            serializer.save(brand=brand)


class LocationGroupViewSet(BrandPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for location groups."""

    permission_classes = [IsAuthenticated]
    serializer_class = LocationGroupSerializer

    def get_queryset(self):
        brand = self.get_brand()
        if not brand:
            return LocationGroup.objects.none()
        return LocationGroup.objects.filter(brand=brand)

    def perform_create(self, serializer):
        brand = self.get_brand()
        if brand:
            serializer.save(brand=brand)


class SharedMenuViewSet(BrandPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for shared menus."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        brand = self.get_brand()
        if not brand:
            return SharedMenu.objects.none()
        return SharedMenu.objects.filter(brand=brand).prefetch_related(
            "categories__items"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return SharedMenuListSerializer
        return SharedMenuSerializer

    def perform_create(self, serializer):
        brand = self.get_brand()
        if brand:
            serializer.save(brand=brand)

    @action(detail=True, methods=["post"])
    def sync_to_location(self, request, pk=None):
        """Sync shared menu to a location."""
        shared_menu = self.get_object()
        restaurant_id = request.data.get("restaurant_id")

        try:
            restaurant = Restaurant.objects.get(
                id=restaurant_id,
                brand=shared_menu.brand,
            )
        except Restaurant.DoesNotExist:
            return Response(
                {"detail": "Location not found or not part of this brand"},
                status=status.HTTP_404_NOT_FOUND,
            )

        sync, created = LocationMenuSync.objects.update_or_create(
            restaurant=restaurant,
            shared_menu=shared_menu,
            defaults={
                "is_active": True,
                "last_synced_at": timezone.now(),
            },
        )

        # Here we would sync the actual menu items
        # This is a placeholder for the sync logic
        serializer = LocationMenuSyncSerializer(sync)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def synced_locations(self, request, pk=None):
        """Get locations synced to this menu."""
        shared_menu = self.get_object()
        syncs = LocationMenuSync.objects.filter(
            shared_menu=shared_menu, is_active=True
        ).select_related("restaurant")

        serializer = LocationMenuSyncSerializer(syncs, many=True)
        return Response(serializer.data)


class SharedMenuCategoryViewSet(BrandPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for shared menu categories."""

    permission_classes = [IsAuthenticated]
    serializer_class = SharedMenuCategorySerializer

    def get_queryset(self):
        brand = self.get_brand()
        if not brand:
            return SharedMenuCategory.objects.none()
        return SharedMenuCategory.objects.filter(
            shared_menu__brand=brand
        ).select_related("shared_menu")


class SharedMenuItemViewSet(BrandPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for shared menu items."""

    permission_classes = [IsAuthenticated]
    serializer_class = SharedMenuItemSerializer

    def get_queryset(self):
        brand = self.get_brand()
        if not brand:
            return SharedMenuItem.objects.none()
        return SharedMenuItem.objects.filter(
            category__shared_menu__brand=brand
        ).select_related("category__shared_menu")


class LocationPriceOverrideViewSet(viewsets.ModelViewSet):
    """ViewSet for location price overrides."""

    permission_classes = [IsAuthenticated]
    serializer_class = LocationPriceOverrideSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "restaurant") and user.restaurant:
            return LocationPriceOverride.objects.filter(
                restaurant=user.restaurant
            ).select_related("menu_item")
        return LocationPriceOverride.objects.none()

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class LocationItemAvailabilityViewSet(viewsets.ModelViewSet):
    """ViewSet for item availability at locations."""

    permission_classes = [IsAuthenticated]
    serializer_class = LocationItemAvailabilitySerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "restaurant") and user.restaurant:
            return LocationItemAvailability.objects.filter(
                restaurant=user.restaurant
            ).select_related("menu_item")
        return LocationItemAvailability.objects.none()

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class BrandAnnouncementViewSet(BrandPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for brand announcements."""

    permission_classes = [IsAuthenticated]
    serializer_class = BrandAnnouncementSerializer

    def get_queryset(self):
        brand = self.get_brand()
        if not brand:
            return BrandAnnouncement.objects.none()
        return BrandAnnouncement.objects.filter(brand=brand).prefetch_related(
            "target_groups"
        )

    def perform_create(self, serializer):
        brand = self.get_brand()
        if brand:
            serializer.save(brand=brand)

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get active announcements for current location."""
        brand = self.get_brand()
        if not brand:
            return Response([])

        now = timezone.now()
        announcements = BrandAnnouncement.objects.filter(
            brand=brand,
            is_active=True,
            publish_at__lte=now,
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )

        # Filter by location group if applicable
        user = request.user
        if hasattr(user, "restaurant") and user.restaurant and user.restaurant.location_group:
            announcements = announcements.filter(
                models.Q(target_groups__isnull=True)
                | models.Q(target_groups=user.restaurant.location_group)
            ).distinct()

        serializer = self.get_serializer(announcements, many=True)
        return Response(serializer.data)
