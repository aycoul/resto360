from django.utils.deprecation import MiddlewareMixin

from .context import set_current_restaurant


class TenantMiddleware(MiddlewareMixin):
    """Extract restaurant from authenticated user and set tenant context."""

    def process_request(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            if hasattr(request.user, "restaurant") and request.user.restaurant:
                set_current_restaurant(request.user.restaurant)
        return None

    def process_response(self, request, response):
        set_current_restaurant(None)  # Clear context after request
        return response
