import logging

from django.db import transaction
from rest_framework import serializers

from core.emails import enviar_pedido_recebido
from core.models import SolicitacaoAgencia, User

logger = logging.getLogger(__name__)


class SolicitacaoAgenciaCreateSerializer(serializers.ModelSerializer):
    """Usado só na criação (POST) — aceita tudo que o formulário manda.

    Cria o User (tipo=agencia, sem Agencia vinculada ainda) NA HORA do
    pedido, não só quando aprova — assim quem pediu já sai com login
    próprio pra acompanhar o status depois, em vez de depender de um link
    salvo no navegador (que some se trocar de aparelho/limpar dados)."""

    senha = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = SolicitacaoAgencia
        fields = [
            'id', 'nome', 'site', 'cidade', 'pais_sede', 'paises_atendidos', 'ano_fundacao',
            'nome_responsavel', 'cargo_responsavel', 'email_responsavel', 'senha',
            'documento', 'descricao',
        ]
        read_only_fields = ['id']

    def validate_email_responsavel(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Já existe uma conta com esse e-mail — faça login em vez de enviar um novo pedido.')
        return value

    def create(self, validated_data):
        senha = validated_data.pop('senha')
        paises_atendidos = validated_data.pop('paises_atendidos', [])

        # Atômico: criar o User e falhar depois ao criar a SolicitacaoAgencia
        # (upload do documento, campo obrigatório faltando etc.) deixava o
        # usuário órfão salvo no banco sem pedido nenhum — quem tentasse de
        # novo esbarrava em "e-mail já cadastrado" sem ter nenhum pedido pra
        # mostrar. Com a transação, qualquer erro no meio desfaz tudo e a
        # pessoa consegue tentar de novo com o mesmo e-mail.
        with transaction.atomic():
            usuario = User.objects.create_user(
                email=validated_data['email_responsavel'],
                password=senha,
                name=validated_data['nome_responsavel'],
            )
            usuario.tipo = 'agencia'
            usuario.save(update_fields=['tipo'])

            solicitacao = SolicitacaoAgencia.objects.create(usuario_criado=usuario, **validated_data)
            solicitacao.paises_atendidos.set(paises_atendidos)

        try:
            enviar_pedido_recebido(solicitacao)
        except Exception:
            # Não deixa uma falha de e-mail (provedor fora, etc.) derrubar
            # o pedido em si — a pessoa já consegue ver o status logando.
            logger.exception('Falha ao enviar e-mail de "pedido recebido" para %s', solicitacao.email_responsavel)

        return solicitacao


class SolicitacaoAgenciaStatusSerializer(serializers.ModelSerializer):
    """Usado pra consultar status (GET) — só o que é seguro mostrar
    publicamente, sem exigir login (quem manda o pedido ainda não tem
    conta). Nada de e-mail/documento/dados sensíveis aqui."""

    class Meta:
        model = SolicitacaoAgencia
        fields = ['id', 'nome', 'status', 'motivo_recusa', 'criado_em', 'revisado_em']
