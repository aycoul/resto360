from django.utils.deprecation import MiddlewareMixin

from .context import set_current_business


class TenantMiddleware(MiddlewareMixin):
    """Extract business from authenticated user and set tenant context.

    Note: This middleware runs before DRF authentication, so for DRF views
    the context is set via TenantContextMixin in the view layer.
    This middleware handles Django admin and other non-DRF views.
    """

    def process_request(self, request):
        # For Django views (admin, etc.) where authentication happens via middleware
        if hasattr(request, "user") and request.user.is_authenticated:
            if hasattr(request.user, "business") and request.user.business:
                set_current_business(request.user.business)
        return None

    def process_response(self, request, response):
        set_current_business(None)  # Clear context after request
        return response
