from rest_framework import serializers
from django.db.models import Avg

from core.models import Agencia, Plano


class AgenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agencia
        fields = '__all__'


class PlanoCatalogoSerializer(serializers.ModelSerializer):
    programa_nome = serializers.CharField(source='id_programa.nome')
    duracao_min = serializers.IntegerField(source='id_programa.duracao_min')
    duracao_max = serializers.IntegerField(source='id_programa.duracao_max')

    class Meta:
        model = Plano
        fields = ['id', 'programa_nome', 'duracao_min', 'duracao_max', 'preco', 'descricao', 'inclui']


class AvaliacaoResumidaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nota = serializers.IntegerField()
    comentario = serializers.CharField()
    autor = serializers.CharField(source='id_usuario.name')


class AgenciaDetalheSerializer(serializers.ModelSerializer):
    """Serializer da página de agência: identidade + cidade/país, planos
    (catálogo de programas oferecidos) e avaliações mais recentes."""

    cidade = serializers.SerializerMethodField()
    pais = serializers.SerializerMethodField()
    nota_media = serializers.SerializerMethodField()
    total_avaliacoes = serializers.SerializerMethodField()
    planos = serializers.SerializerMethodField()
    avaliacoes = serializers.SerializerMethodField()

    class Meta:
        model = Agencia
        fields = [
            'id', 'nome', 'descricao', 'contato', 'telefone', 'site', 'endereco',
            'ativo', 'cidade', 'pais', 'nota_media', 'total_avaliacoes', 'planos', 'avaliacoes',
        ]

    def get_cidade(self, obj):
        return obj.id_estado.cidade_principal if obj.id_estado else None

    def get_pais(self, obj):
        return obj.id_estado.id_pais.nome if obj.id_estado else None

    def get_nota_media(self, obj):
        media = obj.avaliacao_set.aggregate(media=Avg('nota'))['media']
        return round(media, 1) if media is not None else None

    def get_total_avaliacoes(self, obj):
        return obj.avaliacao_set.count()

    def get_planos(self, obj):
        planos = Plano.objects.filter(id_agencia=obj).select_related('id_programa')
        return PlanoCatalogoSerializer(planos, many=True).data

    def get_avaliacoes(self, obj):
        avaliacoes = obj.avaliacao_set.select_related('id_usuario').order_by('-id')[:10]
        return AvaliacaoResumidaSerializer(avaliacoes, many=True).data
