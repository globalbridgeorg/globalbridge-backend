from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Pais
from core.serializers import PaisSerializer, PaisDetalheSerializer

class PaisViewSet(ModelViewSet):
    queryset = Pais.objects.all()
    serializer_class = PaisSerializer
    # Lista de referência pequena (dezenas, não milhares) que várias telas
    # esperam receber inteira de uma vez — Destinos conta por região,
    # Região filtra e mostra todos os países dela, o globo do /mapview
    # cruza cada um com as agências. Com paginação (padrão de 10 por
    # página) essas contagens/telas silenciosamente cortavam o resto assim
    # que o catálogo passou de 10 países. Mesmo tratamento já dado à Tag.
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaisDetalheSerializer
        return PaisSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        regiao = self.request.query_params.get('regiao')
        if regiao:
            queryset = queryset.filter(regiao=regiao)
        return queryset

    @action(detail=False, methods=['get'], url_path='mais-procurados')
    def mais_procurados(self, request):
        quantidade = request.query_params.get('quantidade', 6)  # padrão 6 países

        paises = Pais.objects.filter(ativo=True).order_by('-intercambistas')[:int(quantidade)]

        serializer = self.get_serializer(paises, many=True)
        return Response(serializer.data)
