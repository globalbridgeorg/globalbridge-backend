from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import User


class UserSerializer(ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'foto', 'foto_url', 'avatar', 'avatar_url', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'groups']
        depth = 1

    def get_avatar_url(self, obj):
        return self._build_file_url(obj.avatar)

    def get_foto_url(self, obj):
        return self._build_file_url(obj.foto)

    def _build_file_url(self, file_field):
        if not file_field:
            return None

        file_value = getattr(file_field, 'name', file_field)
        if isinstance(file_value, str) and (file_value.startswith('http://') or file_value.startswith('https://')):
            return file_value

        if hasattr(file_field, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(file_field.url)
            return file_field.url

        return file_value


class PublicProfileSerializer(UserSerializer):
    """Perfil de OUTRO usuário, visto por quem está logado — só o que é
    seguro mostrar publicamente (nome e foto). Nunca email, permissões
    ou qualquer outro dado da conta."""

    class Meta:
        model = User
        fields = ['id', 'name', 'foto_url', 'avatar_url']


class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'foto']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
