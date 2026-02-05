"""Views for reviews app."""

from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import Business

from .models import (
    FeedbackRequest,
    Review,
    ReviewPhoto,
    ReviewResponse,
    ReviewSettings,
    ReviewSource,
    ReviewStatus,
    ReviewSummary,
)
from .serializers import (
    CreateFeedbackRequestSerializer,
    CreateReviewResponseSerializer,
    CreateReviewSerializer,
    FeedbackRequestSerializer,
    ModerateReviewSerializer,
    PublicReviewSerializer,
    ReviewSerializer,
    ReviewSettingsSerializer,
    ReviewSummarySerializer,
    SubmitFeedbackSerializer,
)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reviews."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateReviewSerializer
        return ReviewSerializer

    def get_queryset(self):
        qs = Review.objects.filter(business=self.request.user.business)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter by rating
        rating = self.request.query_params.get("rating")
        if rating:
            qs = qs.filter(rating=rating)

        # Filter by featured
        featured = self.request.query_params.get("featured")
        if featured == "true":
            qs = qs.filter(is_featured=True)

        # Filter by has_response
        has_response = self.request.query_params.get("has_response")
        if has_response == "true":
            qs = qs.filter(response__isnull=False)
        elif has_response == "false":
            qs = qs.filter(response__isnull=True)

        return qs.select_related("response").prefetch_related("photos")

    def perform_create(self, serializer):
        """Create a review (staff-created)."""
        settings, _ = ReviewSettings.objects.get_or_create(
            business=self.request.user.business
        )

        # Determine status based on settings
        initial_status = ReviewStatus.PENDING
        if settings.auto_approve:
            rating = serializer.validated_data.get("rating", 0)
            if rating >= settings.min_rating_auto_approve:
                initial_status = ReviewStatus.APPROVED

        serializer.save(
            business=self.request.user.business,
            status=initial_status,
            source=ReviewSource.WEBSITE,
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve a review."""
        review = self.get_object()
        review.status = ReviewStatus.APPROVED
        review.moderated_at = timezone.now()
        review.save()

        # Update summary
        self._update_summary()

        return Response(ReviewSerializer(review).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject a review."""
        review = self.get_object()
        review.status = ReviewStatus.REJECTED
        review.moderated_at = timezone.now()
        review.moderation_notes = request.data.get("reason", "")
        review.save()

        return Response(ReviewSerializer(review).data)

    @action(detail=True, methods=["post"])
    def feature(self, request, pk=None):
        """Toggle featured status."""
        review = self.get_object()
        review.is_featured = not review.is_featured
        review.save()
        return Response(ReviewSerializer(review).data)

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        """Add owner response to review."""
        review = self.get_object()

        if hasattr(review, "response") and review.response:
            return Response(
                {"error": "Review already has a response"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateReviewResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ReviewResponse.objects.create(
            business=self.request.user.business,
            review=review,
            **serializer.validated_data,
        )

        # Refresh review
        review.refresh_from_db()
        return Response(ReviewSerializer(review).data)

    @action(detail=True, methods=["patch"])
    def update_response(self, request, pk=None):
        """Update owner response."""
        review = self.get_object()

        if not hasattr(review, "response") or not review.response:
            return Response(
                {"error": "Review has no response to update"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateReviewResponseSerializer(
            review.response, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        review.refresh_from_db()
        return Response(ReviewSerializer(review).data)

    @action(detail=True, methods=["delete"])
    def delete_response(self, request, pk=None):
        """Delete owner response."""
        review = self.get_object()

        if hasattr(review, "response") and review.response:
            review.response.delete()

        review.refresh_from_db()
        return Response(ReviewSerializer(review).data)

    def _update_summary(self):
        """Update review summary cache."""
        summary, _ = ReviewSummary.objects.get_or_create(
            business=self.request.user.business
        )
        summary.refresh()


class ReviewSettingsView(APIView):
    """View for managing review settings."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings, _ = ReviewSettings.objects.get_or_create(
            business=request.user.business
        )
        return Response(ReviewSettingsSerializer(settings).data)

    def patch(self, request):
        settings, _ = ReviewSettings.objects.get_or_create(
            business=request.user.business
        )
        serializer = ReviewSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ReviewSummaryView(APIView):
    """View for review summary statistics."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        summary, created = ReviewSummary.objects.get_or_create(
            business=request.user.business
        )

        # Refresh if new or stale (older than 1 hour)
        if created or (
            timezone.now() - summary.last_updated
        ).total_seconds() > 3600:
            summary.refresh()

        return Response(ReviewSummarySerializer(summary).data)


class FeedbackRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing feedback requests."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateFeedbackRequestSerializer
        return FeedbackRequestSerializer

    def get_queryset(self):
        return FeedbackRequest.objects.filter(
            business=self.request.user.business
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """Mark feedback request as sent."""
        feedback_request = self.get_object()
        feedback_request.sent_at = timezone.now()
        feedback_request.save()
        # TODO: Actually send email/SMS
        return Response(FeedbackRequestSerializer(feedback_request).data)


# Public endpoints


class PublicReviewsView(APIView):
    """Public endpoint for viewing restaurant reviews."""

    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            business = Business.objects.get(slug=slug)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get settings
        settings, _ = ReviewSettings.objects.get_or_create(business=business)

        if not settings.show_reviews_on_menu:
            return Response({"reviews": [], "summary": None})

        # Get approved reviews
        reviews = Review.objects.filter(
            business=business,
            status=ReviewStatus.APPROVED,
        ).select_related("response").prefetch_related("photos")

        # Check minimum reviews
        if reviews.count() < settings.min_reviews_to_show:
            return Response({"reviews": [], "summary": None})

        # Get summary
        summary = None
        if settings.show_average_rating:
            summary_obj, _ = ReviewSummary.objects.get_or_create(business=business)
            if (timezone.now() - summary_obj.last_updated).total_seconds() > 3600:
                summary_obj.refresh()
            summary = ReviewSummarySerializer(summary_obj).data

        # Featured reviews first, then by date
        reviews = reviews.order_by("-is_featured", "-created_at")[:20]

        return Response({
            "reviews": PublicReviewSerializer(reviews, many=True).data,
            "summary": summary,
        })


class PublicSubmitReviewView(APIView):
    """Public endpoint for submitting reviews."""

    permission_classes = [AllowAny]

    def post(self, request, slug):
        try:
            business = Business.objects.get(slug=slug)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CreateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get settings
        settings, _ = ReviewSettings.objects.get_or_create(business=business)

        # Determine status
        initial_status = ReviewStatus.PENDING
        if settings.auto_approve:
            rating = serializer.validated_data.get("rating", 0)
            if rating >= settings.min_rating_auto_approve:
                initial_status = ReviewStatus.APPROVED

        review = Review.objects.create(
            business=business,
            status=initial_status,
            source=ReviewSource.WEBSITE,
            **serializer.validated_data,
        )

        # Update summary if approved
        if initial_status == ReviewStatus.APPROVED:
            summary, _ = ReviewSummary.objects.get_or_create(business=business)
            summary.refresh()

        return Response({
            "id": str(review.id),
            "status": review.status,
            "message": "Thank you for your review!",
        }, status=status.HTTP_201_CREATED)


class SubmitFeedbackView(APIView):
    """Submit feedback via token (from email/SMS link)."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        """Get feedback request info."""
        try:
            feedback_request = FeedbackRequest.all_objects.get(token=token)
        except FeedbackRequest.DoesNotExist:
            return Response(
                {"error": "Invalid or expired feedback link"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if feedback_request.completed_at:
            return Response(
                {"error": "Feedback already submitted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark as opened
        if not feedback_request.opened_at:
            feedback_request.opened_at = timezone.now()
            feedback_request.save()

        return Response({
            "customer_name": feedback_request.customer_name,
            "restaurant_name": feedback_request.business.name,
        })

    def post(self, request, token):
        """Submit feedback."""
        try:
            feedback_request = FeedbackRequest.all_objects.get(token=token)
        except FeedbackRequest.DoesNotExist:
            return Response(
                {"error": "Invalid or expired feedback link"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if feedback_request.completed_at:
            return Response(
                {"error": "Feedback already submitted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get settings
        settings, _ = ReviewSettings.objects.get_or_create(
            business=feedback_request.business
        )

        # Determine status
        initial_status = ReviewStatus.PENDING
        if settings.auto_approve:
            rating = serializer.validated_data.get("rating", 0)
            if rating >= settings.min_rating_auto_approve:
                initial_status = ReviewStatus.APPROVED

        # Determine source based on channel
        source = (
            ReviewSource.EMAIL
            if feedback_request.channel == "email"
            else ReviewSource.SMS
        )

        # Create review
        review = Review.objects.create(
            business=feedback_request.business,
            status=initial_status,
            source=source,
            is_verified=True,  # Verified because it came from feedback request
            order_id=feedback_request.order_id,
            reservation_id=feedback_request.reservation_id,
            reviewer_name=serializer.validated_data.get(
                "reviewer_name", feedback_request.customer_name
            ),
            reviewer_email=feedback_request.customer_email,
            reviewer_phone=feedback_request.customer_phone,
            **{
                k: v
                for k, v in serializer.validated_data.items()
                if k != "reviewer_name"
            },
        )

        # Update feedback request
        feedback_request.completed_at = timezone.now()
        feedback_request.review = review
        feedback_request.save()

        # Update summary if approved
        if initial_status == ReviewStatus.APPROVED:
            summary, _ = ReviewSummary.objects.get_or_create(
                business=feedback_request.business
            )
            summary.refresh()

        return Response({
            "message": "Thank you for your feedback!",
            "review_id": str(review.id),
        }, status=status.HTTP_201_CREATED)
