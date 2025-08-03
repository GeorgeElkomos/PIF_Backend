"""
Updated authentication views for SubmitIQ with company-based user management.

Security-first API views with comprehensive authentication and authorization.
"""

import logging
from typing import Dict, Any
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .serializers import (
    CompanyRegistrationSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    TokenRefreshSerializer,
    PasswordChangeSerializer,
    UserProfileSerializer,
    UserListSerializer,
    CompanyApprovalSerializer,
)
from .services.token_service import TokenService
from .repositories.user_repository import UserRepository
from .models import Company

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationAPIView(APIView):
    """
    Base class for authentication views with security features.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def get_client_info(self, request: Request) -> Dict[str, str]:
        """Extract client information for security logging."""
        return {
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'forwarded_for': request.META.get('HTTP_X_FORWARDED_FOR', ''),
        }


class SuperAdminPermission(permissions.BasePermission):
    """
    Permission class for SuperAdmin only access.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_approve_companies()
        )


class AdminPermission(permissions.BasePermission):
    """
    Permission class for Admin and SuperAdmin access.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_manage_users()
        )


@extend_schema_view(
    post=extend_schema(
        summary="Company Registration",
        description="Register a new company with admin user. Requires SuperAdmin approval.",
        tags=["Authentication"]
    )
)
class CompanyRegisterView(AuthenticationAPIView):
    """
    Company registration endpoint for creating new companies with admin users.
    """

    @extend_schema(
        request=CompanyRegistrationSerializer,
        responses={
            201: UserProfileSerializer,
            400: "Validation errors"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Register a new company with admin user.
        """
        client_info = self.get_client_info(request)
        
        serializer = CompanyRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Create company and admin user
                user = serializer.save()
                
                # Log successful registration
                logger.info(
                    f"Company registered successfully - Company: {user.company.name}, "
                    f"Admin User: {user.username}, IP: {client_info['ip_address']}"
                )
                
                # Return user profile
                profile_serializer = UserProfileSerializer(user)
                return Response(
                    profile_serializer.data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                logger.error(
                    f"Registration failed - Error: {str(e)}, "
                    f"IP: {client_info['ip_address']}"
                )
                return Response(
                    {'error': 'Registration failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    post=extend_schema(
        summary="User Login",
        description="Authenticate user and receive JWT tokens",
        tags=["Authentication"]
    )
)
class LoginView(AuthenticationAPIView):
    """
    User login endpoint with JWT token generation.
    """
    
    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: "Login successful with tokens and user profile",
            401: "Invalid credentials"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Authenticate user with username/email and password.
        """
        client_info = self.get_client_info(request)
        
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Authenticate user using repository
                user = UserRepository.authenticate_user(
                    username_or_email=serializer.validated_data['username_or_email'],
                    password=serializer.validated_data['password']
                )
                
                if user:
                    # Generate JWT tokens
                    tokens = TokenService.generate_tokens_for_user(user)
                    
                    # Log successful login
                    logger.info(
                        f"User logged in - ID: {user.id}, "
                        f"IP: {client_info['ip_address']}"
                    )
                    
                    # Return tokens and user profile
                    return Response({
                        'access': tokens['access'],
                        'refresh': tokens['refresh'],
                        'user': UserProfileSerializer(user).data
                    })
                else:
                    logger.warning(
                        f"Login failed - Invalid credentials, "
                        f"IP: {client_info['ip_address']}"
                    )
                    return Response(
                        {'error': 'Invalid credentials.'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                    
            except Exception as e:
                logger.error(
                    f"Login failed - Error: {str(e)}, "
                    f"IP: {client_info['ip_address']}"
                )
                return Response(
                    {'error': 'Authentication failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary="List Pending Company Registrations",
        description="Get list of pending company admin registrations (SuperAdmin only)",
        tags=["Company Management"]
    ),
    post=extend_schema(
        summary="Approve/Reject Company Registration",
        description="Approve or reject a pending company admin registration (SuperAdmin only)",
        tags=["Company Management"]
    )
)
class CompanyApprovalViewSet(GenericViewSet, ListModelMixin):
    """
    ViewSet for SuperAdmin to manage company registrations.
    """
    permission_classes = [SuperAdminPermission]
    throttle_classes = [UserRateThrottle]
    serializer_class = UserListSerializer
    
    def get_queryset(self):
        """Get pending company admin users."""
        return User.objects.filter(
            role='Admin',
            status='Pending'
        ).select_related('company')
    
    @extend_schema(
        request=CompanyApprovalSerializer,
        responses={
            200: UserProfileSerializer,
            404: "User not found",
            400: "Invalid status"
        }
    )
    @action(detail=True, methods=['post'])
    def approve_reject(self, request, pk=None):
        """
        Approve or reject a pending company admin registration.
        """
        try:
            user = User.objects.get(pk=pk, role='Admin', status='Pending')
        except User.DoesNotExist:
            return Response(
                {'error': 'Pending company admin not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CompanyApprovalSerializer(
            user, 
            data=request.data,
            context={'approved_by': request.user}
        )
        
        if serializer.is_valid():
            updated_user = serializer.save()
            
            # Log approval/rejection
            logger.info(
                f"Company admin {updated_user.status.lower()} - "
                f"User: {updated_user.username}, "
                f"Company: {updated_user.company.name}, "
                f"By: {request.user.username}"
            )
            
            return Response(
                UserProfileSerializer(updated_user).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary="List Company Users",
        description="Get list of users in the admin's company",
        tags=["User Management"]
    ),
    post=extend_schema(
        summary="Create Company User",
        description="Create a new user in the admin's company",
        tags=["User Management"]
    )
)
class CompanyUserManagementViewSet(GenericViewSet, ListModelMixin):
    """
    ViewSet for company admins to manage their users.
    """
    permission_classes = [AdminPermission]
    throttle_classes = [UserRateThrottle]
    serializer_class = UserListSerializer
    
    def get_queryset(self):
        """Get users from the admin's company."""
        # Both SuperAdmin and Company admin can only see their company users
        return User.objects.filter(
            company=self.request.user.company
        ).select_related('company')
    
    @extend_schema(
        request=UserRegistrationSerializer,
        responses={
            201: UserProfileSerializer,
            400: "Validation errors"
        }
    )
    def create(self, request):
        """
        Create a new user in the admin's company.
        """
        if not request.user.is_admin() and not request.user.is_superadmin():
            return Response(
                {'error': 'Permission denied. Only company admins can create users.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserRegistrationSerializer(
            data=request.data,
            context={'company': request.user.company}
        )
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                # Log user creation
                logger.info(
                    f"User created - Username: {user.username}, "
                    f"Company: {user.company.name}, "
                    f"Created by: {request.user.username}"
                )
                
                return Response(
                    UserProfileSerializer(user).data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                logger.error(
                    f"User creation failed - Error: {str(e)}, "
                    f"Admin: {request.user.username}"
                )
                return Response(
                    {'error': 'User creation failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Keep the existing views for backward compatibility
from .views import (
    TokenRefreshView,
    LogoutView,
    UserProfileViewSet,
)
