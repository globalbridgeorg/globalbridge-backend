from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Pais
from core.serializers import PaisSerializer

class PaisViewSet(ModelViewSet):
    queryset = Pais.objects.all()
    serializer_class = PaisSerializer

    @action(detail=False, methods=['get'], url_path='mais-procurados')
    def mais_procurados(self, request):
        quantidade = request.query_params.get('quantidade', 6)

        paises = Pais.objects.filter(ativo=True).order_by('-intercambistas')[:int(quantidade)]

        data = []
        for pais in paises:
            item = self.get_serializer(pais).data
            item['programas_disponiveis'] = item.get('programas_disponiveis') or max(40, pais.universidades // 2)
            data.append(item)

        return Response(data)