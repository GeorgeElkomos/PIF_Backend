from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from period_deadline.models import PeriodDeadline
class Investment(models.Model):

    RELATIONSHIP_CHOICES = [
        ('Subsidiary', 'Subsidiary'),
        ('Associate', 'Associate'),
        ('JV', 'Joint Venture'),
    ]

    DIRECT_CHOICES = [
        ('Direct', 'Direct'),
        ('Indirect', 'Indirect'),
    ]

    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000)],
        verbose_name="Investment Year",
        help_text="Year of the investment, must be 2000 or later"
    )
    time_period = models.CharField(
        max_length=20,
        choices=PeriodDeadline.TIME_PERIOD_CHOICES,
        help_text="Time period of the investment"
    )
    asset_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Unique code for the investment asset"
    )
    entity_name = models.CharField(
        max_length=255,
        help_text="Name of the entity"
    )
    arabic_legal_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Arabic legal name of the entity"
    )
    commercial_registration_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Commercial Registration (CR) Number"
    )
    moi_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="MOI (700) Number"
    )
    country_of_incorporation = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Country of Incorporation"
    )
    ownership_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Ownership Percentage (%)"
    )
    acquisition_disposal_date = models.DateField(
        blank=True,
        null=True,
        help_text="Acquisition/Disposal Date (only for entities acquired/disposed)"
    )
    direct_parent = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Direct Parent"
    )
    ultimate_parent = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Ultimate Parent"
    )
    relationship_of_investment = models.CharField(
        max_length=50,
        choices=RELATIONSHIP_CHOICES,
        blank=True,
        null=True,
        help_text="Relationship of investment (Subsidiary / Associate / JV)"
    )
    direct_or_indirect = models.CharField(
        max_length=10,
        choices=DIRECT_CHOICES,
        blank=True,
        null=True,
        help_text="Direct or Indirect investment"
    )
    entities_principal_activities = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Entity's Principal Activities"
    )
    is_submitted = models.BooleanField(
        default=False,
        help_text="Indicates if the investment record is submitted"
    )
    submitted_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when submitted"
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='submitted_investments',
        blank=True,
        null=True,
        help_text="User who submitted this investment"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_investments',
        help_text="User who created this investment"
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_investments',
        blank=True,
        null=True,
        help_text="User who last updated this investment"
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'investments'
        verbose_name = 'Investment'
        verbose_name_plural = 'Investments'
        ordering = ['-year', 'time_period']

    def __str__(self):
        return f"{self.year} - {self.time_period} - {self.entity_name}"
