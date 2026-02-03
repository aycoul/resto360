from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Only restaurant owners can access."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "owner"


class IsOwnerOrManager(permissions.BasePermission):
    """Owners and managers can access."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ("owner", "manager")
        )


class IsCashier(permissions.BasePermission):
    """Cashiers and above can access (owner, manager, cashier)."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ("owner", "manager", "cashier")
        )


class IsSameRestaurant(permissions.BasePermission):
    """User can only access their own restaurant's data."""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "restaurant"):
            return obj.restaurant == request.user.restaurant
        return True
