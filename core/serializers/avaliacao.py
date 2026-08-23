from rest_framework import serializers
from core.models import Avaliacao

class AvaliacaoSerializer(serializers.ModelSerializer):
    # id_usuario nunca vem do cliente — é sempre o usuário autenticado que
    # fez a requisição (ver AvaliacaoViewSet.perform_create), senão
    # qualquer um poderia postar uma avaliação em nome de outra pessoa.
    usuario_nome = serializers.CharField(source='id_usuario.name', read_only=True)

    class Meta:
        model = Avaliacao
        fields = ['id', 'nota', 'comentario', 'id_usuario', 'id_agencia', 'usuario_nome']
        read_only_fields = ['id_usuario']
