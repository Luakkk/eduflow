from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Responsibilities:
    - validate email format and uniqueness
    - validate password using Django's password validators
    - create a new User instance with a hashed password
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "role")

    # ---- field-level validators ----

    def validate_email(self, value: str) -> str:
        """
        Validate email format and check that it is unique.
        """
        validate_email(value)  # basic format check

        normalized = value.lower().strip()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("This email is already registered.")

        return normalized

    def validate_username(self, value: str) -> str:
        """
        Basic username validation. You can extend this if needed.
        """
        v = value.strip()
        if len(v) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        return v

    def validate_password(self, value: str) -> str:
        """
        Validate password using Django's built-in validators.

        Any validation errors will be converted by DRF into a normal
        JSON error, and then wrapped into RFC7807 format by the
        custom exception handler.
        """
        validate_password(value)
        return value

    # ---- object creation ----

    def create(self, validated_data: dict) -> User:
        """
        Create a new User instance, hash the password,
        and save the user to the database.
        """
        raw_password = validated_data.pop("password")

        # Create the user instance without saving yet
        user = User(**validated_data)

        # Run password validation again with user context (optional but nice)
        validate_password(raw_password, user)

        # Hash and set password
        user.set_password(raw_password)
        user.save()

        return user

class ProfileSerializer(serializers.ModelSerializer):
    """
    Read-only user profile serializer.

    Used for:
    - returning profile data after login
    - the /auth/me/ endpoint
    """
    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "date_joined")
        read_only_fields = fields