"""
Core view mixins and base classes for RESTO360 API.
"""

from rest_framework import viewsets

from .context import set_current_restaurant


class TenantContextMixin:
    """
    Mixin that sets the tenant context from the authenticated user.

    Use this mixin in DRF views to ensure tenant filtering works correctly.
    DRF authentication happens at the view level (after middleware),
    so we need to set the context here.
    """

    def initial(self, request, *args, **kwargs):
        """Called after authentication but before request handling."""
        super().initial(request, *args, **kwargs)
        # Set tenant context from authenticated user
        if request.user.is_authenticated:
            if hasattr(request.user, "restaurant") and request.user.restaurant:
                set_current_restaurant(request.user.restaurant)

    def finalize_response(self, request, response, *args, **kwargs):
        """Called after request handling to clean up context."""
        response = super().finalize_response(request, response, *args, **kwargs)
        set_current_restaurant(None)
        return response


class TenantModelViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """Base ModelViewSet with tenant context support."""

    pass
