from django.db import models
from django.utils import timezone

class PeriodDeadline(models.Model):
    year = models.PositiveIntegerField()
    TIME_PERIOD_CHOICES = [
        ('First Half', 'First Half'),
        ('Third Quarter', 'Third Quarter'),
        ('Fourth Quarter', 'Fourth Quarter'),  # fixed typo
    ]
    time_period = models.CharField(max_length=20, choices=TIME_PERIOD_CHOICES)
    dead_line = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('year', 'time_period')

    def __str__(self):
        return f"{self.year} - {self.get_time_period_display()} - {self.dead_line.strftime('%Y-%m-%d %H:%M:%S')}"
