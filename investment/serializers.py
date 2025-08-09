from rest_framework import serializers
from .models import Investment

class InvestmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = [
            'year',
            'time_period',
            'asset_code',
            'entity_name',
            'arabic_legal_name',
            'commercial_registration_number',
            'moi_number',
            'country_of_incorporation',
            'ownership_percentage',
            'acquisition_disposal_date',
            'direct_parent',
            'ultimate_parent',
            'relationship_of_investment',
            'direct_or_indirect',
            'entities_principal_activities',
        ]
from rest_framework import serializers
from .models import Investment, PeriodDeadline

class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = [
            'id',  # include id for update/delete references
            'year',
            'time_period',
            'asset_code',
            'entity_name',
            'arabic_legal_name',
            'commercial_registration_number',
            'moi_number',
            'country_of_incorporation',
            'ownership_percentage',
            'acquisition_disposal_date',
            'direct_parent',
            'ultimate_parent',
            'relationship_of_investment',
            'direct_or_indirect',
            'entities_principal_activities',
            'is_submitted',
            'submitted_at',
            'submitted_by',
            'created_by',
            'created_at',
            'updated_by',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'submitted_at', 'submitted_by', 'created_by', 'created_at', 'updated_by', 'updated_at'
        ]

    def validate_relationship_of_investment(self, value):
        if value and value not in dict(Investment.RELATIONSHIP_CHOICES):
            raise serializers.ValidationError("Invalid relationship_of_investment choice.")
        return value

    def validate_direct_or_indirect(self, value):
        if value and value not in dict(Investment.DIRECT_CHOICES):
            raise serializers.ValidationError("Invalid direct_or_indirect choice.")
        return value
    def validate_time_period(self, value):
        if value and value not in dict(PeriodDeadline.TIME_PERIOD_CHOICES):
            raise serializers.ValidationError("Invalid time_period choice.")
        return value
    
    
class ReportRowSerializer(serializers.ModelSerializer):
    assetCode = serializers.CharField(source='asset_code', allow_null=True)
    entityNameEnglish = serializers.CharField(source='entity_name')
    entityNameArabic = serializers.CharField(source='arabic_legal_name', allow_null=True)
    commercialRegistrationNumber = serializers.CharField(source='commercial_registration_number', allow_null=True)
    moiNumber = serializers.CharField(source='moi_number', allow_null=True)
    countryOfIncorporation = serializers.CharField(source='country_of_incorporation', allow_null=True)
    acquisitionDisposalDate = serializers.DateField(source='acquisition_disposal_date', format='%Y-%m-%d', allow_null=True)
    directParentEntity = serializers.CharField(source='direct_parent', allow_null=True)
    ultimateParentEntity = serializers.CharField(source='ultimate_parent', allow_null=True)
    investmentRelationshipType = serializers.CharField(source='relationship_of_investment', allow_null=True)
    ownershipStructure = serializers.CharField(source='direct_or_indirect', allow_null=True)
    principalActivities = serializers.CharField(source='entities_principal_activities', allow_null=True)
    currency = serializers.SerializerMethodField()
    ownershipPercentage = serializers.DecimalField(source='ownership_percentage', max_digits=7, decimal_places=2)

    class Meta:
        model = Investment
        fields = [
            'assetCode',
            'entityNameEnglish',
            'entityNameArabic',
            'commercialRegistrationNumber',
            'moiNumber',
            'countryOfIncorporation',
            'acquisitionDisposalDate',
            'directParentEntity',
            'ultimateParentEntity',
            'investmentRelationshipType',
            'ownershipStructure',
            'principalActivities',
            'currency',
            'ownershipPercentage',
        ]

    def get_currency(self, obj):
        # placeholder — return empty unless you add a currency field
        return ""
