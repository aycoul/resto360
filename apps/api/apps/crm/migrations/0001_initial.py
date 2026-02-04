# Generated manually for CRM models

import uuid

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("authentication", "0001_initial"),
        ("menu", "0001_initial"),
        ("orders", "0001_initial"),
    ]

    operations = [
        # LoyaltyProgram
        migrations.CreateModel(
            name="LoyaltyProgram",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("points_per_currency", models.DecimalField(decimal_places=2, default=1, max_digits=5, help_text="Points earned per unit of currency spent")),
                ("currency_unit", models.PositiveIntegerField(default=1000, help_text="Currency amount that earns points_per_currency points")),
                ("signup_bonus", models.PositiveIntegerField(default=0)),
                ("referral_bonus_referrer", models.PositiveIntegerField(default=0)),
                ("referral_bonus_referee", models.PositiveIntegerField(default=0)),
                ("birthday_bonus", models.PositiveIntegerField(default=0)),
                ("review_bonus", models.PositiveIntegerField(default=0)),
                ("points_expire", models.BooleanField(default=False)),
                ("expiry_months", models.PositiveIntegerField(default=12)),
                ("min_points_redeem", models.PositiveIntegerField(default=100)),
                ("points_value_currency", models.DecimalField(decimal_places=2, default=10, max_digits=5, help_text="Currency value of each point")),
                ("terms_and_conditions", models.TextField(blank=True)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="%(class)ss", to="authentication.restaurant")),
            ],
            options={
                "verbose_name": "Loyalty Program",
                "verbose_name_plural": "Loyalty Programs",
            },
        ),
        # LoyaltyTier
        migrations.CreateModel(
            name="LoyaltyTier",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=50)),
                ("min_points", models.PositiveIntegerField(default=0)),
                ("min_lifetime_points", models.PositiveIntegerField(default=0, help_text="Minimum lifetime points to qualify")),
                ("points_multiplier", models.DecimalField(decimal_places=2, default=1.0, max_digits=3, help_text="Multiplier for points earned")),
                ("discount_percentage", models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)])),
                ("color", models.CharField(default="#6B7280", max_length=7)),
                ("icon", models.CharField(blank=True, max_length=50)),
                ("description", models.TextField(blank=True)),
                ("benefits", models.JSONField(blank=True, default=list)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="%(class)ss", to="authentication.restaurant")),
            ],
            options={
                "ordering": ["display_order", "min_points"],
            },
        ),
        # Customer
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("loyalty_points", models.PositiveIntegerField(default=0)),
                ("lifetime_points", models.PositiveIntegerField(default=0)),
                ("total_visits", models.PositiveIntegerField(default=0)),
                ("total_spent", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("average_order_value", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("last_visit_at", models.DateTimeField(blank=True, null=True)),
                ("birth_date", models.DateField(blank=True, null=True)),
                ("anniversary_date", models.DateField(blank=True, null=True)),
                ("preferred_language", models.CharField(default="en", max_length=5)),
                ("marketing_consent", models.BooleanField(default=False)),
                ("sms_consent", models.BooleanField(default=False)),
                ("referral_code", models.CharField(blank=True, max_length=10, unique=True)),
                ("notes", models.TextField(blank=True)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="%(class)ss", to="authentication.restaurant")),
                ("tier", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="customers", to="crm.loyaltytier")),
                ("referred_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="referrals", to="crm.customer")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["restaurant", "email"], name="crm_custome_restaur_ba35c1_idx"),
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["restaurant", "phone"], name="crm_custome_restaur_5f0e93_idx"),
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["restaurant", "loyalty_points"], name="crm_custome_restaur_3a82db_idx"),
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["referral_code"], name="crm_custome_referra_b42c91_idx"),
        ),
        # LoyaltyReward
        migrations.CreateModel(
            name="LoyaltyReward",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("points_required", models.PositiveIntegerField()),
                ("reward_type", models.CharField(choices=[("free_item", "Free Item"), ("discount_amount", "Discount Amount"), ("discount_percent", "Discount Percentage"), ("experience", "Special Experience")], default="free_item", max_length=20)),
                ("discount_value", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
                ("limited_quantity", models.BooleanField(default=False)),
                ("quantity_available", models.PositiveIntegerField(blank=True, null=True)),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to="rewards/")),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="%(class)ss", to="authentication.restaurant")),
                ("menu_item", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="loyalty_rewards", to="menu.menuitem")),
                ("min_tier", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="exclusive_rewards", to="crm.loyaltytier")),
            ],
            options={
                "ordering": ["points_required"],
            },
        ),
        # PointsTransaction
        migrations.CreateModel(
            name="PointsTransaction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("points", models.IntegerField()),
                ("balance_after", models.PositiveIntegerField()),
                ("transaction_type", models.CharField(choices=[("earn", "Earned"), ("redeem", "Redeemed")], max_length=10)),
                ("earn_type", models.CharField(blank=True, choices=[("purchase", "Purchase"), ("signup", "Sign Up Bonus"), ("referral", "Referral Bonus"), ("birthday", "Birthday Bonus"), ("review", "Review Bonus"), ("manual", "Manual Adjustment")], max_length=20)),
                ("redeem_type", models.CharField(blank=True, choices=[("reward", "Reward Redemption"), ("discount", "Discount"), ("expiry", "Points Expired"), ("manual", "Manual Adjustment")], max_length=20)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="%(class)ss", to="authentication.restaurant")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="points_transactions", to="crm.customer")),
                ("order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="points_transactions", to="orders.order")),
                ("reward", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="redemptions", to="crm.loyaltyreward")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="pointstransaction",
            index=models.Index(fields=["customer", "-created_at"], name="crm_pointst_custome_e15bb0_idx"),
        ),
        # RewardRedemption
        migrations.CreateModel(
            name="RewardRedemption",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("points_used", models.PositiveIntegerField()),
                ("code", models.CharField(max_length=20, unique=True)),
                ("is_used", models.BooleanField(default=False)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField()),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="%(class)ss", to="authentication.restaurant")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="redemptions", to="crm.customer")),
                ("reward", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="customer_redemptions", to="crm.loyaltyreward")),
                ("order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reward_redemptions", to="orders.order")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        # Campaign
        migrations.CreateModel(
            name="Campaign",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("scheduled", "Scheduled"), ("active", "Active"), ("paused", "Paused"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="draft", max_length=20)),
                ("channel", models.CharField(choices=[("email", "Email"), ("sms", "SMS"), ("both", "Email & SMS")], default="email", max_length=10)),
                ("subject", models.CharField(blank=True, max_length=200)),
                ("email_content", models.TextField(blank=True)),
                ("sms_content", models.CharField(blank=True, max_length=160)),
                ("scheduled_at", models.DateTimeField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("target_all_customers", models.BooleanField(default=False)),
                ("target_min_points", models.PositiveIntegerField(blank=True, null=True)),
                ("target_min_visits", models.PositiveIntegerField(blank=True, null=True)),
                ("target_inactive_days", models.PositiveIntegerField(blank=True, help_text="Target customers inactive for this many days", null=True)),
                ("target_tags", models.JSONField(blank=True, default=list)),
                ("recipients_count", models.PositiveIntegerField(default=0)),
                ("sent_count", models.PositiveIntegerField(default=0)),
                ("opened_count", models.PositiveIntegerField(default=0)),
                ("clicked_count", models.PositiveIntegerField(default=0)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="%(class)ss", to="authentication.restaurant")),
                ("target_tiers", models.ManyToManyField(blank=True, related_name="campaigns", to="crm.loyaltytier")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        # CampaignRecipient
        migrations.CreateModel(
            name="CampaignRecipient",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("opened_at", models.DateTimeField(blank=True, null=True)),
                ("clicked_at", models.DateTimeField(blank=True, null=True)),
                ("tracking_id", models.UUIDField(default=uuid.uuid4, unique=True)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="%(class)ss", to="authentication.restaurant")),
                ("campaign", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recipients", to="crm.campaign")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="campaign_receipts", to="crm.customer")),
            ],
            options={
                "unique_together": {("campaign", "customer")},
            },
        ),
    ]
