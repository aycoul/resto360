"""
CRM & Loyalty Models

This module provides customer relationship management and loyalty program functionality.
"""

import secrets
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel, TenantModel


class PointsEarnType(models.TextChoices):
    """Types of point earning events."""

    PURCHASE = "purchase", "Purchase"
    SIGNUP = "signup", "Sign Up Bonus"
    REFERRAL = "referral", "Referral Bonus"
    BIRTHDAY = "birthday", "Birthday Bonus"
    REVIEW = "review", "Review Bonus"
    MANUAL = "manual", "Manual Adjustment"


class PointsRedeemType(models.TextChoices):
    """Types of point redemption events."""

    REWARD = "reward", "Reward Redemption"
    DISCOUNT = "discount", "Discount"
    EXPIRY = "expiry", "Points Expired"
    MANUAL = "manual", "Manual Adjustment"


class CampaignStatus(models.TextChoices):
    """Campaign status choices."""

    DRAFT = "draft", "Draft"
    SCHEDULED = "scheduled", "Scheduled"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class CampaignChannel(models.TextChoices):
    """Campaign delivery channels."""

    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    BOTH = "both", "Email & SMS"


class Customer(TenantModel):
    """
    Customer profile for CRM and loyalty tracking.

    Stores customer contact information, loyalty points, and preferences.
    """

    # Contact Information
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Loyalty Program
    loyalty_points = models.PositiveIntegerField(default=0)
    lifetime_points = models.PositiveIntegerField(default=0)
    tier = models.ForeignKey(
        "LoyaltyTier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
    )

    # Statistics
    total_visits = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_visit_at = models.DateTimeField(null=True, blank=True)

    # Personal Info (for birthday rewards, etc.)
    birth_date = models.DateField(null=True, blank=True)
    anniversary_date = models.DateField(null=True, blank=True)

    # Preferences
    preferred_language = models.CharField(max_length=5, default="en")
    marketing_consent = models.BooleanField(default=False)
    sms_consent = models.BooleanField(default=False)

    # Referral
    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referred_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals",
    )

    # Notes
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["restaurant", "email"]),
            models.Index(fields=["restaurant", "phone"]),
            models.Index(fields=["restaurant", "loyalty_points"]),
            models.Index(fields=["referral_code"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)

    def _generate_referral_code(self):
        """Generate a unique 8-character referral code."""
        while True:
            code = secrets.token_urlsafe(6)[:8].upper()
            if not Customer.objects.filter(referral_code=code).exists():
                return code

    def add_points(self, points: int, earn_type: str, description: str = "") -> "PointsTransaction":
        """Add points to customer account and log the transaction."""
        self.loyalty_points += points
        self.lifetime_points += points
        self.save(update_fields=["loyalty_points", "lifetime_points", "updated_at"])

        return PointsTransaction.objects.create(
            restaurant=self.restaurant,
            customer=self,
            points=points,
            balance_after=self.loyalty_points,
            transaction_type="earn",
            earn_type=earn_type,
            description=description,
        )

    def redeem_points(self, points: int, redeem_type: str, description: str = "") -> "PointsTransaction":
        """Redeem points from customer account."""
        if points > self.loyalty_points:
            raise ValueError("Insufficient points")

        self.loyalty_points -= points
        self.save(update_fields=["loyalty_points", "updated_at"])

        return PointsTransaction.objects.create(
            restaurant=self.restaurant,
            customer=self,
            points=-points,
            balance_after=self.loyalty_points,
            transaction_type="redeem",
            redeem_type=redeem_type,
            description=description,
        )

    def record_visit(self, order_total: float):
        """Record a customer visit and update statistics."""
        from decimal import Decimal

        self.total_visits += 1
        self.total_spent += Decimal(str(order_total))
        self.average_order_value = self.total_spent / self.total_visits
        self.last_visit_at = timezone.now()
        self.save(update_fields=[
            "total_visits", "total_spent", "average_order_value",
            "last_visit_at", "updated_at"
        ])


class LoyaltyProgram(TenantModel):
    """
    Loyalty program settings for a restaurant.

    Defines how points are earned and general program rules.
    """

    is_active = models.BooleanField(default=True)

    # Point Earning Rules
    points_per_currency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1,
        help_text="Points earned per unit of currency spent",
    )
    currency_unit = models.PositiveIntegerField(
        default=1000,
        help_text="Currency amount that earns points_per_currency points (e.g., 1000 XOF)",
    )

    # Bonus Points
    signup_bonus = models.PositiveIntegerField(default=0)
    referral_bonus_referrer = models.PositiveIntegerField(default=0)
    referral_bonus_referee = models.PositiveIntegerField(default=0)
    birthday_bonus = models.PositiveIntegerField(default=0)
    review_bonus = models.PositiveIntegerField(default=0)

    # Expiry Settings
    points_expire = models.BooleanField(default=False)
    expiry_months = models.PositiveIntegerField(default=12)

    # Redemption Rules
    min_points_redeem = models.PositiveIntegerField(default=100)
    points_value_currency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        help_text="Currency value of each point when redeeming",
    )

    # Program Info
    terms_and_conditions = models.TextField(blank=True)

    class Meta:
        verbose_name = "Loyalty Program"
        verbose_name_plural = "Loyalty Programs"

    def __str__(self):
        return f"Loyalty Program - {self.restaurant.name}"

    def calculate_points(self, order_total: float) -> int:
        """Calculate points earned for an order total."""
        from decimal import Decimal

        total = Decimal(str(order_total))
        units = total / Decimal(str(self.currency_unit))
        points = int(units * self.points_per_currency)
        return max(0, points)


