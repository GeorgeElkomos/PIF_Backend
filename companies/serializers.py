from rest_framework import serializers
from authentication.models import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'name',
            'arabic_name',
            'cr_number',
            'moi_number',
            'country_of_incorporation',
            'is_active'
        ]
