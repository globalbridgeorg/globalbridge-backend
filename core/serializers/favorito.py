from rest_framework import serializers

from core.models import Agencia, Favorito, Pais


class FavoritoSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()
    subtitulo = serializers.SerializerMethodField()

    class Meta:
        model = Favorito
        fields = ['id', 'tipo', 'objeto_id', 'nome', 'subtitulo', 'criado_em']
        read_only_fields = ['id', 'criado_em']

    def get_nome(self, obj):
        objeto = self._resolver_objeto(obj)
        return getattr(objeto, 'nome', None)

    def get_subtitulo(self, obj):
        objeto = self._resolver_objeto(obj)
        if objeto is None:
            return None
        if obj.tipo == 'pais':
            return objeto.idioma
        cidade = objeto.id_estado.cidade_principal if objeto.id_estado else None
        pais = objeto.id_estado.id_pais.nome if objeto.id_estado else None
        return f'{cidade}, {pais}' if cidade and pais else None

    def _resolver_objeto(self, obj):
        modelo = Pais if obj.tipo == 'pais' else Agencia
        return modelo.objects.filter(id=obj.objeto_id).first()

    def validate(self, attrs):
        tipo = attrs.get('tipo')
        objeto_id = attrs.get('objeto_id')
        modelo = Pais if tipo == 'pais' else Agencia
        if not modelo.objects.filter(id=objeto_id).exists():
            raise serializers.ValidationError(f'{tipo} com id {objeto_id} não existe.')
        return attrs
