from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsOwnerOrManager

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


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for menu categories."""

    queryset = Category.objects.all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CategoryWriteSerializer
        return CategorySerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter by visibility for non-manager users."""
        qs = super().get_queryset()

        # For list/retrieve actions, filter by visibility for non-managers
        if self.action in ("list", "retrieve"):
            user = self.request.user
            if user.role not in ("owner", "manager"):
                qs = qs.filter(is_visible=True)

        # Prefetch items for efficiency
        qs = qs.prefetch_related(
            Prefetch(
                "items",
                queryset=MenuItem.objects.filter(is_available=True).prefetch_related(
                    Prefetch(
                        "modifiers",
                        queryset=Modifier.objects.prefetch_related("options"),
                    )
                ),
            )
        )
        return qs


class MenuItemViewSet(viewsets.ModelViewSet):
    """ViewSet for menu items."""

    queryset = MenuItem.objects.all()
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
        """Allow filtering by category_id."""
        qs = super().get_queryset()
        category_id = self.request.query_params.get("category_id")
        if category_id:
            qs = qs.filter(category_id=category_id)

        # Prefetch modifiers and options
        qs = qs.prefetch_related(
            Prefetch(
                "modifiers",
                queryset=Modifier.objects.prefetch_related("options"),
            )
        )
        return qs


class ModifierViewSet(viewsets.ModelViewSet):
    """ViewSet for modifiers."""

    queryset = Modifier.objects.all()
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
        """Allow filtering by menu_item_id."""
        qs = super().get_queryset()
        menu_item_id = self.request.query_params.get("menu_item_id")
        if menu_item_id:
            qs = qs.filter(menu_item_id=menu_item_id)
        return qs.prefetch_related("options")


class ModifierOptionViewSet(viewsets.ModelViewSet):
    """ViewSet for modifier options."""

    queryset = ModifierOption.objects.all()
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
        """Allow filtering by modifier_id."""
        qs = super().get_queryset()
        modifier_id = self.request.query_params.get("modifier_id")
        if modifier_id:
            qs = qs.filter(modifier_id=modifier_id)
        return qs


class FullMenuView(APIView):
    """API endpoint for the complete nested menu structure."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return all categories with nested items and modifiers.
        Optimized with select_related and prefetch_related.
        """
        # Get user's role for filtering
        user = request.user
        is_manager = user.role in ("owner", "manager")

        # Build optimized queryset
        categories_qs = Category.objects.all()

        # Non-managers only see visible categories
        if not is_manager:
            categories_qs = categories_qs.filter(is_visible=True)

        # Build items queryset based on user role
        if is_manager:
            items_qs = MenuItem.objects.all()
        else:
            items_qs = MenuItem.objects.filter(is_available=True)

        # Prefetch with optimized nested querysets
        categories_qs = categories_qs.prefetch_related(
            Prefetch(
                "items",
                queryset=items_qs.prefetch_related(
                    Prefetch(
                        "modifiers",
                        queryset=Modifier.objects.prefetch_related(
                            Prefetch(
                                "options",
                                queryset=ModifierOption.objects.filter(
                                    is_available=True
                                )
                                if not is_manager
                                else ModifierOption.objects.all(),
                            )
                        ),
                    )
                ),
            )
        ).order_by("display_order", "name")

        serializer = FullMenuSerializer({"categories": categories_qs})
        return Response(serializer.data, status=status.HTTP_200_OK)
