"""
CRM & Loyalty Views
"""

from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Campaign,
    CampaignStatus,
    Customer,
    LoyaltyProgram,
    LoyaltyReward,
    LoyaltyTier,
    PointsTransaction,
    RewardRedemption,
)
from .serializers import (
    AddPointsSerializer,
    CampaignCreateSerializer,
    CampaignListSerializer,
    CampaignSerializer,
    CRMSummarySerializer,
    CustomerCreateSerializer,
    CustomerListSerializer,
    CustomerSearchSerializer,
    CustomerSerializer,
    CustomerUpdateSerializer,
    LoyaltyProgramSerializer,
    LoyaltyProgramUpdateSerializer,
    LoyaltyRewardCreateSerializer,
    LoyaltyRewardSerializer,
    LoyaltyTierCreateSerializer,
    LoyaltyTierSerializer,
    PointsTransactionSerializer,
    RedeemPointsSerializer,
    RedeemRewardSerializer,
    RewardRedemptionSerializer,
)


class CRMSummaryView(APIView):
    """Dashboard summary for CRM."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        now = timezone.now()
        month_ago = now - timedelta(days=30)

        # Get customer stats
        customers = Customer.objects.filter(business=business)
        total_customers = customers.count()
        active_customers = customers.filter(last_visit_at__gte=month_ago).count()
        new_customers = customers.filter(created_at__gte=month_ago).count()

        # Get points stats
        transactions = PointsTransaction.objects.filter(business=business)
        total_issued = transactions.filter(points__gt=0).aggregate(
            total=Sum("points")
        )["total"] or 0
        total_redeemed = abs(
            transactions.filter(points__lt=0).aggregate(total=Sum("points"))["total"] or 0
        )

        # Get rewards stats
        total_rewards = RewardRedemption.objects.filter(
            business=business, is_used=True
        ).count()

        # Average customer value
        avg_value = customers.aggregate(avg=Avg("total_spent"))["avg"] or 0

        # Customers by tier
        tiers = LoyaltyTier.objects.filter(business=business)
        customers_by_tier = [
            {
                "tier": tier.name,
                "color": tier.color,
                "count": customers.filter(tier=tier).count(),
            }
            for tier in tiers
        ]
        # Add customers without tier
        no_tier_count = customers.filter(tier__isnull=True).count()
        if no_tier_count > 0:
            customers_by_tier.append({
                "tier": "No Tier",
                "color": "#9CA3AF",
                "count": no_tier_count,
            })

        data = {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "new_customers_month": new_customers,
            "total_points_issued": total_issued,
            "total_points_redeemed": total_redeemed,
            "total_rewards_redeemed": total_rewards,
            "avg_customer_value": avg_value,
            "customers_by_tier": customers_by_tier,
        }

        serializer = CRMSummarySerializer(data)
        return Response(serializer.data)


class LoyaltyProgramView(APIView):
    """View and manage loyalty program settings."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        program, _ = LoyaltyProgram.objects.get_or_create(business=business)
        serializer = LoyaltyProgramSerializer(program)
        return Response(serializer.data)

    def patch(self, request):
        business = request.user.business
        program, _ = LoyaltyProgram.objects.get_or_create(business=business)
        serializer = LoyaltyProgramUpdateSerializer(program, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(LoyaltyProgramSerializer(program).data)


class LoyaltyTierViewSet(viewsets.ModelViewSet):
    """ViewSet for loyalty tiers."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LoyaltyTier.objects.filter(business=self.request.user.business)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LoyaltyTierCreateSerializer
        return LoyaltyTierSerializer

    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business)


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for customer management."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Customer.objects.filter(business=self.request.user.business)
        qs = qs.select_related("tier", "referred_by")

        # Search filters
        query = self.request.query_params.get("search")
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )

        tier_id = self.request.query_params.get("tier")
        if tier_id:
            qs = qs.filter(tier_id=tier_id)

        min_points = self.request.query_params.get("min_points")
        if min_points:
            qs = qs.filter(loyalty_points__gte=int(min_points))

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return CustomerListSerializer
        if self.action == "create":
            return CustomerCreateSerializer
        if self.action in ["update", "partial_update"]:
            return CustomerUpdateSerializer
        return CustomerSerializer

    def perform_create(self, serializer):
        business = self.request.user.business
        customer = serializer.save(business=business)

        # Award signup bonus if program is active
        try:
            program = LoyaltyProgram.objects.get(business=business, is_active=True)
            if program.signup_bonus > 0:
                customer.add_points(
                    program.signup_bonus,
                    "signup",
                    "Welcome bonus"
                )
        except LoyaltyProgram.DoesNotExist:
            pass

    @action(detail=True, methods=["post"])
    def add_points(self, request, pk=None):
        """Manually add points to a customer."""
        customer = self.get_object()
        serializer = AddPointsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction = customer.add_points(
            serializer.validated_data["points"],
            serializer.validated_data["earn_type"],
            serializer.validated_data.get("description", ""),
        )

        return Response(PointsTransactionSerializer(transaction).data)

    @action(detail=True, methods=["post"])
    def redeem_points(self, request, pk=None):
        """Manually redeem points from a customer."""
        customer = self.get_object()
        serializer = RedeemPointsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transaction = customer.redeem_points(
                serializer.validated_data["points"],
                serializer.validated_data["redeem_type"],
                serializer.validated_data.get("description", ""),
            )
            return Response(PointsTransactionSerializer(transaction).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        """Get points transaction history for a customer."""
        customer = self.get_object()
        transactions = PointsTransaction.objects.filter(customer=customer)[:50]
        serializer = PointsTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def redemptions(self, request, pk=None):
        """Get reward redemptions for a customer."""
        customer = self.get_object()
        redemptions = RewardRedemption.objects.filter(customer=customer)
        serializer = RewardRedemptionSerializer(redemptions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def redeem_reward(self, request, pk=None):
        """Redeem a reward for a customer."""
        customer = self.get_object()
        serializer = RedeemRewardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reward = LoyaltyReward.objects.get(
                id=serializer.validated_data["reward_id"],
                business=customer.business,
            )
        except LoyaltyReward.DoesNotExist:
            return Response(
                {"detail": "Reward not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not reward.is_available:
            return Response(
                {"detail": "Reward is not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if customer.loyalty_points < reward.points_required:
            return Response(
                {"detail": "Insufficient points"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check tier requirement
        if reward.min_tier and (not customer.tier or customer.tier.display_order < reward.min_tier.display_order):
            return Response(
                {"detail": f"This reward requires {reward.min_tier.name} tier"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Redeem points
        customer.redeem_points(
            reward.points_required,
            "reward",
            f"Redeemed: {reward.name}",
        )

        # Create redemption record
        redemption = RewardRedemption.objects.create(
            business=customer.business,
            customer=customer,
            reward=reward,
            points_used=reward.points_required,
        )

        # Update reward quantity if limited
        if reward.limited_quantity and reward.quantity_available:
            reward.quantity_available -= 1
            reward.save(update_fields=["quantity_available"])

        return Response(RewardRedemptionSerializer(redemption).data)


class LoyaltyRewardViewSet(viewsets.ModelViewSet):
    """ViewSet for loyalty rewards."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LoyaltyReward.objects.filter(business=self.request.user.business)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LoyaltyRewardCreateSerializer
        return LoyaltyRewardSerializer

    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business)


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for marketing campaigns."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Campaign.objects.filter(business=self.request.user.business)

    def get_serializer_class(self):
        if self.action == "list":
            return CampaignListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return CampaignCreateSerializer
        return CampaignSerializer

    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business)

    @action(detail=True, methods=["post"])
    def schedule(self, request, pk=None):
        """Schedule a campaign for sending."""
        campaign = self.get_object()
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
            return Response(
                {"detail": "Campaign cannot be scheduled in current status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scheduled_at = request.data.get("scheduled_at")
        if not scheduled_at:
            return Response(
                {"detail": "scheduled_at is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campaign.scheduled_at = scheduled_at
        campaign.status = CampaignStatus.SCHEDULED
        campaign.recipients_count = campaign.get_target_customers().count()
        campaign.save(update_fields=["scheduled_at", "status", "recipients_count", "updated_at"])

        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=["post"])
    def send_now(self, request, pk=None):
        """Send a campaign immediately."""
        campaign = self.get_object()
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            return Response(
                {"detail": "Campaign cannot be sent in current status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # In production, this would trigger a Celery task
        # For now, just update status
        campaign.status = CampaignStatus.ACTIVE
        campaign.recipients_count = campaign.get_target_customers().count()
        campaign.sent_at = timezone.now()
        campaign.save(update_fields=["status", "recipients_count", "sent_at", "updated_at"])

        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause an active campaign."""
        campaign = self.get_object()
        if campaign.status != CampaignStatus.ACTIVE:
            return Response(
                {"detail": "Only active campaigns can be paused"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campaign.status = CampaignStatus.PAUSED
        campaign.save(update_fields=["status", "updated_at"])
        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a campaign."""
        campaign = self.get_object()
        if campaign.status == CampaignStatus.COMPLETED:
            return Response(
                {"detail": "Completed campaigns cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campaign.status = CampaignStatus.CANCELLED
        campaign.save(update_fields=["status", "updated_at"])
        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=["get"])
    def preview_recipients(self, request, pk=None):
        """Preview target customers for a campaign."""
        campaign = self.get_object()
        customers = campaign.get_target_customers()[:20]
        serializer = CustomerListSerializer(customers, many=True)
        return Response({
            "total_count": campaign.get_target_customers().count(),
            "preview": serializer.data,
        })


class RewardRedemptionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing reward redemptions."""

    permission_classes = [IsAuthenticated]
    serializer_class = RewardRedemptionSerializer

    def get_queryset(self):
        qs = RewardRedemption.objects.filter(business=self.request.user.business)
        qs = qs.select_related("customer", "reward")

        unused = self.request.query_params.get("unused")
        if unused == "true":
            qs = qs.filter(is_used=False)

        return qs

    @action(detail=True, methods=["post"])
    def use(self, request, pk=None):
        """Mark a redemption as used."""
        redemption = self.get_object()
        if redemption.is_used:
            return Response(
                {"detail": "Redemption already used"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() > redemption.expires_at:
            return Response(
                {"detail": "Redemption has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        redemption.mark_used()
        return Response(self.get_serializer(redemption).data)


class ValidateRedemptionCodeView(APIView):
    """Validate a redemption code."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"detail": "code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            redemption = RewardRedemption.objects.get(
                code=code,
                business=request.user.business,
            )
        except RewardRedemption.DoesNotExist:
            return Response(
                {"detail": "Invalid code"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if redemption.is_used:
            return Response(
                {"detail": "Code already used", "valid": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() > redemption.expires_at:
            return Response(
                {"detail": "Code has expired", "valid": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "valid": True,
            "redemption": RewardRedemptionSerializer(redemption).data,
        })
