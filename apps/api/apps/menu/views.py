from django.db.models import Prefetch
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.context import set_current_restaurant
from apps.core.permissions import IsOwnerOrManager
from apps.core.views import TenantModelViewSet

from .models import Category, MenuItem, Modifier, ModifierOption
from .serializers import (
    CategorySerializer,
    CategoryWriteSerializer,
    FullMenuSerializer,
    MenuItemSerializer,
    MenuItemWriteSerializer,
    ModifierOptionSerializer,
    ModifierOptionWriteSerializer,
    ModifierSerializer,
    ModifierWriteSerializer,
)


class CategoryViewSet(TenantModelViewSet):
    """ViewSet for menu categories."""

    # Note: Don't use class-level queryset with TenantManager
    # as it gets evaluated without tenant context at class load time.

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CategoryWriteSerializer
        return CategorySerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Get categories filtered by tenant and visibility."""
        # Get fresh queryset with tenant context
        qs = Category.objects.all()

        # For list/retrieve actions, filter by visibility for non-managers
        if self.action in ("list", "retrieve"):
            user = self.request.user
            if user.role not in ("owner", "manager"):
                qs = qs.filter(is_visible=True)

        # Prefetch items for efficiency
        qs = qs.prefetch_related(
            Prefetch(
                "items",
                queryset=MenuItem.all_objects.filter(is_available=True).prefetch_related(
                    Prefetch(
                        "modifiers",
                        queryset=Modifier.all_objects.prefetch_related("options"),
                    )
                ),
            )
        )
        return qs


class MenuItemViewSet(TenantModelViewSet):
    """ViewSet for menu items."""

    filterset_fields = ["category", "is_available"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return MenuItemWriteSerializer
        return MenuItemSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Get menu items filtered by tenant and category."""
        # Get fresh queryset with tenant context
        qs = MenuItem.objects.all()

        category_id = self.request.query_params.get("category_id")
        if category_id:
            qs = qs.filter(category_id=category_id)

        # Prefetch modifiers and options
        qs = qs.prefetch_related(
            Prefetch(
                "modifiers",
                queryset=Modifier.all_objects.prefetch_related("options"),
            )
        )
        return qs


class ModifierViewSet(TenantModelViewSet):
    """ViewSet for modifiers."""

    filterset_fields = ["menu_item"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ModifierWriteSerializer
        return ModifierSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Get modifiers filtered by tenant and menu item."""
        # Get fresh queryset with tenant context
        qs = Modifier.objects.all()

        menu_item_id = self.request.query_params.get("menu_item_id")
        if menu_item_id:
            qs = qs.filter(menu_item_id=menu_item_id)
        return qs.prefetch_related("options")


class ModifierOptionViewSet(TenantModelViewSet):
    """ViewSet for modifier options."""

    filterset_fields = ["modifier", "is_available"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ModifierOptionWriteSerializer
        return ModifierOptionSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Get modifier options filtered by tenant and modifier."""
        # Get fresh queryset with tenant context
        qs = ModifierOption.objects.all()

        modifier_id = self.request.query_params.get("modifier_id")
        if modifier_id:
            qs = qs.filter(modifier_id=modifier_id)
        return qs


class FullMenuView(APIView):
    """API endpoint for the complete nested menu structure."""

    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        """Set tenant context after authentication."""
        super().initial(request, *args, **kwargs)
        if request.user.is_authenticated:
            if hasattr(request.user, "restaurant") and request.user.restaurant:
                set_current_restaurant(request.user.restaurant)

    def finalize_response(self, request, response, *args, **kwargs):
        """Clear tenant context after response."""
        response = super().finalize_response(request, response, *args, **kwargs)
        set_current_restaurant(None)
        return response

    def get(self, request):
        """
        Return all categories with nested items and modifiers.
        Optimized with select_related and prefetch_related.
        """
        # Get user's role for filtering
        user = request.user
        is_manager = user.role in ("owner", "manager")

        # Build optimized queryset - use objects for tenant filtering
        categories_qs = Category.objects.all()

        # Non-managers only see visible categories
        if not is_manager:
            categories_qs = categories_qs.filter(is_visible=True)

        # Build items queryset based on user role
        if is_manager:
            items_qs = MenuItem.all_objects.all()
        else:
            items_qs = MenuItem.all_objects.filter(is_available=True)

        # Prefetch with optimized nested querysets
        categories_qs = categories_qs.prefetch_related(
            Prefetch(
                "items",
                queryset=items_qs.prefetch_related(
                    Prefetch(
                        "modifiers",
                        queryset=Modifier.all_objects.prefetch_related(
                            Prefetch(
                                "options",
                                queryset=ModifierOption.all_objects.filter(
                                    is_available=True
                                )
                                if not is_manager
                                else ModifierOption.all_objects.all(),
                            )
                        ),
                    )
                ),
            )
        ).order_by("display_order", "name")

        serializer = FullMenuSerializer({"categories": categories_qs})
        return Response(serializer.data, status=status.HTTP_200_OK)
