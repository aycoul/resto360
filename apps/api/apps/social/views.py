"""
Social Media Automation Views
"""

from datetime import timedelta

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AICaption,
    ContentCalendar,
    PostMedia,
    PostPublish,
    PostStatus,
    PostTemplate,
    SocialAccount,
    SocialAnalytics,
    SocialPost,
)
from .serializers import (
    AICaptionSerializer,
    ContentCalendarCreateSerializer,
    ContentCalendarSerializer,
    GenerateCaptionSerializer,
    PostMediaSerializer,
    PostTemplateCreateSerializer,
    PostTemplateSerializer,
    SchedulePostSerializer,
    SocialAccountSerializer,
    SocialAnalyticsSerializer,
    SocialDashboardSerializer,
    SocialPostCreateSerializer,
    SocialPostListSerializer,
    SocialPostSerializer,
)


class SocialDashboardView(APIView):
    """Social media dashboard."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        posts = SocialPost.objects.filter(business=business)
        accounts = SocialAccount.objects.filter(business=business, is_active=True)

        # Stats
        total_posts = posts.count()
        scheduled_posts = posts.filter(status=PostStatus.SCHEDULED).count()
        published_this_month = posts.filter(
            status=PostStatus.PUBLISHED,
            published_at__gte=month_start,
        ).count()

        # Total engagement from publishes
        total_engagement = PostPublish.objects.filter(
            post__business=business,
            status=PostStatus.PUBLISHED,
        ).aggregate(
            total=Sum("likes") + Sum("comments") + Sum("shares")
        )["total"] or 0

        # Recent posts
        recent_posts = posts.order_by("-created_at")[:5]

        # Top performing (by engagement)
        top_post_ids = (
            PostPublish.objects.filter(
                post__business=business,
                status=PostStatus.PUBLISHED,
            )
            .values("post")
            .annotate(engagement=Sum("likes") + Sum("comments") + Sum("shares"))
            .order_by("-engagement")[:5]
            .values_list("post", flat=True)
        )
        top_performing = posts.filter(id__in=top_post_ids)

        data = {
            "total_posts": total_posts,
            "scheduled_posts": scheduled_posts,
            "published_this_month": published_this_month,
            "total_engagement": total_engagement,
            "accounts": accounts,
            "recent_posts": recent_posts,
            "top_performing": top_performing,
        }

        serializer = SocialDashboardSerializer(data, context={"request": request})
        return Response(serializer.data)


class SocialAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for social accounts."""

    permission_classes = [IsAuthenticated]
    serializer_class = SocialAccountSerializer

    def get_queryset(self):
        return SocialAccount.objects.filter(business=self.request.user.business)

    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business)

    @action(detail=True, methods=["post"])
    def disconnect(self, request, pk=None):
        """Disconnect a social account."""
        account = self.get_object()
        account.is_active = False
        account.access_token = ""
        account.refresh_token = ""
        account.save()
        return Response({"detail": "Account disconnected"})

    @action(detail=True, methods=["post"])
    def refresh_token(self, request, pk=None):
        """Refresh the OAuth token (placeholder)."""
        account = self.get_object()
        # In production, this would call the platform's API to refresh the token
        return Response({"detail": "Token refresh not implemented yet"})


class PostTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for post templates."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PostTemplate.objects.filter(business=self.request.user.business)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PostTemplateCreateSerializer
        return PostTemplateSerializer

    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business)


class SocialPostViewSet(viewsets.ModelViewSet):
    """ViewSet for social posts."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SocialPost.objects.filter(business=self.request.user.business)
        qs = qs.select_related("template", "menu_item")
        qs = qs.prefetch_related("media", "publishes__account")

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return SocialPostListSerializer
        if self.action == "create":
            return SocialPostCreateSerializer
        return SocialPostSerializer

    def perform_create(self, serializer):
        post = serializer.save(business=self.request.user.business)

        # Create publish records for specified accounts
        account_ids = serializer.validated_data.get("account_ids", [])
        for account_id in account_ids:
            try:
                account = SocialAccount.objects.get(
                    id=account_id,
                    business=self.request.user.business,
                    is_active=True,
                )
                PostPublish.objects.create(
                    business=self.request.user.business,
                    post=post,
                    account=account,
                )
            except SocialAccount.DoesNotExist:
                pass

    @action(detail=True, methods=["post"])
    def schedule(self, request, pk=None):
        """Schedule a post for publishing."""
        post = self.get_object()
        serializer = SchedulePostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        scheduled_at = serializer.validated_data["scheduled_at"]
        account_ids = serializer.validated_data["account_ids"]

        # Update post
        post.scheduled_at = scheduled_at
        post.status = PostStatus.SCHEDULED
        post.save(update_fields=["scheduled_at", "status", "updated_at"])

        # Create/update publish records
        for account_id in account_ids:
            try:
                account = SocialAccount.objects.get(
                    id=account_id,
                    business=request.user.business,
                    is_active=True,
                )
                PostPublish.objects.update_or_create(
                    post=post,
                    account=account,
                    defaults={
                        "business": request.user.business,
                        "status": PostStatus.SCHEDULED,
                    },
                )
            except SocialAccount.DoesNotExist:
                pass

        return Response(SocialPostSerializer(post, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def publish_now(self, request, pk=None):
        """Publish a post immediately (placeholder)."""
        post = self.get_object()

        if post.publishes.count() == 0:
            return Response(
                {"detail": "No accounts selected for publishing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # In production, this would trigger a Celery task
        post.status = PostStatus.PUBLISHING
        post.save(update_fields=["status", "updated_at"])

        # Simulate publishing
        for publish in post.publishes.all():
            publish.status = PostStatus.PUBLISHED
            publish.published_at = timezone.now()
            publish.save()

        post.status = PostStatus.PUBLISHED
        post.published_at = timezone.now()
        post.save(update_fields=["status", "published_at", "updated_at"])

        return Response(SocialPostSerializer(post, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def add_media(self, request, pk=None):
        """Add media to a post."""
        post = self.get_object()

        if "file" not in request.FILES:
            return Response(
                {"detail": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        media = PostMedia.objects.create(
            business=request.user.business,
            post=post,
            file=request.FILES["file"],
            media_type=request.data.get("media_type", "image"),
            display_order=post.media.count(),
        )

        return Response(PostMediaSerializer(media, context={"request": request}).data)

    @action(detail=True, methods=["delete"], url_path="media/(?P<media_id>[^/.]+)")
    def remove_media(self, request, pk=None, media_id=None):
        """Remove media from a post."""
        post = self.get_object()
        media = get_object_or_404(PostMedia, id=media_id, post=post)
        media.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContentCalendarViewSet(viewsets.ModelViewSet):
    """ViewSet for content calendar."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ContentCalendar.objects.filter(business=self.request.user.business)
        qs = qs.select_related("post")

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        return qs

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ContentCalendarCreateSerializer
        return ContentCalendarSerializer

    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business)


class AICaptionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AI captions."""

    permission_classes = [IsAuthenticated]
    serializer_class = AICaptionSerializer

    def get_queryset(self):
        return AICaption.objects.filter(business=self.request.user.business)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate AI caption for a menu item."""
        serializer = GenerateCaptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        menu_item_id = serializer.validated_data["menu_item_id"]
        tone = serializer.validated_data["tone"]
        language = serializer.validated_data["language"]
        include_hashtags = serializer.validated_data["include_hashtags"]

        # Get menu item
        from apps.menu.models import MenuItem
        try:
            menu_item = MenuItem.objects.get(
                id=menu_item_id,
                category__business=request.user.business,
            )
        except MenuItem.DoesNotExist:
            return Response(
                {"detail": "Menu item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Generate caption using AI (simplified version)
        # In production, this would call OpenAI API
        caption = self._generate_caption(menu_item, tone, language)
        hashtags = self._generate_hashtags(menu_item, language) if include_hashtags else ""

        ai_caption = AICaption.objects.create(
            business=request.user.business,
            menu_item=menu_item,
            caption=caption,
            hashtags=hashtags,
            tone=tone,
            language=language,
        )

        return Response(AICaptionSerializer(ai_caption).data)

    def _generate_caption(self, menu_item, tone, language):
        """Generate a caption (simplified)."""
        templates = {
            "professional": {
                "en": f"Introducing our exquisite {menu_item.name}. {menu_item.description or 'A culinary masterpiece crafted with care.'} Available now at our restaurant.",
                "fr": f"Découvrez notre exquis {menu_item.name}. {menu_item.description or 'Un chef-d\'œuvre culinaire préparé avec soin.'} Disponible maintenant.",
            },
            "casual": {
                "en": f"Have you tried our {menu_item.name} yet? 😋 {menu_item.description or 'Trust us, it\'s amazing!'} Come grab yours!",
                "fr": f"Avez-vous essayé notre {menu_item.name} ? 😋 {menu_item.description or 'Faites-nous confiance, c\'est délicieux !'} Venez goûter !",
            },
            "playful": {
                "en": f"Warning: Our {menu_item.name} may cause extreme happiness! 🎉 {menu_item.description or 'Don\'t say we didn\'t warn you!'}",
                "fr": f"Attention : Notre {menu_item.name} peut causer un bonheur extrême ! 🎉 {menu_item.description or 'On vous aura prévenu !'}",
            },
            "elegant": {
                "en": f"Experience the refined taste of our {menu_item.name}. {menu_item.description or 'An elegant creation for the discerning palate.'}",
                "fr": f"Découvrez le goût raffiné de notre {menu_item.name}. {menu_item.description or 'Une création élégante pour les palais exigeants.'}",
            },
            "promotional": {
                "en": f"🔥 Don't miss out! Our {menu_item.name} is waiting for you! {menu_item.description or 'Order now!'} Only {menu_item.price} XOF!",
                "fr": f"🔥 Ne ratez pas ! Notre {menu_item.name} vous attend ! {menu_item.description or 'Commandez maintenant !'} Seulement {menu_item.price} XOF !",
            },
        }
        return templates.get(tone, templates["casual"]).get(language, templates[tone]["en"])

    def _generate_hashtags(self, menu_item, language):
        """Generate hashtags (simplified)."""
        base_hashtags = "#restaurant #foodie #delicious #food"
        if language == "fr":
            base_hashtags = "#restaurant #gastronomie #delicieux #cuisine"
        return base_hashtags


class SocialAnalyticsView(APIView):
    """View social analytics."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        days = int(request.query_params.get("days", 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        analytics = SocialAnalytics.objects.filter(
            account__business=business,
            date__gte=start_date,
            date__lte=end_date,
        ).select_related("account")

        serializer = SocialAnalyticsSerializer(analytics, many=True)
        return Response(serializer.data)


class ConnectAccountView(APIView):
    """Connect a new social account (placeholder)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        platform = request.data.get("platform")
        if platform not in ["instagram", "facebook", "tiktok", "twitter"]:
            return Response(
                {"detail": "Invalid platform"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # In production, this would redirect to OAuth flow
        # For now, create a placeholder account
        account = SocialAccount.objects.create(
            business=request.user.business,
            platform=platform,
            account_name=f"Demo {platform.title()} Account",
            account_id=f"demo_{platform}_{request.user.business.id}",
        )

        return Response(SocialAccountSerializer(account).data)
