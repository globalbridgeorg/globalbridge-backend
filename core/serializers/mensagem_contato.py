from rest_framework import serializers

from core.models import MensagemContato


class MensagemContatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MensagemContato
        fields = [
            'id', 'publico', 'nome', 'email', 'nome_agencia',
            'assunto', 'mensagem', 'lida', 'criado_em',
        ]
        read_only_fields = ['id', 'lida', 'criado_em']
