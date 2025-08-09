from rest_framework import serializers
from authentication.models import Company

class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"
        read_only_fields = ("parent_company", "created_at", "updated_at")


class EntityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "name",
            "arabic_name",
            "cr_number",
            "moi_number",
            "country_of_incorporation",
            "is_active"
        ]


class EntityUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "name",
            "arabic_name",
            "cr_number",
            "moi_number",
            "country_of_incorporation",
            "is_active"
        ]
