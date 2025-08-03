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
from .models import Company

User = get_user_model()


class CompanyRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for company registration with admin user.
    """
    # Company fields
    company_name = serializers.CharField(
        max_length=100,
        help_text="Name of the company"
    )
    
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
            'company_name',
            'username', 'email', 'password', 'password_confirm', 
            'first_name', 'last_name'
        )
    
    def validate_company_name(self, value):
        """Validate company name is unique."""
        if Company.objects.filter(name=value).exists():
            raise serializers.ValidationError("A company with this name already exists.")
        return value
    
    def validate_username(self, value):
        """Validate username format and uniqueness."""
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "Username must contain only alphanumeric characters and underscores."
            )
        
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation and strength."""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Validate password strength
        try:
            validate_password(password)
            PasswordService.validate_password_strength(password)
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})
        
        return attrs
    
    def create(self, validated_data):
        """Create company and admin user."""
        # Extract company data
        company_data = {
            'name': validated_data.pop('company_name'),
        }
        
        # Remove password_confirm
        validated_data.pop('password_confirm')
        
        # Create company
        company = Company.objects.create(**company_data)
        
        # Create admin user
        user = User.objects.create_user(
            company=company,
            role='Admin',
            status='Pending',
            is_active=False,
            **validated_data
        )
        
        return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration serializer for regular users created by company admins.
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

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True, 'max_length': 30},
            'last_name': {'required': True, 'max_length': 30},
        }

    def validate_username(self, value):
        """Validate username format and uniqueness."""
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError(
                "Username can only contain letters, numbers, and underscores."
            )
        
        if User.objects.filter(username=value).exists():
            raise ValidationError("A user with this username already exists.")
        
        return value

    def validate_email(self, value):
        """Validate email uniqueness and format."""
        if User.objects.filter(email=value).exists():
            raise ValidationError("A user with this email already exists.")
        
        return value.lower()

    def validate(self, attrs):
        """Validate password confirmation and strength."""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Validate password strength
        try:
            validate_password(password)
            PasswordService.validate_password_strength(password)
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})
        
        return attrs
    
    def create(self, validated_data):
        """Create user with company from admin user context."""
        # This will be called by company admins to create users
        # The company will be set from the request context
        validated_data.pop('password_confirm')
        
        # Get the company from the admin user (set in view)
        company = self.context['company']
        
        user = User.objects.create_user(
            company=company,
            role='User',
            status='Accepted',  # Company users are auto-approved
            is_active=True,
            **validated_data
        )
        
        return user


class CompanyApprovalSerializer(serializers.ModelSerializer):
    """
    Serializer for approving/rejecting company admin users.
    """
    status = serializers.ChoiceField(
        choices=[('Accepted', 'Accepted'), ('Rejected', 'Rejected')],
        help_text="Approval decision"
    )
    rejection_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Reason for rejection (optional)"
    )
    
    class Meta:
        model = User
        fields = ['status', 'rejection_reason']
    
    def update(self, instance, validated_data):
        """Update user approval status."""
        status = validated_data['status']
        rejection_reason = validated_data.get('rejection_reason', '')
        
        if status == 'Accepted':
            instance.approve_account(self.context['approved_by'])
        else:
            instance.reject_account(self.context['approved_by'], rejection_reason)
        
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users with company information.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'status', 'company_name', 'date_joined', 'is_active'
        ]


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
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name', 
            'role', 'status', 'company_name', 'date_joined', 'date_accepted', 
            'date_rejected', 'last_login'
        )
        read_only_fields = (
            'id', 'username', 'role', 'status', 'company_name', 'date_joined', 
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
