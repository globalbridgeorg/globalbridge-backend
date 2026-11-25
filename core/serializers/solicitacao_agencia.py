import logging

from django.db import transaction
from rest_framework import serializers

from core.emails import enviar_pedido_recebido
from core.models import SolicitacaoAgencia, User

logger = logging.getLogger(__name__)


class SolicitacaoAgenciaCreateSerializer(serializers.ModelSerializer):
    """Cria uma solicitação de conta business.

    Suporta dois fluxos:
    1. Usuário já autenticado (ex.: cadastro criado na etapa anterior do formulário):
       vincula a solicitação ao próprio usuário e marca `tipo = 'agencia'`.
    2. Usuário anônimo (ex.: envio direto via API/Swagger com campo `senha`):
       cria o `User(tipo='agencia')` e a `SolicitacaoAgencia` atomicamente.
    """

    senha = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=True)

    class Meta:
        model = SolicitacaoAgencia
        fields = [
            'id', 'nome', 'site', 'cidade', 'pais_sede', 'paises_atendidos', 'ano_fundacao',
            'nome_responsavel', 'cargo_responsavel', 'email_responsavel', 'senha',
            'documento', 'descricao',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        autenticado = bool(user and user.is_authenticated)

        if autenticado:
            if SolicitacaoAgencia.objects.filter(usuario_criado=user).exists():
                raise serializers.ValidationError({'detail': 'Você já possui uma solicitação de agência enviada.'})
            attrs['email_responsavel'] = (attrs.get('email_responsavel') or user.email).strip().lower()
        else:
            email = (attrs.get('email_responsavel') or '').strip().lower()
            attrs['email_responsavel'] = email
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({
                    'email_responsavel': 'Já existe uma conta com esse e-mail — faça login em vez de enviar um novo pedido.'
                })
            if not attrs.get('senha'):
                raise serializers.ValidationError({'senha': 'Informe uma senha com pelo menos 8 caracteres.'})

        return attrs

    def create(self, validated_data):
        senha = validated_data.pop('senha', None)
        paises_atendidos = validated_data.pop('paises_atendidos', [])
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        with transaction.atomic():
            if user and user.is_authenticated:
                usuario = user
                if usuario.tipo != 'agencia':
                    usuario.tipo = 'agencia'
                    usuario.save(update_fields=['tipo'])
            else:
                usuario = User.objects.create_user(
                    email=validated_data['email_responsavel'],
                    password=senha,
                    name=validated_data['nome_responsavel'],
                )
                usuario.tipo = 'agencia'
                usuario.save(update_fields=['tipo'])

            solicitacao = SolicitacaoAgencia.objects.create(usuario_criado=usuario, **validated_data)
            paises = list(paises_atendidos)
            if solicitacao.pais_sede not in paises:
                paises.append(solicitacao.pais_sede)
            solicitacao.paises_atendidos.set(paises)

        try:
            enviar_pedido_recebido(solicitacao)
        except Exception:
            logger.exception('Falha ao enviar e-mail de "pedido recebido" para %s', solicitacao.email_responsavel)

        return solicitacao


class SolicitacaoAgenciaStatusSerializer(serializers.ModelSerializer):
    """Consulta de status da solicitação — sem expor dados sensíveis."""

    agencia_criada_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = SolicitacaoAgencia
        fields = ['id', 'nome', 'status', 'motivo_recusa', 'criado_em', 'revisado_em', 'agencia_criada_id']
