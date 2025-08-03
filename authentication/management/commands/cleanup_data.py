"""
Management command to clean up and format existing user data for the new company structure.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from authentication.models import Company

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean up and format existing user data for new company structure'

    def handle(self, *args, **options):
        """Clean up existing data and prepare for new structure."""
        
        self.stdout.write(
            self.style.WARNING('Starting data cleanup and formatting...')
        )
        
        # First, create PIF company if it doesn't exist
        try:
            pif_company, created = Company.objects.get_or_create(
                name='PIF',
                defaults={'is_active': True}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Created PIF company successfully!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('PIF company already exists.')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating PIF company: {str(e)}')
            )
            return
        
        # Get all existing users
        existing_users = User.objects.all()
        self.stdout.write(
            self.style.WARNING(f'Found {existing_users.count()} existing users.')
        )
        
        # Process each existing user
        for user in existing_users:
            try:
                updated = False
                
                # Check if user has no company assigned
                if not hasattr(user, 'company') or user.company is None:
                    user.company = pif_company
                    updated = True
                    self.stdout.write(
                        self.style.WARNING(f'Assigned PIF company to user: {user.username}')
                    )
                
                # Update role if it's the old format
                if hasattr(user, 'role'):
                    if user.role == 'Administrator':
                        user.role = 'SuperAdmin'
                        updated = True
                        self.stdout.write(
                            self.style.WARNING(f'Updated role from Administrator to SuperAdmin for: {user.username}')
                        )
                    elif user.role == 'Company':
                        user.role = 'Admin'
                        updated = True
                        self.stdout.write(
                            self.style.WARNING(f'Updated role from Company to Admin for: {user.username}')
                        )
                
                # Ensure proper status
                if not hasattr(user, 'status') or user.status is None:
                    user.status = 'Accepted'
                    updated = True
                    self.stdout.write(
                        self.style.WARNING(f'Set status to Accepted for: {user.username}')
                    )
                
                # Set date_accepted if user is accepted but doesn't have the date
                if user.status == 'Accepted' and not user.date_accepted:
                    user.date_accepted = timezone.now()
                    updated = True
                    self.stdout.write(
                        self.style.WARNING(f'Set date_accepted for: {user.username}')
                    )
                
                # Save if any updates were made
                if updated:
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated user: {user.username}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'User {user.username} is already properly formatted.')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating user {user.username}: {str(e)}')
                )
        
        # Show final summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('DATA CLEANUP SUMMARY'))
        self.stdout.write('='*50)
        
        # Count users by company
        companies = Company.objects.all()
        for company in companies:
            user_count = User.objects.filter(company=company).count()
            self.stdout.write(
                self.style.WARNING(f'Company: {company.name} - Users: {user_count}')
            )
        
        # Count users by role
        for role_choice in User.ROLE_CHOICES:
            role_code = role_choice[0]
            role_name = role_choice[1]
            user_count = User.objects.filter(role=role_code).count()
            self.stdout.write(
                self.style.WARNING(f'Role: {role_name} - Users: {user_count}')
            )
        
        # Count users by status
        for status_choice in User.STATUS_CHOICES:
            status_code = status_choice[0]
            status_name = status_choice[1]
            user_count = User.objects.filter(status=status_code).count()
            self.stdout.write(
                self.style.WARNING(f'Status: {status_name} - Users: {user_count}')
            )
        
        self.stdout.write('\n' + self.style.SUCCESS('Data cleanup completed successfully!'))
        self.stdout.write(self.style.WARNING('You can now run: python manage.py create_admin'))
