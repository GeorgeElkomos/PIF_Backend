from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin

class Company(models.Model):
    """
    Stores core information for both main companies and entities.
    Entities will have parent_company set.
    Main companies will have parent_company = None.
    """
    name = models.CharField(max_length=100, unique=True)
    arabic_name = models.CharField(max_length=100, null=True, blank=True)
    cr_number = models.CharField(max_length=50, null=True, blank=True)
    moi_number = models.CharField(max_length=50, null=True, blank=True)
    country_of_incorporation = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    parent_company = models.ForeignKey(
        'self',  # self-referencing FK
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='entities'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class User(AbstractUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    ROLE_CHOICES = [
        ('SuperAdmin', 'SuperAdmin'),  # PIF system administrator
        ('Admin', 'Admin'),           # Company administrator
        ('User', 'User'),             # Regular company user
    ]
    type = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Admin')
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        help_text="Company this user belongs to"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.username


