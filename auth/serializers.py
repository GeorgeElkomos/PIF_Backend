"""
Authentication serializers for SubmitIQ.

Security-first serializers with comprehensive validation.
"""

import re
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .services.password_service import PasswordService

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration serializer for Company users with security validations.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=12,
        help_text="Password must be at least 12 characters long"
    )
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    username = serializers.CharField(
        min_length=3,
        max_length=30,
        help_text="Username must be 3-30 characters, alphanumeric and underscores only"
    )
    role = serializers.ChoiceField(
        choices=[('Company', 'Company')],
        default='Company',
        help_text="Role is automatically set to Company for registration"
    )
    status = serializers.CharField(
        read_only=True,
        default='Pending',
        help_text="Status is automatically set to Pending for new registrations"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'role', 'status')
        extra_kwargs = {
            'first_name': {'required': True, 'max_length': 30},
            'last_name': {'required': True, 'max_length': 30},
        }

    def validate_username(self, value):
        """Validate username format and uniqueness."""
        # Allow only alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError(
                "Username can only contain letters, numbers, and underscores."
            )
        
        # Check uniqueness
        if User.objects.filter(username=value).exists():
            raise ValidationError("A user with this username already exists.")
        
        return value

    def validate_email(self, value):
        """Validate email uniqueness and format."""
        if User.objects.filter(email=value).exists():
            raise ValidationError("A user with this email already exists.")
        
        # Additional email validation can be added here
        return value.lower()

    def validate_password(self, value):
        """Validate password strength."""
        # Use Django's password validators
        validate_password(value)
        
        # Additional custom validations
        if not re.search(r'[A-Z]', value):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'[0-9]', value):
            raise ValidationError("Password must contain at least one digit.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError("Password must contain at least one special character.")
        
        return value

    def validate_role(self, value):
        """Ensure role is always Company for registration."""
        if value != 'Company':
            raise ValidationError("New registrations must have Company role.")
        return value

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise ValidationError("Passwords do not match.")
        
        # Remove password_confirm as it's not needed for user creation
        attrs.pop('password_confirm')
        
        # Force role to Company and status to Pending
        attrs['role'] = 'Company'
        attrs['status'] = 'Pending'
        
        return attrs

    def create(self, validated_data):
        """Create user with validated data."""
        password = validated_data.pop('password')
        
        # Create user with Company role and Pending status
        user = User.objects.create_user(
            **validated_data,
            role='Company',
            status='Pending',
            is_active=False  # Inactive until approved
        )
        user.set_password(password)
        user.save()
        return user


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


class TokenRefreshSerializer(serializers.Serializer):
    """
    Token refresh serializer with security metadata.
    """
    refresh = serializers.CharField(help_text="Refresh token")
    
    # Optional security fields for enhanced validation
    ip_address = serializers.IPAddressField(required=False)
    user_agent = serializers.CharField(max_length=500, required=False)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Password change serializer for authenticated users using the service layer.
    """
    current_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=12,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_new_password(self, value):
        """Validate new password strength."""
        user = self.context['request'].user
        validate_password(value, user)
        
        # Additional custom validations
        if not re.search(r'[A-Z]', value):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'[0-9]', value):
            raise ValidationError("Password must contain at least one digit.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError("Password must contain at least one special character.")
        
        return value

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise ValidationError("New passwords do not match.")
        
        attrs.pop('new_password_confirm')
        return attrs

    def save(self):
        """Change password using the password service."""
        user = self.context['request'].user
        current_password = self.validated_data['current_password']
        new_password = self.validated_data['new_password']
        
        # Use the password service to change password
        PasswordService.change_password(user, current_password, new_password)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer for safe user data exposure with role and status info.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name', 
            'role', 'status', 'date_joined', 'date_accepted', 'date_rejected', 'last_login'
        )
        read_only_fields = (
            'id', 'username', 'role', 'status', 'date_joined', 
            'date_accepted', 'date_rejected', 'last_login'
        )

    def get_full_name(self, obj):
        """Get user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip()

    def validate_email(self, value):
        """Validate email uniqueness for updates."""
        user = self.instance
        if user and User.objects.filter(email=value).exclude(id=user.id).exists():
            raise ValidationError("A user with this email already exists.")
        return value.lower()


class UserListSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for list views with role and status information.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'email', 'role', 'status', 
            'is_active', 'date_joined', 'date_accepted', 'date_rejected'
        )

    def get_full_name(self, obj):
        """Get user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip()


class UserApprovalSerializer(serializers.Serializer):
    """
    Serializer for approving/rejecting user accounts.
    """
    action = serializers.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        help_text="Action to take on the user account"
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Reason for rejection (optional for approval)"
    )
