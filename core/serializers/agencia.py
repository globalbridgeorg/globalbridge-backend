from rest_framework import serializers
from django.db.models import Avg

from core.models import Agencia, Plano
from core.storage import url_para_campo_arquivo


class AgenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agencia
        fields = '__all__'
        read_only_fields = ['id', 'usuario', 'ativo', 'data_cadastro']


class PlanoCatalogoSerializer(serializers.ModelSerializer):
    programa_id = serializers.IntegerField(source='id_programa_id', read_only=True)
    programa_nome = serializers.CharField(source='id_programa.nome')
    duracao_min = serializers.IntegerField(source='id_programa.duracao_min')
    duracao_max = serializers.IntegerField(source='id_programa.duracao_max')

    class Meta:
        model = Plano
        fields = ['id', 'programa_id', 'programa_nome', 'duracao_min', 'duracao_max', 'preco', 'descricao', 'inclui']


class AvaliacaoResumidaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nota = serializers.IntegerField()
    comentario = serializers.CharField()
    autor = serializers.CharField(source='id_usuario.name')
    autor_id = serializers.IntegerField(source='id_usuario.id')
    autor_username = serializers.CharField(source='id_usuario.username')
    autor_foto = serializers.SerializerMethodField()

    def get_autor_foto(self, obj):
        usuario = obj.id_usuario
        return url_para_campo_arquivo(usuario.avatar or usuario.foto, self.context.get('request'))


class AgenciaDetalheSerializer(serializers.ModelSerializer):
    """Serializer da página de agência: identidade + cidade/país, planos
    (catálogo de programas oferecidos) e avaliações mais recentes."""

    cidade = serializers.SerializerMethodField()
    pais = serializers.SerializerMethodField()
    pais_id = serializers.SerializerMethodField()
    regiao = serializers.SerializerMethodField()
    outros_paises = serializers.SerializerMethodField()
    nota_media = serializers.SerializerMethodField()
    total_avaliacoes = serializers.SerializerMethodField()
    planos = serializers.SerializerMethodField()
    avaliacoes = serializers.SerializerMethodField()
    imagem_capa_url = serializers.SerializerMethodField()
    galeria = serializers.SerializerMethodField()

    class Meta:
        model = Agencia
        fields = [
            'id', 'nome', 'descricao', 'como_funciona', 'contato', 'telefone', 'site', 'endereco',
            'ativo', 'cidade', 'pais', 'pais_id', 'regiao', 'outros_paises',
            'nota_media', 'total_avaliacoes', 'planos', 'avaliacoes', 'layout', 'imagem_capa_url',
            'imagem_capa_foco_x', 'imagem_capa_foco_y', 'conteudo_blocos', 'galeria',
        ]

    def get_galeria(self, obj):
        request = self.context.get('request')
        imagens = []
        for img in obj.galeria.all():
            url = url_para_campo_arquivo(img.imagem, request)
            imagens.append({'id': img.id, 'agencia_id': obj.id, 'url': url, 'ordem': img.ordem})
        return imagens

    def get_imagem_capa_url(self, obj):
        return url_para_campo_arquivo(obj.imagem_capa, self.context.get('request'))

    def get_cidade(self, obj):
        return obj.id_estado.cidade_principal if obj.id_estado else None

    def get_pais(self, obj):
        return obj.id_estado.id_pais.nome if obj.id_estado else None

    def get_pais_id(self, obj):
        return obj.id_estado.id_pais.id if obj.id_estado else None

    def get_regiao(self, obj):
        return obj.id_estado.id_pais.regiao if obj.id_estado else None

    def get_outros_paises(self, obj):
        sede_id = obj.id_estado.id_pais_id if obj.id_estado else None
        return list(
            obj.paises_atendidos.exclude(id=sede_id).values_list('nome', flat=True).order_by('nome')
        )

    def get_nota_media(self, obj):
        media = obj.avaliacao_set.aggregate(media=Avg('nota'))['media']
        return round(media, 1) if media is not None else None

    def get_total_avaliacoes(self, obj):
        return obj.avaliacao_set.count()

    def get_planos(self, obj):
        planos = Plano.objects.filter(id_agencia=obj).select_related('id_programa').order_by('id')
        return PlanoCatalogoSerializer(planos, many=True).data

    def get_avaliacoes(self, obj):
        avaliacoes = obj.avaliacao_set.select_related('id_usuario').order_by('-id')[:20]
        return AvaliacaoResumidaSerializer(avaliacoes, many=True, context=self.context).data
