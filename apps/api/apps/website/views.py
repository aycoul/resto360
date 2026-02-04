"""
Website Generator Views
"""

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Website,
    WebsiteBusinessHours,
    WebsiteContactForm,
    WebsiteGalleryImage,
    WebsiteStatus,
    WebsiteTemplate,
)
from .serializers import (
    PublicWebsiteSerializer,
    WebsiteBusinessHoursSerializer,
    WebsiteContactFormCreateSerializer,
    WebsiteContactFormSerializer,
    WebsiteGalleryImageSerializer,
    WebsiteSerializer,
    WebsiteUpdateSerializer,
)


class WebsiteView(APIView):
    """
    View and manage restaurant website.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get website configuration."""
        restaurant = request.user.restaurant
        website, _ = Website.objects.get_or_create(restaurant=restaurant)
        serializer = WebsiteSerializer(website, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        """Update website configuration."""
        restaurant = request.user.restaurant
        website, _ = Website.objects.get_or_create(restaurant=restaurant)
        serializer = WebsiteUpdateSerializer(website, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(WebsiteSerializer(website, context={"request": request}).data)


class WebsitePublishView(APIView):
    """Publish or unpublish website."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Publish website."""
        website, _ = Website.objects.get_or_create(restaurant=request.user.restaurant)
        website.publish()
        return Response(WebsiteSerializer(website, context={"request": request}).data)

    def delete(self, request):
        """Unpublish website."""
        website, _ = Website.objects.get_or_create(restaurant=request.user.restaurant)
        website.unpublish()
        return Response(WebsiteSerializer(website, context={"request": request}).data)


class WebsiteGalleryViewSet(viewsets.ModelViewSet):
    """ViewSet for gallery images."""

    permission_classes = [IsAuthenticated]
    serializer_class = WebsiteGalleryImageSerializer

    def get_queryset(self):
        website, _ = Website.objects.get_or_create(restaurant=self.request.user.restaurant)
        return WebsiteGalleryImage.objects.filter(website=website)

    def perform_create(self, serializer):
        website, _ = Website.objects.get_or_create(restaurant=self.request.user.restaurant)
        serializer.save(restaurant=self.request.user.restaurant, website=website)


class WebsiteBusinessHoursViewSet(viewsets.ModelViewSet):
    """ViewSet for business hours."""

    permission_classes = [IsAuthenticated]
    serializer_class = WebsiteBusinessHoursSerializer

    def get_queryset(self):
        website, _ = Website.objects.get_or_create(restaurant=self.request.user.restaurant)
        return WebsiteBusinessHours.objects.filter(website=website)

    def perform_create(self, serializer):
        website, _ = Website.objects.get_or_create(restaurant=self.request.user.restaurant)
        serializer.save(restaurant=self.request.user.restaurant, website=website)


class WebsiteContactFormViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for contact form submissions."""

    permission_classes = [IsAuthenticated]
    serializer_class = WebsiteContactFormSerializer

    def get_queryset(self):
        website, _ = Website.objects.get_or_create(restaurant=self.request.user.restaurant)
        return WebsiteContactForm.objects.filter(website=website)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark a submission as read."""
        submission = self.get_object()
        submission.mark_read()
        return Response(self.get_serializer(submission).data)


class TemplateChoicesView(APIView):
    """Get available website templates."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        templates = [
            {
                "value": t.value,
                "label": t.label,
                "description": self._get_description(t.value),
                "preview_url": f"/templates/{t.value}.png",
            }
            for t in WebsiteTemplate
        ]
        return Response({"templates": templates})

    def _get_description(self, template):
        descriptions = {
            "modern": "Clean, contemporary design with bold typography",
            "elegant": "Sophisticated design perfect for fine dining",
            "casual": "Friendly, approachable design for casual eateries",
            "minimal": "Simple, content-focused design",
            "vibrant": "Bold colors and dynamic layout for lively venues",
        }
        return descriptions.get(template, "")


# Public Views (No Authentication Required)

class PublicWebsiteView(APIView):
    """
    Public view for restaurant website.
    """

    permission_classes = [AllowAny]

    def get(self, request, subdomain):
        """Get public website data by subdomain."""
        website = get_object_or_404(
            Website,
            subdomain=subdomain,
            status=WebsiteStatus.PUBLISHED,
        )
        serializer = PublicWebsiteSerializer(website, context={"request": request})
        return Response(serializer.data)


class PublicContactFormView(APIView):
    """
    Public endpoint for contact form submissions.
    """

    permission_classes = [AllowAny]

    def post(self, request, subdomain):
        """Submit a contact form."""
        website = get_object_or_404(
            Website,
            subdomain=subdomain,
            status=WebsiteStatus.PUBLISHED,
        )

        serializer = WebsiteContactFormCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(restaurant=website.restaurant, website=website)

        return Response(
            {"detail": "Message sent successfully"},
            status=status.HTTP_201_CREATED,
        )


class CheckSubdomainView(APIView):
    """Check if a subdomain is available."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        subdomain = request.query_params.get("subdomain", "").lower()
        if not subdomain:
            return Response({"available": False, "reason": "Subdomain is required"})

        # Check if valid format
        import re
        if not re.match(r"^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$", subdomain):
            return Response({
                "available": False,
                "reason": "Invalid format. Use only lowercase letters, numbers, and hyphens",
            })

        # Check if taken
        website = Website.objects.filter(subdomain=subdomain).first()
        if website and website.restaurant != request.user.restaurant:
            return Response({"available": False, "reason": "Subdomain is taken"})

        return Response({"available": True})


class UpdateSubdomainView(APIView):
    """Update website subdomain."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        subdomain = request.data.get("subdomain", "").lower()
        if not subdomain:
            return Response(
                {"detail": "Subdomain is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if valid format
        import re
        if not re.match(r"^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$", subdomain):
            return Response(
                {"detail": "Invalid format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if taken
        existing = Website.objects.filter(subdomain=subdomain).exclude(
            restaurant=request.user.restaurant
        ).first()
        if existing:
            return Response(
                {"detail": "Subdomain is taken"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        website, _ = Website.objects.get_or_create(restaurant=request.user.restaurant)
        website.subdomain = subdomain
        website.save(update_fields=["subdomain", "updated_at"])

        return Response(WebsiteSerializer(website, context={"request": request}).data)
