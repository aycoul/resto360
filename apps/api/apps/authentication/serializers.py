import uuid

from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Restaurant, User


class RestaurantSerializer(serializers.ModelSerializer):
    """Serializer for Restaurant model."""

    class Meta:
        model = Restaurant
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
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with nested restaurant."""

    restaurant = RestaurantSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "name",
            "role",
            "restaurant",
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
    """Register new restaurant owner with restaurant."""

    # User fields
    phone = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

    # Restaurant fields
    restaurant_name = serializers.CharField(max_length=200)
    restaurant_slug = serializers.SlugField()
    restaurant_phone = serializers.CharField(max_length=20, required=False)
    restaurant_address = serializers.CharField(required=False, allow_blank=True)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value

    def validate_restaurant_slug(self, value):
        if Restaurant.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                "A restaurant with this slug already exists."
            )
        return value

    def create(self, validated_data):
        # Create restaurant
        restaurant = Restaurant.objects.create(
            name=validated_data["restaurant_name"],
            slug=validated_data["restaurant_slug"],
            phone=validated_data.get("restaurant_phone", validated_data["phone"]),
            address=validated_data.get("restaurant_address", ""),
        )

        # Create owner user
        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=validated_data["password"],
            name=validated_data["name"],
            email=validated_data.get("email", ""),
            restaurant=restaurant,
            role="owner",
        )
        return user


class PublicRegistrationSerializer(serializers.Serializer):
    """Public registration for self-service signup (RESTO360 Lite)."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    restaurant_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=20)

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
        return attrs

    def _generate_unique_slug(self, name):
        """Generate unique slug from restaurant name with UUID suffix."""
        base_slug = slugify(name)
        if not base_slug:
            base_slug = "restaurant"
        # Always add UUID suffix for uniqueness
        unique_suffix = uuid.uuid4().hex[:8]
        return f"{base_slug}-{unique_suffix}"

    @transaction.atomic
    def create(self, validated_data):
        # Remove password_confirm as it's not needed for creation
        validated_data.pop("password_confirm")

        # Generate unique slug
        slug = self._generate_unique_slug(validated_data["restaurant_name"])

        # Create restaurant with free plan
        restaurant = Restaurant.objects.create(
            name=validated_data["restaurant_name"],
            slug=slug,
            phone=validated_data["phone"],
            email=validated_data["email"],
            plan_type="free",
        )

        # Create owner user
        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=validated_data["password"],
            name=f"{validated_data['restaurant_name']} Owner",
            email=validated_data["email"],
            restaurant=restaurant,
            role="owner",
        )

        return {"user": user, "restaurant": restaurant}


class StaffInviteSerializer(serializers.Serializer):
    """Invite staff member to restaurant."""

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
            restaurant=request.user.restaurant,
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
        if user.restaurant:
            token["restaurant_id"] = str(user.restaurant.id)
            token["restaurant_name"] = user.restaurant.name
        token["permissions"] = user.get_permissions_list()

        return token
