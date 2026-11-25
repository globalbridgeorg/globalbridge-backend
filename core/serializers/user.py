import logging

from django.conf import settings
from django.db.models import Avg
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.emails import enviar_boas_vindas
from core.models import Agencia, CodigoVerificacaoEmail, User
from core.storage import url_para_campo_arquivo

logger = logging.getLogger(__name__)


class UserSerializer(ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    foto_url = serializers.SerializerMethodField()
    agencia_id = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'name', 'tipo', 'agencia_id', 'is_admin',
            'foto', 'foto_url', 'avatar', 'avatar_url', 'is_active', 'is_staff',
            'is_superuser', 'last_login', 'groups',
        ]
        # CRÍTICO: campos de permissão são estritamente somente leitura para
        # impedir escalada de privilégio via PATCH /usuarios/<id>/.
        read_only_fields = [
            'username', 'email', 'tipo', 'is_active', 'is_staff',
            'is_superuser', 'last_login', 'groups',
        ]
        depth = 1

    def get_agencia_id(self, obj):
        agencia = getattr(obj, 'agencia', None)
        return agencia.id if agencia else None

    def get_is_admin(self, obj):
        return bool(obj.is_staff or obj.is_superuser)

    def get_avatar_url(self, obj):
        return url_para_campo_arquivo(obj.avatar or obj.foto, self.context.get('request'))

    def get_foto_url(self, obj):
        return url_para_campo_arquivo(obj.foto or obj.avatar, self.context.get('request'))


class PublicProfileSerializer(UserSerializer):
    """Perfil de OUTRO usuário — só o que é seguro mostrar publicamente.
    Nunca expõe email, permissões ou dados sensíveis."""

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
            'imagem_capa_url': url_para_campo_arquivo(agencia.imagem_capa, self.context.get('request')),
            'imagem_capa_foco_x': agencia.imagem_capa_foco_x,
            'imagem_capa_foco_y': agencia.imagem_capa_foco_y,
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

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Este e-mail já está em uso.')
        if getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', False):
            if not CodigoVerificacaoEmail.email_verificado_recentemente(email):
                raise serializers.ValidationError('Confirme seu e-mail antes de criar a conta.')
        return email

    def create(self, validated_data):
        usuario = User.objects.create_user(**validated_data)
        try:
            enviar_boas_vindas(usuario)
        except Exception:
            logger.exception('Falha ao enviar e-mail de boas-vindas para %s', usuario.email)
        return usuario
