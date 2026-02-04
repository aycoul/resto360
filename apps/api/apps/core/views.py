"""
Core view mixins and base classes for BIZ360 API.
"""

from rest_framework import viewsets

from .context import set_current_business

# Backwards compatibility alias
set_current_restaurant = set_current_business


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
            if hasattr(request.user, "business") and request.user.business:
                set_current_business(request.user.business)

    def finalize_response(self, request, response, *args, **kwargs):
        """Called after request handling to clean up context."""
        response = super().finalize_response(request, response, *args, **kwargs)
        set_current_business(None)
        return response


class TenantModelViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """Base ModelViewSet with tenant context support."""

    pass
