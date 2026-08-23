from rest_framework import serializers
from django.db.models import Avg

from core.models import Pais, Estado, Agencia, Programa
from .tag import TagSerializer


class PaisSerializer(serializers.ModelSerializer):
    programas_count = serializers.SerializerMethodField()
    agencia_destaque = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Pais
        fields = '__all__'

    def get_programas_count(self, obj):
        return Programa.objects.filter(
            plano__id_agencia__id_estado__id_pais=obj
        ).distinct().count()

    def get_agencia_destaque(self, obj):
        agencias = Agencia.objects.filter(id_estado__id_pais=obj, ativo=True).annotate(
            nota_calc=Avg('avaliacao__nota')
        ).order_by('-nota_calc', 'id')
        agencia = agencias.first()
        if not agencia:
            return None
        return AgenciaResumidaSerializer(agencia).data


class CidadeResumidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = ['id', 'nome', 'cidade_principal']


class AgenciaResumidaSerializer(serializers.ModelSerializer):
    cidade = serializers.SerializerMethodField()
    nota_media = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Agencia
        fields = ['id', 'nome', 'descricao', 'cidade', 'nota_media', 'tags']

    def get_cidade(self, obj):
        return obj.id_estado.cidade_principal if obj.id_estado else None

    def get_nota_media(self, obj):
        media = obj.avaliacao_set.aggregate(media=Avg('nota'))['media']
        return round(media, 1) if media is not None else None


class ProgramaCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programa
        fields = ['id', 'nome', 'descricao', 'duracao_min', 'duracao_max']


class PaisDetalheSerializer(serializers.ModelSerializer):
    """Serializer da página de país: além dos campos do país, traz as
    cidades, agências parceiras e programas oferecidos por elas — tudo o
    que a página de destino precisa numa única chamada."""

    cidades = CidadeResumidaSerializer(source='estado_set', many=True, read_only=True)
    agencias = serializers.SerializerMethodField()
    programas = serializers.SerializerMethodField()

    class Meta:
        model = Pais
        fields = [
            'id', 'nome', 'codigo_iso', 'regiao', 'custo_de_vida', 'idioma',
            'cultura', 'descricao', 'imagem_url', 'intercambistas', 'universidades',
            'ativo', 'cidades', 'agencias', 'programas',
        ]

    def get_agencias(self, obj):
        agencias = Agencia.objects.filter(id_estado__id_pais=obj, ativo=True)
        return AgenciaResumidaSerializer(agencias, many=True).data

    def get_programas(self, obj):
        programas = Programa.objects.filter(
            plano__id_agencia__id_estado__id_pais=obj
        ).distinct()
        return ProgramaCatalogoSerializer(programas, many=True).data
