from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CurrentUserView,
    CustomTokenObtainPairView,
    InviteStaffView,
    LogoutView,
    PublicRegistrationView,
    RegisterOwnerView,
    RestaurantSettingsView,
    StaffListView,
)

app_name = "authentication"

urlpatterns = [
    # Auth endpoints
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Registration
    path("register/", PublicRegistrationView.as_view(), name="public-register"),
    # Legacy registration (requires restaurant_slug)
    path("register/owner/", RegisterOwnerView.as_view(), name="register_owner"),
    # User management
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path("staff/", StaffListView.as_view(), name="staff_list"),
    path("staff/invite/", InviteStaffView.as_view(), name="invite_staff"),
    # Restaurant settings
    path("restaurant/", RestaurantSettingsView.as_view(), name="restaurant_settings"),
]
