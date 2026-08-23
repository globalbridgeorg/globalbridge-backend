from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Pais
from core.serializers import PaisSerializer, PaisDetalheSerializer

class PaisViewSet(ModelViewSet):
    queryset = Pais.objects.all()
    serializer_class = PaisSerializer

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
