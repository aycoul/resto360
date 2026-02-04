"""
Views for the Supplier Marketplace API.
"""

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Cart,
    CartItem,
    Supplier,
    SupplierCategory,
    SupplierFavorite,
    SupplierOrder,
    SupplierOrderItem,
    SupplierProduct,
    SupplierReview,
)
from .serializers import (
    AddFavoriteSerializer,
    AddToCartSerializer,
    CartSerializer,
    CreateOrderFromCartSerializer,
    CreateReviewSerializer,
    MarketplaceSearchSerializer,
    SupplierCategorySerializer,
    SupplierCreateUpdateSerializer,
    SupplierDetailSerializer,
    SupplierFavoriteSerializer,
    SupplierListSerializer,
    SupplierOrderDetailSerializer,
    SupplierOrderListSerializer,
    SupplierProductCreateUpdateSerializer,
    SupplierProductDetailSerializer,
    SupplierProductListSerializer,
    SupplierResponseSerializer,
    SupplierReviewSerializer,
    SupplierStatsSerializer,
    UpdateCartItemSerializer,
    UpdateOrderStatusSerializer,
)


class IsSupplierOwner(permissions.BasePermission):
    """Permission to check if user owns the supplier."""

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Supplier):
            return obj.owner == request.user
        if hasattr(obj, "supplier"):
            return obj.supplier.owner == request.user
        return False


class SupplierCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing supplier categories.
    """

    queryset = SupplierCategory.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = SupplierCategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    @action(detail=True, methods=["get"])
    def products(self, request, slug=None):
        """Get products in this category."""
        category = self.get_object()
        products = SupplierProduct.objects.filter(
            Q(category=category) | Q(category__parent=category),
            is_available=True,
            supplier__is_active=True,
            supplier__verification_status=Supplier.VerificationStatus.VERIFIED,
        )
        serializer = SupplierProductListSerializer(products, many=True)
        return Response(serializer.data)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for suppliers.

    - Anyone can browse verified suppliers
    - Supplier owners can manage their own supplier profile
    """

    queryset = Supplier.objects.filter(is_active=True)
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SupplierCreateUpdateSerializer
        if self.action == "retrieve":
            return SupplierDetailSerializer
        return SupplierListSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsSupplierOwner()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # For public listing, only show verified suppliers
        if self.action == "list":
            queryset = queryset.filter(
                verification_status=Supplier.VerificationStatus.VERIFIED
            )

            # Filter by city
            city = self.request.query_params.get("city")
            if city:
                queryset = queryset.filter(city__iexact=city)

            # Filter by supplier type
            supplier_type = self.request.query_params.get("type")
            if supplier_type:
                queryset = queryset.filter(supplier_type=supplier_type)

            # Filter by category
            category = self.request.query_params.get("category")
            if category:
                queryset = queryset.filter(
                    products__category__slug=category
                ).distinct()

            # Search
            q = self.request.query_params.get("q")
            if q:
                queryset = queryset.filter(
                    Q(name__icontains=q) | Q(description__icontains=q)
                )

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"])
    def products(self, request, slug=None):
        """Get all products from this supplier."""
        supplier = self.get_object()
        products = supplier.products.filter(is_available=True)

        # Filter by category
        category = request.query_params.get("category")
        if category:
            products = products.filter(category__slug=category)

        serializer = SupplierProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def reviews(self, request, slug=None):
        """Get reviews for this supplier."""
        supplier = self.get_object()
        reviews = supplier.reviews.filter(is_published=True)
        serializer = SupplierReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_suppliers(self, request):
        """Get suppliers owned by the current user."""
        suppliers = Supplier.objects.filter(owner=request.user)
        serializer = SupplierListSerializer(suppliers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stats(self, request, slug=None):
        """Get statistics for supplier (owner only)."""
        supplier = self.get_object()
        if supplier.owner != request.user:
            return Response(
                {"error": "Not authorized"},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        orders = supplier.orders.exclude(status=SupplierOrder.Status.CANCELLED)
        month_orders = orders.filter(created_at__gte=month_start)

        stats = {
            "total_orders": supplier.total_orders,
            "total_revenue": supplier.total_revenue,
            "pending_orders": orders.filter(
                status__in=[
                    SupplierOrder.Status.SUBMITTED,
                    SupplierOrder.Status.CONFIRMED,
                ]
            ).count(),
            "this_month_orders": month_orders.count(),
            "this_month_revenue": month_orders.aggregate(
                total=Sum("total")
            )["total"] or 0,
            "average_order_value": orders.aggregate(avg=Avg("total"))["avg"] or 0,
            "top_products": list(
                SupplierProduct.objects.filter(supplier=supplier)
                .order_by("-times_ordered")[:5]
                .values("name", "times_ordered")
            ),
            "top_customers": list(
                orders.values("restaurant__name")
                .annotate(order_count=Count("id"), total_spent=Sum("total"))
                .order_by("-total_spent")[:5]
            ),
        }

        serializer = SupplierStatsSerializer(stats)
        return Response(serializer.data)


class SupplierProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for supplier products.
    """

    queryset = SupplierProduct.objects.filter(
        is_available=True,
        supplier__is_active=True,
        supplier__verification_status=Supplier.VerificationStatus.VERIFIED,
    )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SupplierProductCreateUpdateSerializer
        if self.action == "retrieve":
            return SupplierProductDetailSerializer
        return SupplierProductListSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsSupplierOwner()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search
        q = self.request.query_params.get("q")
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        # Filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        # Filter by supplier
        supplier = self.request.query_params.get("supplier")
        if supplier:
            queryset = queryset.filter(supplier__slug=supplier)

        # Filter by price range
        min_price = self.request.query_params.get("min_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.query_params.get("max_price")
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Filter by stock status
        in_stock = self.request.query_params.get("in_stock")
        if in_stock == "true":
            queryset = queryset.exclude(stock_status="out_of_stock")

        # Sort
        sort_by = self.request.query_params.get("sort_by", "name")
        if sort_by == "price":
            queryset = queryset.order_by("price")
        elif sort_by == "-price":
            queryset = queryset.order_by("-price")
        elif sort_by == "popularity":
            queryset = queryset.order_by("-times_ordered")
        elif sort_by == "-name":
            queryset = queryset.order_by("-name")
        else:
            queryset = queryset.order_by("name")

        return queryset


class CartViewSet(viewsets.ViewSet):
    """
    ViewSet for managing shopping carts.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_restaurant(self, request):
        return getattr(request.user, "restaurant", None)

    def list(self, request):
        """List all carts for the current restaurant."""
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        carts = Cart.objects.filter(restaurant=restaurant)
        serializer = CartSerializer(carts, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get cart for a specific supplier."""
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        try:
            cart = Cart.objects.get(restaurant=restaurant, supplier_id=pk)
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response({"items": [], "total": 0, "item_count": 0})

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """Add item to cart."""
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = SupplierProduct.objects.get(id=serializer.validated_data["product_id"])
        quantity = serializer.validated_data["quantity"]

        # Get or create cart for this supplier
        cart, _ = Cart.objects.get_or_create(
            restaurant=restaurant,
            supplier=product.supplier,
        )

        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"])
    def update_item(self, request):
        """Update cart item quantity."""
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        item_id = request.data.get("item_id")
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__restaurant=restaurant,
            )

            if serializer.validated_data["quantity"] == 0:
                cart = cart_item.cart
                cart_item.delete()
            else:
                cart_item.quantity = serializer.validated_data["quantity"]
                cart_item.save()
                cart = cart_item.cart

            return Response(CartSerializer(cart).data)

        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)

    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        """Remove item from cart."""
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        item_id = request.data.get("item_id")

        try:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__restaurant=restaurant,
            )
            cart = cart_item.cart
            cart_item.delete()

            return Response(CartSerializer(cart).data)

        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)

    @action(detail=True, methods=["post"])
    def clear(self, request, pk=None):
        """Clear cart for a specific supplier."""
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        try:
            cart = Cart.objects.get(restaurant=restaurant, supplier_id=pk)
            cart.items.all().delete()
            return Response({"message": "Cart cleared"})
        except Cart.DoesNotExist:
            return Response({"message": "Cart already empty"})


class SupplierOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for supplier orders.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SupplierOrderDetailSerializer
        return SupplierOrderListSerializer

    def get_queryset(self):
        user = self.request.user
        restaurant = getattr(user, "restaurant", None)

        # Check if user is a supplier owner
        supplier_ids = Supplier.objects.filter(owner=user).values_list("id", flat=True)

        if restaurant and supplier_ids:
            # User has both restaurant and supplier - show both
            return SupplierOrder.objects.filter(
                Q(restaurant=restaurant) | Q(supplier_id__in=supplier_ids)
            )
        elif restaurant:
            # Restaurant user - show their orders
            return SupplierOrder.objects.filter(restaurant=restaurant)
        elif supplier_ids:
            # Supplier user - show orders to them
            return SupplierOrder.objects.filter(supplier_id__in=supplier_ids)

        return SupplierOrder.objects.none()

    @action(detail=False, methods=["post"])
    def create_from_cart(self, request):
        """Create an order from the current cart."""
        restaurant = getattr(request.user, "restaurant", None)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        serializer = CreateOrderFromCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cart = Cart.objects.get(
                restaurant=restaurant,
                supplier_id=serializer.validated_data["supplier_id"],
            )
        except Cart.DoesNotExist:
            return Response({"error": "Cart is empty"}, status=400)

        if cart.items.count() == 0:
            return Response({"error": "Cart is empty"}, status=400)

        # Create order
        order = SupplierOrder.objects.create(
            supplier=cart.supplier,
            restaurant=restaurant,
            placed_by=request.user,
            status=SupplierOrder.Status.SUBMITTED,
            submitted_at=timezone.now(),
            delivery_address=serializer.validated_data["delivery_address"],
            delivery_instructions=serializer.validated_data.get("delivery_instructions", ""),
            expected_delivery=serializer.validated_data.get("expected_delivery"),
            restaurant_notes=serializer.validated_data.get("notes", ""),
        )

        # Create order items from cart
        for cart_item in cart.items.all():
            SupplierOrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_sku=cart_item.product.sku,
                unit=cart_item.product.unit,
                unit_size=cart_item.product.unit_size,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
            )

        # Calculate totals
        order.calculate_totals()
        order.save()

        # Clear the cart
        cart.items.all().delete()

        return Response(
            SupplierOrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """Update order status (supplier only)."""
        order = self.get_object()

        # Check if user is the supplier
        if order.supplier.owner != request.user:
            return Response(
                {"error": "Only the supplier can update order status"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        notes = serializer.validated_data.get("notes", "")

        # Update status
        order.status = new_status

        # Update timestamps
        if new_status == SupplierOrder.Status.CONFIRMED:
            order.confirmed_at = timezone.now()
        elif new_status == SupplierOrder.Status.DELIVERED:
            order.delivered_at = timezone.now()

        if notes:
            order.supplier_notes = notes

        order.save()

        # Update supplier stats on delivery
        if new_status == SupplierOrder.Status.DELIVERED:
            supplier = order.supplier
            supplier.total_orders += 1
            supplier.total_revenue += order.total
            supplier.save()

            # Update product stats
            for item in order.items.all():
                item.product.times_ordered += item.quantity
                item.product.save()

        return Response(SupplierOrderDetailSerializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an order (restaurant only, if not yet shipped)."""
        order = self.get_object()
        restaurant = getattr(request.user, "restaurant", None)

        if order.restaurant != restaurant:
            return Response(
                {"error": "Only the ordering restaurant can cancel"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status in [
            SupplierOrder.Status.SHIPPED,
            SupplierOrder.Status.DELIVERED,
        ]:
            return Response(
                {"error": "Cannot cancel shipped or delivered orders"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = SupplierOrder.Status.CANCELLED
        order.save()

        return Response(SupplierOrderDetailSerializer(order).data)


class SupplierReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for supplier reviews.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SupplierReviewSerializer

    def get_queryset(self):
        return SupplierReview.objects.filter(is_published=True)

    def get_serializer_class(self):
        if self.action == "create":
            return CreateReviewSerializer
        return SupplierReviewSerializer

    def perform_create(self, serializer):
        restaurant = getattr(self.request.user, "restaurant", None)
        if not restaurant:
            raise serializers.ValidationError("No restaurant associated with this user")

        # Check if user has ordered from this supplier
        order = serializer.validated_data.get("order")
        is_verified = False
        if order and order.restaurant == restaurant:
            is_verified = True

        serializer.save(
            restaurant=restaurant,
            reviewed_by=self.request.user,
            is_verified=is_verified,
        )

        # Update supplier rating
        supplier = serializer.validated_data["supplier"]
        reviews = supplier.reviews.filter(is_published=True)
        supplier.review_count = reviews.count()
        supplier.average_rating = reviews.aggregate(avg=Avg("overall_rating"))["avg"] or 0
        supplier.save()

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        """Supplier responds to a review."""
        review = self.get_object()

        if review.supplier.owner != request.user:
            return Response(
                {"error": "Only the supplier can respond"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SupplierResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review.supplier_response = serializer.validated_data["response"]
        review.response_at = timezone.now()
        review.save()

        return Response(SupplierReviewSerializer(review).data)


class SupplierFavoriteViewSet(viewsets.ViewSet):
    """
    ViewSet for managing supplier favorites.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_restaurant(self, request):
        return getattr(request.user, "restaurant", None)

    def list(self, request):
        """List all favorite suppliers."""
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        favorites = SupplierFavorite.objects.filter(restaurant=restaurant)
        serializer = SupplierFavoriteSerializer(favorites, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Add a supplier to favorites."""
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        serializer = AddFavoriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        favorite, created = SupplierFavorite.objects.get_or_create(
            restaurant=restaurant,
            supplier_id=serializer.validated_data["supplier_id"],
            defaults={"notes": serializer.validated_data.get("notes", "")},
        )

        if not created and serializer.validated_data.get("notes"):
            favorite.notes = serializer.validated_data["notes"]
            favorite.save()

        return Response(
            SupplierFavoriteSerializer(favorite).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def destroy(self, request, pk=None):
        """Remove a supplier from favorites."""
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "No restaurant associated with this user"}, status=400)

        try:
            favorite = SupplierFavorite.objects.get(
                restaurant=restaurant,
                supplier_id=pk,
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SupplierFavorite.DoesNotExist:
            return Response({"error": "Not in favorites"}, status=404)


class MarketplaceSearchAPI(APIView):
    """
    Unified search across suppliers and products.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = MarketplaceSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        q = data.get("q", "")

        # Search suppliers
        suppliers = Supplier.objects.filter(
            is_active=True,
            verification_status=Supplier.VerificationStatus.VERIFIED,
        )
        if q:
            suppliers = suppliers.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        # Search products
        products = SupplierProduct.objects.filter(
            is_available=True,
            supplier__is_active=True,
            supplier__verification_status=Supplier.VerificationStatus.VERIFIED,
        )
        if q:
            products = products.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        # Apply filters
        if data.get("category"):
            products = products.filter(category__slug=data["category"])

        if data.get("supplier"):
            products = products.filter(supplier_id=data["supplier"])

        if data.get("city"):
            suppliers = suppliers.filter(city__iexact=data["city"])
            products = products.filter(supplier__city__iexact=data["city"])

        if data.get("min_price"):
            products = products.filter(price__gte=data["min_price"])

        if data.get("max_price"):
            products = products.filter(price__lte=data["max_price"])

        if data.get("in_stock"):
            products = products.exclude(stock_status="out_of_stock")

        # Sort
        sort_by = data.get("sort_by", "name")
        if sort_by == "price":
            products = products.order_by("price")
        elif sort_by == "-price":
            products = products.order_by("-price")
        elif sort_by == "popularity":
            products = products.order_by("-times_ordered")
        elif sort_by == "-name":
            products = products.order_by("-name")
        else:
            products = products.order_by("name")

        return Response({
            "suppliers": SupplierListSerializer(suppliers[:10], many=True).data,
            "products": SupplierProductListSerializer(products[:50], many=True).data,
            "supplier_count": suppliers.count(),
            "product_count": products.count(),
        })
