"""
Management command to create the default SuperAdmin user for PIF company.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from authentication.models import Company

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default SuperAdmin user for PIF company'

    def handle(self, *args, **options):
        """Create the default SuperAdmin user and PIF company."""
        
        # First, create or get PIF company
        try:
            pif_company, created = Company.objects.get_or_create(
                name='PIF',
                defaults={
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Created PIF company successfully!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('PIF company already exists!')
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating PIF company: {str(e)}')
            )
            return
        
        # Check if SuperAdmin already exists
        existing_user = User.objects.filter(username='PIF_SubmitIQ').first()
        if existing_user:
            self.stdout.write(
                self.style.WARNING('SuperAdmin user "PIF_SubmitIQ" already exists with incorrect data!')
            )
            self.stdout.write(
                self.style.WARNING('Deleting existing user and creating new one with correct data...')
            )
            # Delete the existing user with wrong data
            existing_user.delete()
            self.stdout.write(
                self.style.SUCCESS('Deleted existing user with incorrect data.')
            )
        
        try:
            # Create SuperAdmin user
            admin_user = User.objects.create_user(
                username='PIF_SubmitIQ',
                email='PIF_SubmitIQ@PIF.com',
                password='PIF_SubmitIQ123',
                first_name='PIF',
                last_name='SuperAdmin',
                company=pif_company,
                role='SuperAdmin',
                status='Accepted',
                is_active=True,
                is_staff=True,
                is_superuser=True,
                date_accepted=timezone.now()
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created SuperAdmin user:\n'
                    f'  Username: {admin_user.username}\n'
                    f'  Email: {admin_user.email}\n'
                    f'  Company: {admin_user.company.name}\n'
                    f'  Role: {admin_user.role}\n'
                    f'  Status: {admin_user.status}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating SuperAdmin user: {str(e)}')
            )
