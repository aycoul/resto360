from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.permissions import IsOwner, IsOwnerOrManager

from .models import User
from .serializers import (
    BusinessSerializer,
    CustomTokenObtainPairSerializer,
    OwnerRegistrationSerializer,
    PublicRegistrationSerializer,
    StaffInviteSerializer,
    UserSerializer,
)

# Backwards compatibility alias
RestaurantSerializer = BusinessSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """Login endpoint - returns JWT with custom claims."""

    serializer_class = CustomTokenObtainPairSerializer


class RegisterOwnerView(generics.CreateAPIView):
    """Register new business owner with their business."""

    permission_classes = [AllowAny]
    serializer_class = OwnerRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens for immediate login
        refresh = RefreshToken.for_user(user)
        CustomTokenObtainPairSerializer.get_token(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class PublicRegistrationView(APIView):
    """Public registration for self-service signup (BIZ360 Lite)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PublicRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        user = result["user"]
        business = result["business"]

        # Generate JWT tokens for immediate login
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                # Both keys for backwards compatibility
                "business": {
                    "id": str(business.id),
                    "slug": business.slug,
                    "name": business.name,
                    "business_type": business.business_type,
                },
                "restaurant": {  # Backwards compatibility
                    "id": str(business.id),
                    "slug": business.slug,
                    "name": business.name,
                },
                "user": {
                    "id": str(user.id),
                    "name": user.name,
                    "role": user.role,
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class InviteStaffView(generics.CreateAPIView):
    """Invite staff member (owner/manager only)."""

    permission_classes = [IsAuthenticated, IsOwnerOrManager]
    serializer_class = StaffInviteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class StaffListView(generics.ListAPIView):
    """List staff members in current business."""

    permission_classes = [IsAuthenticated, IsOwnerOrManager]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(business=self.request.user.business)


class CurrentUserView(APIView):
    """Get current authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class BusinessSettingsView(generics.RetrieveUpdateAPIView):
    """Get/update current business settings (owner only)."""

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = BusinessSerializer

    def get_object(self):
        return self.request.user.business


# Backwards compatibility alias
RestaurantSettingsView = BusinessSettingsView


class LogoutView(APIView):
    """Logout - blacklist refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(
                {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )
