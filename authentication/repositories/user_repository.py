"""
User Repository for SubmitIQ.

Handles all user-related data access operations.
"""

import logging
from typing import Optional, List, Dict, Any
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRepository:
    """
    Repository for user data access operations.
    Isolates data access logic from business logic.
    """

    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        **extra_fields
    ) -> AbstractUser:
        """
        Create a new user with validation.
        
        Args:
            username: Unique username
            email: User email address
            password: Raw password (will be hashed)
            **extra_fields: Additional user fields
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If validation fails
        """
        try:
            with transaction.atomic():
                # Validate required fields
                if not username or not email:
                    raise ValueError("Username and email are required")
                
                # Check for existing user
                if User.objects.filter(Q(username=username) | Q(email=email)).exists():
                    raise ValueError("User with this username or email already exists")
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    **extra_fields
                )
                
                logger.info(f"User created successfully: {user.id}")
                return user
                
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            raise

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[AbstractUser]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance or None if not found
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[AbstractUser]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance or None if not found
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[AbstractUser]:
        """
        Get user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User instance or None if not found
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_username_or_email(identifier: str) -> Optional[AbstractUser]:
        """
        Get user by username or email.
        
        Args:
            identifier: Username or email to search for
            
        Returns:
            User instance or None if not found
        """
        try:
            return User.objects.get(
                Q(username=identifier) | Q(email=identifier)
            )
        except User.DoesNotExist:
            return None

    @staticmethod
    def update_user(
        user: AbstractUser,
        **fields
    ) -> AbstractUser:
        """
        Update user fields.
        
        Args:
            user: User instance to update
            **fields: Fields to update
            
        Returns:
            Updated user instance
        """
        try:
            with transaction.atomic():
                for field, value in fields.items():
                    if hasattr(user, field):
                        setattr(user, field, value)
                
                user.save()
                logger.info(f"User {user.id} updated successfully")
                return user
                
        except Exception as e:
            logger.error(f"User update failed for user {user.id}: {str(e)}")
            raise

    @staticmethod
    def change_password(user: AbstractUser, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user: User instance
            new_password: New password (raw)
            
        Returns:
            True if successful
        """
        try:
            user.set_password(new_password)
            user.save()
            logger.info(f"Password changed for user {user.id}")
            return True
        except Exception as e:
            logger.error(f"Password change failed for user {user.id}: {str(e)}")
            return False

    @staticmethod
    def update_last_login(user: AbstractUser) -> None:
        """
        Update user's last login timestamp.
        
        Args:
            user: User instance
        """
        try:
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        except Exception as e:
            logger.error(f"Last login update failed for user {user.id}: {str(e)}")

    @staticmethod
    def deactivate_user(user: AbstractUser) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user: User instance to deactivate
            
        Returns:
            True if successful
        """
        try:
            user.is_active = False
            user.save()
            logger.info(f"User {user.id} deactivated")
            return True
        except Exception as e:
            logger.error(f"User deactivation failed for user {user.id}: {str(e)}")
            return False

    @staticmethod
    def activate_user(user: AbstractUser) -> bool:
        """
        Activate a user account.
        
        Args:
            user: User instance to activate
            
        Returns:
            True if successful
        """
        try:
            user.is_active = True
            user.save()
            logger.info(f"User {user.id} activated")
            return True
        except Exception as e:
            logger.error(f"User activation failed for user {user.id}: {str(e)}")
            return False

    @staticmethod
    def get_active_users(limit: Optional[int] = None) -> List[AbstractUser]:
        """
        Get list of active users.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of active users
        """
        queryset = User.objects.filter(is_active=True).order_by('-date_joined')
        if limit:
            queryset = queryset[:limit]
        return list(queryset)

    @staticmethod
    def search_users(query: str, limit: int = 20) -> List[AbstractUser]:
        """
        Search users by username, email, or name.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        return list(
            User.objects.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            ).filter(is_active=True)[:limit]
        )

    @staticmethod
    def get_user_stats() -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user statistics
        """
        try:
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            inactive_users = total_users - active_users
            
            # Users registered in last 30 days
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recent_users = User.objects.filter(
                date_joined__gte=thirty_days_ago
            ).count()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': inactive_users,
                'recent_users': recent_users,
            }
        except Exception as e:
            logger.error(f"Failed to get user stats: {str(e)}")
            return {
                'total_users': 0,
                'active_users': 0,
                'inactive_users': 0,
                'recent_users': 0,
            }
