from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import User


class UserSerializer(ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'foto', 'foto_url', 'avatar', 'avatar_url', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'groups']
        depth = 1

    def get_avatar_url(self, obj):
        if not obj.avatar:
            return None

        avatar_value = getattr(obj.avatar, 'name', obj.avatar)
        if isinstance(avatar_value, str) and (avatar_value.startswith('http://') or avatar_value.startswith('https://')):
            return avatar_value

        if hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url

        return avatar_value


class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'foto']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
