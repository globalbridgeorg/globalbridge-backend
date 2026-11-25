from rest_framework import serializers
from django.db.models import Avg

from core.models import Pais, Estado, Agencia, Programa
from core.storage import url_para_campo_arquivo
from .tag import TagSerializer


class PaisSerializer(serializers.ModelSerializer):
    agencias_count = serializers.SerializerMethodField()
    agencia_destaque = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Pais
        fields = '__all__'

    def get_agencias_count(self, obj):
        return Agencia.objects.filter(paises_atendidos=obj, ativo=True).distinct().count()

    def get_agencia_destaque(self, obj):
        agencias = Agencia.objects.filter(paises_atendidos=obj, ativo=True).annotate(
            nota_calc=Avg('avaliacao__nota')
        ).order_by('-nota_calc', 'id')
        agencia = agencias.first()
        if not agencia:
            return None
        return AgenciaResumidaSerializer(agencia, context=self.context).data


class CidadeResumidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = ['id', 'nome', 'cidade_principal']


class AgenciaResumidaSerializer(serializers.ModelSerializer):
    cidade = serializers.SerializerMethodField()
    pais = serializers.SerializerMethodField()
    pais_nome_ingles = serializers.SerializerMethodField()
    nota_media = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    imagem_capa_url = serializers.SerializerMethodField()

    class Meta:
        model = Agencia
        fields = [
            'id', 'nome', 'descricao', 'cidade', 'pais', 'pais_nome_ingles',
            'nota_media', 'tags', 'imagem_capa_url', 'imagem_capa_foco_x', 'imagem_capa_foco_y',
        ]

    def get_imagem_capa_url(self, obj):
        return url_para_campo_arquivo(obj.imagem_capa, self.context.get('request'))

    def get_cidade(self, obj):
        pais_contexto = self.context.get('pais_contexto')
        if pais_contexto and (not obj.id_estado or obj.id_estado.id_pais_id != pais_contexto.id):
            return None
        return obj.id_estado.cidade_principal if obj.id_estado else None

    def get_pais(self, obj):
        pais_contexto = self.context.get('pais_contexto')
        if pais_contexto:
            return pais_contexto.nome
        return obj.id_estado.id_pais.nome if obj.id_estado else None

    def get_pais_nome_ingles(self, obj):
        pais_contexto = self.context.get('pais_contexto')
        if pais_contexto:
            return pais_contexto.nome_ingles
        return obj.id_estado.id_pais.nome_ingles if obj.id_estado else None

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
        agencias = Agencia.objects.filter(paises_atendidos=obj, ativo=True).distinct()
        ctx = {**self.context, 'pais_contexto': obj}
        return AgenciaResumidaSerializer(agencias, many=True, context=ctx).data

    def get_programas(self, obj):
        programas = Programa.objects.filter(
            plano__id_agencia__paises_atendidos=obj
        ).distinct()
        return ProgramaCatalogoSerializer(programas, many=True).data
