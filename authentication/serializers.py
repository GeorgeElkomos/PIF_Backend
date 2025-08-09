import re
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Company
User = get_user_model()

class UserLoginSerializer(serializers.Serializer):
    """
    User login serializer with brute force protection considerations.
    """
    username_or_email = serializers.CharField(
        max_length=150,
        help_text="Username or email address"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate user credentials."""
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')

        if not username_or_email or not password:
            raise ValidationError("Both username/email and password are required.")

        # Try to find user by username or email
        user = None
        if '@' in username_or_email:
            # It's an email
            try:
                user = User.objects.get(email=username_or_email.lower())
            except User.DoesNotExist:
                pass
        else:
            # It's a username
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                pass

        if user and user.check_password(password):
            if not user.is_active:
                raise ValidationError("User account is disabled.")
            attrs['user'] = user
            return attrs
        
        # Generic error message to prevent username enumeration
        raise ValidationError("Invalid credentials.")

class CompanyRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a company along with its admin user.
    """

    # Company fields
    name = serializers.CharField(max_length=100)
    arabic_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    cr_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    moi_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    country_of_incorporation = serializers.CharField(max_length=100, required=False, allow_blank=True)

    # Admin user fields
    username = serializers.CharField(
        min_length=3,
        max_length=30,
        help_text="Username must be 3-30 characters, alphanumeric and underscores only"
    )
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=12,
        help_text="Password must be at least 12 characters long"
    )
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)

    class Meta:
        model = User
        fields = (
            # Company fields
            'name', 'arabic_name', 'cr_number', 'moi_number', 'country_of_incorporation',
            # Admin fields
            'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name'
        )

    # ===== VALIDATIONS =====

    def validate_name(self, value):
        """Validate company name uniqueness."""
        if Company.objects.filter(name=value).exists():
            raise serializers.ValidationError("A company with this name already exists.")
        return value

    def validate_username(self, value):
        """Validate username format and uniqueness."""
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("Username must contain only alphanumeric characters and underscores.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """Validate passwords match and meet strength requirements."""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})

        try:
            validate_password(attrs.get('password'))
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})

        return attrs

    # ===== CREATE LOGIC =====

    def create(self, validated_data):
        """Create company and admin user."""
        # Extract company fields
        company_fields = {
            'name': validated_data.pop('name'),
            'arabic_name': validated_data.pop('arabic_name', None),
            'cr_number': validated_data.pop('cr_number', None),
            'moi_number': validated_data.pop('moi_number', None),
            'country_of_incorporation': validated_data.pop('country_of_incorporation', None),
            'parent_company': None,  # This is a main company
            'is_active': True,  # Main company is active by default
        }

        # Remove password_confirm (not needed for User creation)
        validated_data.pop('password_confirm')

        # Create the company
        company = Company.objects.create(**company_fields)

        # Create the admin user
        user = User.objects.create_user(
            company=company,
            type='Admin',  # Role as Admin
            **validated_data
        )

        return user

class ChangePasswordSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username_or_email = attrs.get('username_or_email')
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        # Ensure new passwords match
        if new_password != new_password_confirm:
            raise serializers.ValidationError({'new_password_confirm': 'New passwords do not match.'})

        # Find the user by username or email
        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                raise serializers.ValidationError({'username_or_email': 'User not found.'})

        # Check old password
        if not user.check_password(old_password):
            raise serializers.ValidationError({'old_password': 'Old password is incorrect.'})

        # Validate new password strength
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})

        # Save user instance for use in create/update
        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user