class LoyaltyTier(TenantModel):
    """
    Loyalty tier levels (e.g., Bronze, Silver, Gold).

    Tiers provide benefits and status based on points or spend.
    """

    name = models.CharField(max_length=50)
    min_points = models.PositiveIntegerField(default=0)
    min_lifetime_points = models.PositiveIntegerField(
        default=0,
        help_text="Minimum lifetime points to qualify",
    )

    # Benefits
    points_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
        help_text="Multiplier for points earned (e.g., 1.5 for 50% bonus)",
    )
    discount_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        help_text="Automatic discount percentage for this tier",
    )

    # Display
    color = models.CharField(max_length=7, default="#6B7280")
    icon = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    benefits = models.JSONField(default=list, blank=True)

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "min_points"]

    def __str__(self):
        return self.name


class LoyaltyReward(TenantModel):
    """
    Rewards that customers can redeem with their points.
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    points_required = models.PositiveIntegerField()

    # Reward Type
    reward_type = models.CharField(
        max_length=20,
        choices=[
            ("free_item", "Free Item"),
            ("discount_amount", "Discount Amount"),
            ("discount_percent", "Discount Percentage"),
            ("experience", "Special Experience"),
        ],
        default="free_item",
    )

    # Reward Value
    menu_item = models.ForeignKey(
        "menu.MenuItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loyalty_rewards",
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Availability
    is_active = models.BooleanField(default=True)
    limited_quantity = models.BooleanField(default=False)
    quantity_available = models.PositiveIntegerField(null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    # Restrictions
    min_tier = models.ForeignKey(
        LoyaltyTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exclusive_rewards",
    )

    # Image
    image = models.ImageField(upload_to="rewards/", null=True, blank=True)

    class Meta:
        ordering = ["points_required"]

    def __str__(self):
        return f"{self.name} ({self.points_required} pts)"

    @property
    def is_available(self) -> bool:
        """Check if reward is currently available."""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.limited_quantity and (self.quantity_available or 0) <= 0:
            return False
        return True


class PointsTransaction(TenantModel):
    """
    Record of points earned or redeemed by a customer.
    """

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="points_transactions",
    )
    points = models.IntegerField()  # Positive for earn, negative for redeem
    balance_after = models.PositiveIntegerField()

    transaction_type = models.CharField(
        max_length=10,
        choices=[("earn", "Earned"), ("redeem", "Redeemed")],
    )

    # For earned points
    earn_type = models.CharField(
        max_length=20,
        choices=PointsEarnType.choices,
        blank=True,
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="points_transactions",
    )

    # For redeemed points
    redeem_type = models.CharField(
        max_length=20,
        choices=PointsRedeemType.choices,
        blank=True,
    )
    reward = models.ForeignKey(
        LoyaltyReward,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="redemptions",
    )

    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
        ]

    def __str__(self):
        action = "earned" if self.points > 0 else "redeemed"
        return f"{self.customer.name} {action} {abs(self.points)} points"


class RewardRedemption(TenantModel):
    """
    Record of a reward redemption by a customer.
    """

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="redemptions",
    )
    reward = models.ForeignKey(
        LoyaltyReward,
        on_delete=models.CASCADE,
        related_name="customer_redemptions",
    )
    points_used = models.PositiveIntegerField()

    # Redemption Code
    code = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    # Applied to order
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reward_redemptions",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.name} - {self.reward.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)

    def _generate_code(self):
        """Generate a unique redemption code."""
        while True:
            code = f"RWD-{secrets.token_urlsafe(8)[:8].upper()}"
            if not RewardRedemption.objects.filter(code=code).exists():
                return code

    def mark_used(self, order=None):
        """Mark this redemption as used."""
        self.is_used = True
        self.used_at = timezone.now()
        self.order = order
        self.save(update_fields=["is_used", "used_at", "order", "updated_at"])


class Campaign(TenantModel):
    """
    Marketing campaign for customer outreach.
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT,
    )
    channel = models.CharField(
        max_length=10,
        choices=CampaignChannel.choices,
        default=CampaignChannel.EMAIL,
    )

    # Content
    subject = models.CharField(max_length=200, blank=True)  # For email
    email_content = models.TextField(blank=True)
    sms_content = models.CharField(max_length=160, blank=True)

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Targeting
    target_all_customers = models.BooleanField(default=False)
    target_tiers = models.ManyToManyField(LoyaltyTier, blank=True, related_name="campaigns")
    target_min_points = models.PositiveIntegerField(null=True, blank=True)
    target_min_visits = models.PositiveIntegerField(null=True, blank=True)
    target_inactive_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Target customers inactive for this many days",
    )
    target_tags = models.JSONField(default=list, blank=True)

    # Results
    recipients_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def open_rate(self) -> float:
        """Calculate email open rate."""
        if self.sent_count == 0:
            return 0.0
        return (self.opened_count / self.sent_count) * 100

    @property
    def click_rate(self) -> float:
        """Calculate click rate."""
        if self.sent_count == 0:
            return 0.0
        return (self.clicked_count / self.sent_count) * 100

    def get_target_customers(self):
        """Get queryset of customers matching targeting criteria."""
        qs = Customer.objects.filter(restaurant=self.restaurant)

        if self.channel in [CampaignChannel.EMAIL, CampaignChannel.BOTH]:
            qs = qs.exclude(email="")
            qs = qs.filter(marketing_consent=True)
        if self.channel in [CampaignChannel.SMS, CampaignChannel.BOTH]:
            qs = qs.exclude(phone="")
            qs = qs.filter(sms_consent=True)

        if not self.target_all_customers:
            if self.target_tiers.exists():
                qs = qs.filter(tier__in=self.target_tiers.all())
            if self.target_min_points:
                qs = qs.filter(loyalty_points__gte=self.target_min_points)
            if self.target_min_visits:
                qs = qs.filter(total_visits__gte=self.target_min_visits)
            if self.target_inactive_days:
                cutoff = timezone.now() - timezone.timedelta(days=self.target_inactive_days)
                qs = qs.filter(last_visit_at__lt=cutoff)
            if self.target_tags:
                qs = qs.filter(tags__contains=self.target_tags)

        return qs


class CampaignRecipient(TenantModel):
    """
    Individual recipient of a campaign.
    """

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="campaign_receipts",
    )

    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    # For tracking
    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True)

    class Meta:
        unique_together = ["campaign", "customer"]

    def __str__(self):
        return f"{self.campaign.name} -> {self.customer.name}"
