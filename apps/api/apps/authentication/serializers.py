import uuid

from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Business, User


class BusinessSerializer(serializers.ModelSerializer):
    """Serializer for Business model (formerly Restaurant)."""

    # Computed properties
    is_food_business = serializers.BooleanField(read_only=True)
    is_dgi_enabled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "slug",
            "phone",
            "email",
            "address",
            "timezone",
            "currency",
            "is_active",
            "business_type",
            "plan_type",
            "logo",
            "primary_color",
            "show_branding",
            # Tax fields
            "tax_id",
            "tax_regime",
            "default_tax_rate",
            "dgi_is_production",
            # Food-specific features
            "has_kitchen_display",
            "has_table_service",
            "has_delivery",
            # Computed
            "is_food_business",
            "is_dgi_enabled",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "is_food_business", "is_dgi_enabled"]
        extra_kwargs = {
            # Don't expose API keys in responses
            "dgi_api_key": {"write_only": True},
            "dgi_api_secret": {"write_only": True},
        }


# Backwards compatibility alias
RestaurantSerializer = BusinessSerializer


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with nested business."""

    business = BusinessSerializer(read_only=True)
    # Backwards compatibility
    restaurant = BusinessSerializer(source="business", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "name",
            "role",
            "business",
            "restaurant",  # Backwards compatibility
            "language",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["phone", "email", "name", "password", "role", "language"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class OwnerRegistrationSerializer(serializers.Serializer):
    """Register new business owner with business."""

    # User fields
    phone = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

    # Business fields
    business_name = serializers.CharField(max_length=200)
    business_slug = serializers.SlugField()
    business_phone = serializers.CharField(max_length=20, required=False)
    business_address = serializers.CharField(required=False, allow_blank=True)
    business_type = serializers.ChoiceField(
        choices=Business.BUSINESS_TYPE_CHOICES,
        default="restaurant",
    )

    # Backwards compatibility aliases
    restaurant_name = serializers.CharField(max_length=200, required=False, write_only=True)
    restaurant_slug = serializers.SlugField(required=False, write_only=True)
    restaurant_phone = serializers.CharField(max_length=20, required=False, write_only=True)
    restaurant_address = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value

    def validate(self, attrs):
        # Handle backwards compatibility: use restaurant_* if business_* not provided
        if "business_name" not in attrs and "restaurant_name" in attrs:
            attrs["business_name"] = attrs.pop("restaurant_name")
        if "business_slug" not in attrs and "restaurant_slug" in attrs:
            attrs["business_slug"] = attrs.pop("restaurant_slug")
        if "business_phone" not in attrs and "restaurant_phone" in attrs:
            attrs["business_phone"] = attrs.pop("restaurant_phone")
        if "business_address" not in attrs and "restaurant_address" in attrs:
            attrs["business_address"] = attrs.pop("restaurant_address")

        # Require business_name and business_slug
        if "business_name" not in attrs:
            raise serializers.ValidationError({"business_name": "This field is required."})
        if "business_slug" not in attrs:
            raise serializers.ValidationError({"business_slug": "This field is required."})

        # Check slug uniqueness
        if Business.objects.filter(slug=attrs["business_slug"]).exists():
            raise serializers.ValidationError(
                {"business_slug": "A business with this slug already exists."}
            )
        return attrs

    def create(self, validated_data):
        # Remove backwards compatibility fields
        validated_data.pop("restaurant_name", None)
        validated_data.pop("restaurant_slug", None)
        validated_data.pop("restaurant_phone", None)
        validated_data.pop("restaurant_address", None)

        # Create business
        business = Business.objects.create(
            name=validated_data["business_name"],
            slug=validated_data["business_slug"],
            phone=validated_data.get("business_phone", validated_data["phone"]),
            address=validated_data.get("business_address", ""),
            business_type=validated_data.get("business_type", "restaurant"),
        )

        # Create owner user
        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=validated_data["password"],
            name=validated_data["name"],
            email=validated_data.get("email", ""),
            business=business,
            role="owner",
        )
        return user


class PublicRegistrationSerializer(serializers.Serializer):
    """Public registration for self-service signup (BIZ360 Lite)."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    business_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=20)
    business_type = serializers.ChoiceField(
        choices=Business.BUSINESS_TYPE_CHOICES,
        default="restaurant",
        required=False,
    )

    # Backwards compatibility alias
    restaurant_name = serializers.CharField(max_length=200, required=False, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        # Handle backwards compatibility
        if "business_name" not in attrs and "restaurant_name" in attrs:
            attrs["business_name"] = attrs.pop("restaurant_name")
        if "business_name" not in attrs:
            raise serializers.ValidationError({"business_name": "This field is required."})
        return attrs

    def _generate_unique_slug(self, name):
        """Generate unique slug from business name with UUID suffix."""
        base_slug = slugify(name)
        if not base_slug:
            base_slug = "business"
        # Always add UUID suffix for uniqueness
        unique_suffix = uuid.uuid4().hex[:8]
        return f"{base_slug}-{unique_suffix}"

    @transaction.atomic
    def create(self, validated_data):
        # Remove password_confirm as it's not needed for creation
        validated_data.pop("password_confirm")
        validated_data.pop("restaurant_name", None)

        # Generate unique slug
        slug = self._generate_unique_slug(validated_data["business_name"])

        # Create business with free plan
        business = Business.objects.create(
            name=validated_data["business_name"],
            slug=slug,
            phone=validated_data["phone"],
            email=validated_data["email"],
            plan_type="free",
            business_type=validated_data.get("business_type", "restaurant"),
        )

        # Create owner user
        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=validated_data["password"],
            name=f"{validated_data['business_name']} Owner",
            email=validated_data["email"],
            business=business,
            role="owner",
        )

        return {"user": user, "business": business, "restaurant": business}


class StaffInviteSerializer(serializers.Serializer):
    """Invite staff member to business."""

    phone = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=["manager", "cashier", "kitchen", "driver"])

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=validated_data["password"],
            name=validated_data["name"],
            email=validated_data.get("email", ""),
            business=request.user.business,
            role=validated_data["role"],
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add custom claims to JWT token."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["name"] = user.name
        token["role"] = user.role
        if user.business:
            token["business_id"] = str(user.business.id)
            token["business_name"] = user.business.name
            token["business_type"] = user.business.business_type
            # Backwards compatibility
            token["restaurant_id"] = str(user.business.id)
            token["restaurant_name"] = user.business.name
        token["permissions"] = user.get_permissions_list()

        return token
