from rest_framework import serializers

from Investments.models import Investment
from authentication.models import Company
# investments/serializers.py

from rest_framework import serializers

class InvestmentStructuredReadSerializer(serializers.ModelSerializer):
    ID = serializers.IntegerField(source='id')
    Asset_code = serializers.CharField(source='asset_code')
    Entity_Name = serializers.CharField(source='entity.name')
    Arabic_entity_name = serializers.CharField(source='entity.arabic_name')
    CR_number = serializers.CharField(source='entity.cr_number')
    MOI_number = serializers.CharField(source='entity.moi_number')
    country_of_incorporation = serializers.CharField(source='entity.country_of_incorporation')
    Ownership_Persentage = serializers.DecimalField(source='ownership', max_digits=5, decimal_places=2)
    aquization_date = serializers.DateField(source='aquization_date')
    direct_parent_name = serializers.CharField(source='direct_parent.name')
    Ultimate_parent = serializers.CharField(source='Ultimate_parent')
    RelationShip_of_investment = serializers.CharField(source='RelationShip_of_investment')
    direct = serializers.BooleanField()
    Entity_Principal_activities = serializers.CharField(source='Entity_Principal_activities')

    class Meta:
        model = Investment
        fields = [
            'ID', 'Asset_code', 'Entity_Name', 'Arabic_entity_name', 'CR_number', 'MOI_number',
            'country_of_incorporation', 'Ownership_Persentage', 'aquization_date', 'direct_parent_name',
            'Ultimate_parent', 'RelationShip_of_investment', 'direct', 'Entity_Principal_activities'
        ]

# investments/serializers.py

from rest_framework import serializers
from authentication.models import Company

class InvestmentStructuredWriteSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    period = serializers.CharField()
    Asset_code = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    
    Entity_Name = serializers.CharField()
    Arabic_entity_name = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    CR_number = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    MOI_number = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    country_of_incorporation = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    
    Ownership_Persentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    aquization_date = serializers.DateField(allow_null=True, required=False)
    
    direct_parent_name = serializers.CharField()
    Ultimate_parent = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    RelationShip_of_investment = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    direct = serializers.BooleanField(default=False)
    Entity_Principal_activities = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    # Custom company validation
    def validate_Entity_Name(self, value):
        if isinstance(value, str):
            try:
                company = Company.objects.get(name=value)
            except Company.DoesNotExist:
                raise serializers.ValidationError("Company with this name does not exist.")
        elif isinstance(value, Company):
            company = value
        else:
            raise serializers.ValidationError("Invalid value for company.")
        
        if not company.is_active:
            raise serializers.ValidationError("Cannot assign an inactive company.")

        # Store for later use
        self._validated_entity = company
        return value

    def validate_direct_parent_name(self, value):
        if isinstance(value, str):
            try:
                company = Company.objects.get(name=value)
            except Company.DoesNotExist:
                raise serializers.ValidationError("Direct parent company does not exist.")
        elif isinstance(value, Company):
            company = value
        else:
            raise serializers.ValidationError("Invalid value for direct parent company.")

        if not company.is_active:
            raise serializers.ValidationError("Cannot assign an inactive direct parent company.")

        self._validated_direct_parent = company
        return value

    def validate(self, data):
        # Attach resolved Company instances for use in the view
        data['entity_obj'] = getattr(self, '_validated_entity', None)
        data['direct_parent_obj'] = getattr(self, '_validated_direct_parent', None)
        return data

