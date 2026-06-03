from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import User


class UserSerializer(ModelSerializer):
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'foto', 'foto_url', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'groups']
        depth = 1
        
    def get_foto_url(self, obj):
        request = self.context.get('request')

        if obj.foto:
            if request:
                return request.build_absolute_uri(obj.foto.url)
            return obj.foto.url

        return None


class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'foto']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
