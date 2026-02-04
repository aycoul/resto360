"""
CRM & Loyalty Serializers
"""

from rest_framework import serializers

from .models import (
    Campaign,
    CampaignRecipient,
    Customer,
    LoyaltyProgram,
    LoyaltyReward,
    LoyaltyTier,
    PointsTransaction,
    RewardRedemption,
)


class LoyaltyTierSerializer(serializers.ModelSerializer):
    """Serializer for loyalty tiers."""

    customers_count = serializers.SerializerMethodField()

    class Meta:
        model = LoyaltyTier
        fields = [
            "id",
            "name",
            "min_points",
            "min_lifetime_points",
            "points_multiplier",
            "discount_percentage",
            "color",
            "icon",
            "description",
            "benefits",
            "display_order",
            "customers_count",
        ]

    def get_customers_count(self, obj):
        return obj.customers.count()


class LoyaltyTierCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating loyalty tiers."""

    class Meta:
        model = LoyaltyTier
        fields = [
            "name",
            "min_points",
            "min_lifetime_points",
            "points_multiplier",
            "discount_percentage",
            "color",
            "icon",
            "description",
            "benefits",
            "display_order",
        ]


class LoyaltyProgramSerializer(serializers.ModelSerializer):
    """Serializer for loyalty program settings."""

    tiers = LoyaltyTierSerializer(source="restaurant.loyaltytiers", many=True, read_only=True)

    class Meta:
        model = LoyaltyProgram
        fields = [
            "id",
            "is_active",
            "points_per_currency",
            "currency_unit",
            "signup_bonus",
            "referral_bonus_referrer",
            "referral_bonus_referee",
            "birthday_bonus",
            "review_bonus",
            "points_expire",
            "expiry_months",
            "min_points_redeem",
            "points_value_currency",
            "terms_and_conditions",
            "tiers",
        ]


class LoyaltyProgramUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating loyalty program settings."""

    class Meta:
        model = LoyaltyProgram
        fields = [
            "is_active",
            "points_per_currency",
            "currency_unit",
            "signup_bonus",
            "referral_bonus_referrer",
            "referral_bonus_referee",
            "birthday_bonus",
            "review_bonus",
            "points_expire",
            "expiry_months",
            "min_points_redeem",
            "points_value_currency",
            "terms_and_conditions",
        ]


class CustomerListSerializer(serializers.ModelSerializer):
    """Serializer for customer list view."""

    tier_name = serializers.CharField(source="tier.name", read_only=True, allow_null=True)
    tier_color = serializers.CharField(source="tier.color", read_only=True, allow_null=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "loyalty_points",
            "lifetime_points",
            "tier_name",
            "tier_color",
            "total_visits",
            "total_spent",
            "last_visit_at",
            "created_at",
        ]


class CustomerSerializer(serializers.ModelSerializer):
    """Full customer serializer."""

    tier = LoyaltyTierSerializer(read_only=True)
    referral_count = serializers.SerializerMethodField()
    referred_by_name = serializers.CharField(source="referred_by.name", read_only=True, allow_null=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "loyalty_points",
            "lifetime_points",
            "tier",
            "total_visits",
            "total_spent",
            "average_order_value",
            "last_visit_at",
            "birth_date",
            "anniversary_date",
            "preferred_language",
            "marketing_consent",
            "sms_consent",
            "referral_code",
            "referred_by",
            "referred_by_name",
            "referral_count",
            "notes",
            "tags",
            "created_at",
            "updated_at",
        ]

    def get_referral_count(self, obj):
        return obj.referrals.count()


class CustomerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating customers."""

    class Meta:
        model = Customer
        fields = [
            "name",
            "email",
            "phone",
            "birth_date",
            "anniversary_date",
            "preferred_language",
            "marketing_consent",
            "sms_consent",
            "notes",
            "tags",
        ]


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating customers."""

    class Meta:
        model = Customer
        fields = [
            "name",
            "email",
            "phone",
            "birth_date",
            "anniversary_date",
            "preferred_language",
            "marketing_consent",
            "sms_consent",
            "notes",
            "tags",
            "tier",
        ]


class PointsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for points transactions."""

    customer_name = serializers.CharField(source="customer.name", read_only=True)
    earn_type_display = serializers.CharField(source="get_earn_type_display", read_only=True)
    redeem_type_display = serializers.CharField(source="get_redeem_type_display", read_only=True)

    class Meta:
        model = PointsTransaction
        fields = [
            "id",
            "customer",
            "customer_name",
            "points",
            "balance_after",
            "transaction_type",
            "earn_type",
            "earn_type_display",
            "redeem_type",
            "redeem_type_display",
            "order",
            "reward",
            "description",
            "created_at",
        ]


class AddPointsSerializer(serializers.Serializer):
    """Serializer for manually adding points."""

    points = serializers.IntegerField(min_value=1)
    earn_type = serializers.ChoiceField(choices=[
        ("manual", "Manual Adjustment"),
        ("birthday", "Birthday Bonus"),
        ("referral", "Referral Bonus"),
    ], default="manual")
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)


class RedeemPointsSerializer(serializers.Serializer):
    """Serializer for manually redeeming points."""

    points = serializers.IntegerField(min_value=1)
    redeem_type = serializers.ChoiceField(choices=[
        ("manual", "Manual Adjustment"),
        ("discount", "Discount"),
        ("expiry", "Points Expired"),
    ], default="manual")
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)


class LoyaltyRewardSerializer(serializers.ModelSerializer):
    """Serializer for loyalty rewards."""

    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True, allow_null=True)
    min_tier_name = serializers.CharField(source="min_tier.name", read_only=True, allow_null=True)
    is_available = serializers.BooleanField(read_only=True)
    redemption_count = serializers.SerializerMethodField()

    class Meta:
        model = LoyaltyReward
        fields = [
            "id",
            "name",
            "description",
            "points_required",
            "reward_type",
            "menu_item",
            "menu_item_name",
            "discount_value",
            "is_active",
            "limited_quantity",
            "quantity_available",
            "valid_from",
            "valid_until",
            "min_tier",
            "min_tier_name",
            "image",
            "is_available",
            "redemption_count",
            "created_at",
        ]

    def get_redemption_count(self, obj):
        return obj.customer_redemptions.filter(is_used=True).count()


class LoyaltyRewardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating rewards."""

    class Meta:
        model = LoyaltyReward
        fields = [
            "name",
            "description",
            "points_required",
            "reward_type",
            "menu_item",
            "discount_value",
            "is_active",
            "limited_quantity",
            "quantity_available",
            "valid_from",
            "valid_until",
            "min_tier",
            "image",
        ]


class RewardRedemptionSerializer(serializers.ModelSerializer):
    """Serializer for reward redemptions."""

    customer_name = serializers.CharField(source="customer.name", read_only=True)
    reward_name = serializers.CharField(source="reward.name", read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = RewardRedemption
        fields = [
            "id",
            "customer",
            "customer_name",
            "reward",
            "reward_name",
            "points_used",
            "code",
            "is_used",
            "used_at",
            "expires_at",
            "is_expired",
            "order",
            "created_at",
        ]

    def get_is_expired(self, obj):
        from django.utils import timezone
        return timezone.now() > obj.expires_at if not obj.is_used else False


class RedeemRewardSerializer(serializers.Serializer):
    """Serializer for redeeming a reward."""

    reward_id = serializers.UUIDField()


class CampaignListSerializer(serializers.ModelSerializer):
    """Serializer for campaign list."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "status",
            "status_display",
            "channel",
            "channel_display",
            "scheduled_at",
            "sent_at",
            "recipients_count",
            "sent_count",
            "opened_count",
            "clicked_count",
            "open_rate",
            "click_rate",
            "created_at",
        ]


class CampaignSerializer(serializers.ModelSerializer):
    """Full campaign serializer."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    target_customers_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "description",
            "status",
            "status_display",
            "channel",
            "channel_display",
            "subject",
            "email_content",
            "sms_content",
            "scheduled_at",
            "sent_at",
            "target_all_customers",
            "target_tiers",
            "target_min_points",
            "target_min_visits",
            "target_inactive_days",
            "target_tags",
            "recipients_count",
            "sent_count",
            "opened_count",
            "clicked_count",
            "open_rate",
            "click_rate",
            "target_customers_count",
            "created_at",
            "updated_at",
        ]

    def get_target_customers_count(self, obj):
        return obj.get_target_customers().count()


class CampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating campaigns."""

    class Meta:
        model = Campaign
        fields = [
            "name",
            "description",
            "channel",
            "subject",
            "email_content",
            "sms_content",
            "scheduled_at",
            "target_all_customers",
            "target_tiers",
            "target_min_points",
            "target_min_visits",
            "target_inactive_days",
            "target_tags",
        ]


class CRMSummarySerializer(serializers.Serializer):
    """Serializer for CRM dashboard summary."""

    total_customers = serializers.IntegerField()
    active_customers = serializers.IntegerField()
    new_customers_month = serializers.IntegerField()
    total_points_issued = serializers.IntegerField()
    total_points_redeemed = serializers.IntegerField()
    total_rewards_redeemed = serializers.IntegerField()
    avg_customer_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    customers_by_tier = serializers.ListField()


class CustomerSearchSerializer(serializers.Serializer):
    """Serializer for customer search."""

    query = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tier = serializers.UUIDField(required=False, allow_null=True)
    min_points = serializers.IntegerField(required=False, allow_null=True)
    max_points = serializers.IntegerField(required=False, allow_null=True)
    has_email = serializers.BooleanField(required=False, allow_null=True)
    marketing_consent = serializers.BooleanField(required=False, allow_null=True)
