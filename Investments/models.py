"""
Custom User model for SubmitIQ with role-based access and approval system.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator


from django.conf import settings
from authentication.models import Company


class Investment(models.Model):
    """
    Company model to manage different companies in the system.
    """
    PERIOD_CHOICES = [
        ('First Half', 'First Half'),
        ('Third Quarter', 'Third Quarter'),
        ('Fourth Quarter', 'Fourth Quarter'),
    ]
    RelationShip_Choices = [
        ('Subsidiary', 'Subsidiary'),
        ('Joint venture', 'Joint venture'),
        ('Associate', 'Associate'),
        ('Subsidiary of Associate', 'Subsidiary of Associate'),
        ('Joint Venture of Associate', 'Joint Venture of Associate'),
        ('Associate of Associate', 'Associate of Associate'),
        ('Subsidiary of a JV', 'Subsidiary of a JV'),
        ('Associate', 'Associate'),
        ('Subsidiary', 'Subsidiary'),
        ('Associate of a JV', 'Associate of a JV'),
        ('Joint Venture of a JV', 'Joint Venture of a JV'),
    ]
    year = models.PositiveIntegerField(
        help_text="Year of the investment, must be a positive integer",
        validators=[MinValueValidator(2000)],
        verbose_name="Investment Year",
        error_messages={
            'min_value': "Year must be 2000 or later."
        },
        blank=False,
        null=False
    )
    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        help_text="Period of the investment (First Half, Third Quarter, Fourth Quarter)"
    )
    asset_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        default=None,
        help_text="Unique code for the investment asset"
    )
    entity = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='investments_as_entity',
        blank=False,
        null=False,
        help_text="Company associated with the investment"
    )
    ownership = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Ownership percentage of the investment, represented as a decimal"
    )
    aquization_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date when the investment was acquired"
    )
    direct_parent = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='investments_as_parent',
        blank=False,
        null=False,
        help_text="Direct parent investment, if any"
    )
    Ultimate_parent = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default=None,
        help_text="Ultimate parent company of the investment"
    )
    RelationShip_of_investment = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default=None,
        choices=RelationShip_Choices,
        verbose_name="Relationship of Investment",
        help_text="Relationship of the investment to the parent company"
    )
    direct = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name="Direct Investment",
        help_text="Indicates if the investment is direct or indirect"
    )
    Entity_Principal_activities = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="Principal activities of the investment entity"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_investments',
        help_text="User who created the investment record",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_investments',
        help_text="User who updated the investment record",
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'investments'
        verbose_name = 'Investment'
        verbose_name_plural = 'Investments'
        ordering = ['-year', 'period']

    
    def clean(self):
        if self.company and not self.company.is_active:
            raise ValidationError("Cannot assign an inactive company to an investment.")


    def __str__(self):
        return self.year + " - " + self.period + " - " + str(self.entity)
