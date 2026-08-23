from django.db.models import Avg

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import Agencia, User


class UserSerializer(ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'foto', 'foto_url', 'avatar', 'avatar_url', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'groups']
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
    seguro mostrar publicamente. Nunca email, permissões ou qualquer
    outro dado da conta. O conteúdo muda pelo tipo: estudante mostra as
    avaliações que escreveu, agência mostra um resumo da agência vinculada."""

    agencia = serializers.SerializerMethodField()
    avaliacoes = serializers.SerializerMethodField()
    total_avaliacoes = serializers.SerializerMethodField()
    nota_media_dada = serializers.SerializerMethodField()
    agencias_avaliadas = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'foto_url', 'avatar_url', 'tipo',
            'agencia', 'avaliacoes', 'total_avaliacoes', 'nota_media_dada', 'agencias_avaliadas',
        ]

    def get_agencia(self, obj):
        try:
            agencia = obj.agencia
        except Agencia.DoesNotExist:
            return None
        media = agencia.avaliacao_set.aggregate(media=Avg('nota'))['media']
        return {
            'id': agencia.id,
            'nome': agencia.nome,
            'descricao': agencia.descricao,
            'cidade': agencia.id_estado.cidade_principal if agencia.id_estado else None,
            'pais': agencia.id_estado.id_pais.nome if agencia.id_estado else None,
            'nota_media': round(media, 1) if media is not None else None,
            'total_avaliacoes': agencia.avaliacao_set.count(),
            'total_programas': agencia.plano_set.count(),
        }

    def get_avaliacoes(self, obj):
        if obj.tipo != 'estudante':
            return []
        avaliacoes = obj.avaliacao_set.select_related('id_agencia', 'id_agencia__id_estado__id_pais').order_by('-id')[:20]
        return [
            {
                'id': a.id,
                'nota': a.nota,
                'comentario': a.comentario,
                'agencia_id': a.id_agencia.id,
                'agencia_nome': a.id_agencia.nome,
                'agencia_cidade': a.id_agencia.id_estado.cidade_principal if a.id_agencia.id_estado else None,
                'agencia_pais': a.id_agencia.id_estado.id_pais.nome if a.id_agencia.id_estado else None,
            }
            for a in avaliacoes
        ]

    def get_total_avaliacoes(self, obj):
        return obj.avaliacao_set.count()

    def get_nota_media_dada(self, obj):
        media = obj.avaliacao_set.aggregate(media=Avg('nota'))['media']
        return round(media, 1) if media is not None else None

    def get_agencias_avaliadas(self, obj):
        return obj.avaliacao_set.values('id_agencia').distinct().count()


class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'foto']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
