"""
Custom User model for SubmitIQ with role-based access and approval system.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Company(models.Model):
    """
    Company model to manage different companies in the system.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Company name must be unique"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the company is active"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Custom User model with role-based access control and approval workflow.
    """
    
    ROLE_CHOICES = [
        ('SuperAdmin', 'SuperAdmin'),  # PIF system administrator
        ('Admin', 'Admin'),           # Company administrator
        ('User', 'User'),             # Regular company user
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'), 
        ('Rejected', 'Rejected'),
    ]
    
    # Core fields
    email = models.EmailField(unique=True, help_text="Email address must be unique")
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        help_text="Company this user belongs to"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='User',
        help_text="User role in the system"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Account approval status"
    )
    
    # Audit fields
    date_joined = models.DateTimeField(default=timezone.now)
    date_accepted = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when account was accepted"
    )
    date_rejected = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when account was rejected"
    )
    approved_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_users',
        help_text="Administrator who approved/rejected this account"
    )
    
    # Required fields for authentication
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def approve_account(self, approved_by_user):
        """Approve user account."""
        self.status = 'Accepted'
        self.date_accepted = timezone.now()
        self.date_rejected = None
        self.approved_by = approved_by_user
        self.is_active = True
        self.save()
    
    def reject_account(self, rejected_by_user, reason=None):
        """Reject user account."""
        self.status = 'Rejected'
        self.date_rejected = timezone.now()
        self.date_accepted = None
        self.approved_by = rejected_by_user
        self.is_active = False
        self.save()
    
    def is_superadmin(self):
        """Check if user is a superadmin."""
        return self.role == 'SuperAdmin'
    
    def is_admin(self):
        """Check if user is a company admin."""
        return self.role == 'Admin'
    
    def is_company_user(self):
        """Check if user is a regular company user."""
        return self.role == 'User'
    
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role in ['SuperAdmin', 'Admin']
    
    def can_approve_companies(self):
        """Check if user can approve new companies."""
        return self.role == 'SuperAdmin'
    
    def can_approve_users(self):
        """Check if user can approve other users."""
        return self.is_administrator() and self.status == 'Accepted'
