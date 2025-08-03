"""
Authentication views for SubmitIQ.

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
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    TokenRefreshSerializer,
    PasswordChangeSerializer,
    UserProfileSerializer,
)
from .services.token_service import TokenService
from .repositories.user_repository import UserRepository

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


@extend_schema_view(
    post=extend_schema(
        summary="User Registration",
        description="Register a new user account with security validations",
        tags=["Authentication"]
    )
)
class RegisterView(AuthenticationAPIView):
    """
    User registration endpoint with security features.
    """

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={
            201: UserProfileSerializer,
            400: "Validation errors"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Register a new user account.
        """
        client_info = self.get_client_info(request)
        
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Create user using repository
                user = UserRepository.create_user(
                    username=serializer.validated_data['username'],
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    first_name=serializer.validated_data['first_name'],
                    last_name=serializer.validated_data['last_name'],
                )
                
                # Log successful registration
                logger.info(
                    f"User registered successfully - ID: {user.id}, "
                    f"IP: {client_info['ip_address']}"
                )
                
                # Return user profile
                profile_serializer = UserProfileSerializer(user)
                return Response(
                    profile_serializer.data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                logger.error(
                    f"Registration failed - IP: {client_info['ip_address']}, "
                    f"Error: {str(e)}"
                )
                return Response(
                    {'error': 'Registration failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Log validation failures
        logger.warning(
            f"Registration validation failed - IP: {client_info['ip_address']}, "
            f"Errors: {serializer.errors}"
        )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    post=extend_schema(
        summary="User Login",
        description="Authenticate user and return JWT tokens",
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
            200: {
                "type": "object",
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                    "user": UserProfileSerializer,
                }
            },
            401: "Invalid credentials",
            429: "Too many requests"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Authenticate user and return JWT tokens.
        """
        client_info = self.get_client_info(request)
        
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            try:
                # Create tokens
                tokens = TokenService.create_tokens_for_user(user)
                
                # Update last login
                UserRepository.update_last_login(user)
                
                # Log successful login
                logger.info(
                    f"User login successful - User: {user.id}, "
                    f"IP: {client_info['ip_address']}"
                )
                
                # Return tokens and user profile
                user_profile = UserProfileSerializer(user)
                return Response({
                    'access': tokens['access'],
                    'refresh': tokens['refresh'],
                    'user': user_profile.data,
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(
                    f"Token creation failed - User: {user.id}, "
                    f"IP: {client_info['ip_address']}, Error: {str(e)}"
                )
                return Response(
                    {'error': 'Authentication failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Log authentication failures
        logger.warning(
            f"Login attempt failed - IP: {client_info['ip_address']}, "
            f"Data: {request.data.get('username_or_email', 'N/A')}"
        )
        
        return Response(
            {'error': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@extend_schema_view(
    post=extend_schema(
        summary="Refresh Token",
        description="Refresh access token using refresh token",
        tags=["Authentication"]
    )
)
class TokenRefreshView(AuthenticationAPIView):
    """
    Token refresh endpoint with security checks.
    """

    @extend_schema(
        request=TokenRefreshSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                }
            },
            401: "Invalid token",
            429: "Too many requests"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Refresh access token using refresh token.
        """
        client_info = self.get_client_info(request)
        
        serializer = TokenRefreshSerializer(data=request.data)
        if serializer.is_valid():
            refresh_token = serializer.validated_data['refresh']
            
            try:
                # Refresh tokens with security checks
                new_tokens = TokenService.refresh_access_token(
                    refresh_token=refresh_token,
                    request_ip=client_info['ip_address'],
                    user_agent=client_info['user_agent']
                )
                
                logger.info(f"Token refreshed - IP: {client_info['ip_address']}")
                
                return Response(new_tokens, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.warning(
                    f"Token refresh failed - IP: {client_info['ip_address']}, "
                    f"Error: {str(e)}"
                )
                return Response(
                    {'error': 'Invalid or expired token.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    post=extend_schema(
        summary="User Logout",
        description="Logout user and blacklist refresh token",
        tags=["Authentication"]
    )
)
class LogoutView(APIView):
    """
    User logout endpoint with token blacklisting.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "refresh": {"type": "string", "description": "Refresh token to blacklist"}
            }
        },
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}},
            400: "Invalid request"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Logout user and blacklist refresh token.
        """
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Blacklist the token
            success = TokenService.blacklist_token(refresh_token)
            
            if success:
                logger.info(f"User {request.user.id} logged out successfully")
                return Response(
                    {'message': 'Logout successful.'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Invalid token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Logout failed for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Logout failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    retrieve=extend_schema(
        summary="Get User Profile",
        description="Get current user's profile information",
        tags=["User Profile"]
    ),
    partial_update=extend_schema(
        summary="Update User Profile",
        description="Update current user's profile information",
        tags=["User Profile"]
    )
)
class UserProfileViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    """
    User profile management viewset.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        """Return the current user."""
        return self.request.user

    @action(detail=False, methods=['post'], url_path='change-password')
    @extend_schema(
        summary="Change Password",
        description="Change user's password",
        request=PasswordChangeSerializer,
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}},
            400: "Validation errors"
        }
    )
    def change_password(self, request: Request) -> Response:
        """
        Change user's password.
        """
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                # Change password using repository
                success = UserRepository.change_password(
                    user=request.user,
                    new_password=serializer.validated_data['new_password']
                )
                
                if success:
                    # Force logout from all devices for security
                    TokenService.force_logout_user(request.user)
                    
                    logger.info(f"Password changed for user {request.user.id}")
                    return Response(
                        {'message': 'Password changed successfully. Please log in again.'},
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {'error': 'Password change failed.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            except Exception as e:
                logger.error(f"Password change failed for user {request.user.id}: {str(e)}")
                return Response(
                    {'error': 'Password change failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
