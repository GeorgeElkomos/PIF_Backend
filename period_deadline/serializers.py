from rest_framework import serializers
from .models import PeriodDeadline
class PeriodDeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodDeadline
        fields = ['year', 'time_period', 'dead_line']
    