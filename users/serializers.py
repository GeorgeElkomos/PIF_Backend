from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from authentication.models import User

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        request_user = self.context['request'].user
        validated_data['company'] = request_user.company  # inherit company
        validated_data['type'] = 'User'  # default type
        validated_data['password'] = make_password(validated_data['password'])  # hash password
        return super().create(validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=[('Admin', 'Admin'), ('User', 'User')], required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'type']

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']  # never return password
