"""
JWT Token Service for SubmitIQ.

Handles JWT token creation, validation, and blacklisting with security-first approach.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

User = get_user_model()
logger = logging.getLogger(__name__)


class TokenService:
    """
    Service for handling JWT tokens with security features:
    - Token rotation and blacklisting
    - IP and User-Agent validation
    - Suspicious activity detection
    """

    @staticmethod
    def create_tokens_for_user(user: AbstractUser) -> Dict[str, str]:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user: The authenticated user
            
        Returns:
            Dictionary containing access and refresh tokens
        """
        try:
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            logger.info(f"Tokens created for user {user.id}")
            
            return {
                'access': str(access),
                'refresh': str(refresh),
                'access_expires_at': access['exp'],
                'refresh_expires_at': refresh['exp'],
            }
        except Exception as e:
            logger.error(f"Token creation failed for user {user.id}: {str(e)}")
            raise

    @staticmethod
    def refresh_access_token(
        refresh_token: str, 
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Refresh access token with security checks.
        
        Args:
            refresh_token: The refresh token string
            request_ip: Client IP address for validation
            user_agent: Client User-Agent for validation
            
        Returns:
            Dictionary containing new tokens
            
        Raises:
            TokenError: If token is invalid or suspicious activity detected
        """
        try:
            # Validate the refresh token
            token = RefreshToken(refresh_token)
            user = User.objects.get(id=token['user_id'])
            
            # Security check: Detect token reuse (simplified)
            # In production, implement more sophisticated checks
            TokenService._detect_suspicious_activity(user, request_ip, user_agent)
            
            # Blacklist the old refresh token
            token.blacklist()
            
            # Create new tokens
            new_tokens = TokenService.create_tokens_for_user(user)
            
            logger.info(f"Token refreshed for user {user.id}")
            return new_tokens
            
        except TokenError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise
        except User.DoesNotExist:
            logger.warning("Token refresh attempted for non-existent user")
            raise TokenError("Invalid token")
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise TokenError("Token refresh failed")

    @staticmethod
    def blacklist_token(refresh_token: str) -> bool:
        """
        Blacklist a refresh token (logout).
        
        Args:
            refresh_token: The refresh token to blacklist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("Token blacklisted successfully")
            return True
        except TokenError as e:
            logger.warning(f"Token blacklist failed: {str(e)}")
            return False

    @staticmethod
    def validate_access_token(access_token: str) -> Optional[AbstractUser]:
        """
        Validate an access token and return the associated user.
        
        Args:
            access_token: The access token to validate
            
        Returns:
            User object if token is valid, None otherwise
        """
        try:
            token = AccessToken(access_token)
            user = User.objects.get(id=token['user_id'])
            return user
        except (TokenError, User.DoesNotExist):
            return None

    @staticmethod
    def _detect_suspicious_activity(
        user: AbstractUser, 
        request_ip: Optional[str], 
        user_agent: Optional[str]
    ) -> None:
        """
        Detect suspicious token usage patterns.
        
        This is a simplified implementation. In production, implement:
        - IP geolocation checks
        - Device fingerprinting
        - Rate limiting per IP/user
        - Machine learning-based anomaly detection
        
        Args:
            user: The user attempting token refresh
            request_ip: Client IP address
            user_agent: Client User-Agent
            
        Raises:
            TokenError: If suspicious activity is detected
        """
        # Example: Check for too many refresh attempts
        # This should be implemented with proper rate limiting
        
        # Log the activity for monitoring
        logger.info(
            f"Token refresh activity - User: {user.id}, IP: {request_ip}, "
            f"User-Agent: {user_agent}"
        )
        
        # Implement your security checks here
        # For example:
        # - Check if IP is from a known bad actor list
        # - Verify IP geolocation consistency
        # - Check device fingerprint consistency
        # - Implement rate limiting
        
        pass  # Placeholder for actual implementation

    @staticmethod
    def force_logout_user(user: AbstractUser) -> int:
        """
        Force logout a user by blacklisting all their outstanding tokens.
        
        Args:
            user: The user to force logout
            
        Returns:
            Number of tokens blacklisted
        """
        try:
            # Get all outstanding tokens for the user
            outstanding_tokens = OutstandingToken.objects.filter(user=user)
            
            blacklisted_count = 0
            for outstanding_token in outstanding_tokens:
                # Check if token is not already blacklisted
                if not BlacklistedToken.objects.filter(token=outstanding_token).exists():
                    BlacklistedToken.objects.create(token=outstanding_token)
                    blacklisted_count += 1
            
            logger.info(f"Force logout: {blacklisted_count} tokens blacklisted for user {user.id}")
            return blacklisted_count
            
        except Exception as e:
            logger.error(f"Force logout failed for user {user.id}: {str(e)}")
            return 0

    @staticmethod
    def cleanup_expired_tokens() -> Dict[str, int]:
        """
        Clean up expired tokens from the database.
        This should be run periodically (e.g., via Django management command or celery task).
        
        Returns:
            Dictionary with cleanup statistics
        """
        now = datetime.now()
        
        # Delete expired outstanding tokens
        expired_outstanding = OutstandingToken.objects.filter(
            expires_at__lt=now
        )
        outstanding_count = expired_outstanding.count()
        expired_outstanding.delete()
        
        # Delete corresponding blacklisted tokens
        orphaned_blacklisted = BlacklistedToken.objects.filter(
            token__isnull=True
        )
        blacklisted_count = orphaned_blacklisted.count()
        orphaned_blacklisted.delete()
        
        logger.info(
            f"Token cleanup completed - Outstanding: {outstanding_count}, "
            f"Blacklisted: {blacklisted_count}"
        )
        
        return {
            'outstanding_deleted': outstanding_count,
            'blacklisted_deleted': blacklisted_count,
        }
