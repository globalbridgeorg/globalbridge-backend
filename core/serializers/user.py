from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import User


class UserSerializer(ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'avatar', 'avatar_url', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'groups']
        depth = 1

    def get_avatar_url(self, obj):
        if not obj.avatar:
            return None
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url


class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
