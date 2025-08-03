"""
Password management service for SubmitIQ.

Handles password changes with old password verification.
"""

import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


class PasswordService:
    """Service for handling password operations."""
    
    @staticmethod
    def change_password(user, old_password, new_password):
        """
        Change user password with old password verification.
        
        Args:
            user: User instance
            old_password: Current password
            new_password: New password
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            ValidationError: If validation fails
        """
        
        # Verify old password
        if not user.check_password(old_password):
            logger.warning(f"Failed password change attempt for user {user.username} - incorrect old password")
            raise ValidationError("Current password is incorrect.")
        
        # Validate new password
        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            raise ValidationError(e.messages)
        
        # Check if new password is different from old
        if user.check_password(new_password):
            raise ValidationError("New password must be different from current password.")
        
        # Change password
        user.set_password(new_password)
        user.save(update_fields=['password'])
        
        logger.info(f"Password successfully changed for user {user.username}")
        return True
    
    @staticmethod
    def reset_password_by_admin(admin_user, target_user, new_password):
        """
        Reset user password by administrator.
        
        Args:
            admin_user: Administrator user performing the reset
            target_user: User whose password is being reset
            new_password: New password
            
        Returns:
            bool: True if password reset successfully
            
        Raises:
            ValidationError: If validation fails
        """
        
        # Check if admin has permission
        if not admin_user.can_approve_users():
            raise ValidationError("You don't have permission to reset passwords.")
        
        # Validate new password
        try:
            validate_password(new_password, target_user)
        except DjangoValidationError as e:
            raise ValidationError(e.messages)
        
        # Reset password
        target_user.set_password(new_password)
        target_user.save(update_fields=['password'])
        
        logger.info(f"Password reset by admin {admin_user.username} for user {target_user.username}")
        return True
