from rest_framework.viewsets import ModelViewSet
from core.models import Agencia
from core.serializers import AgenciaSerializer, AgenciaDetalheSerializer, AgenciaResumidaSerializer

class AgenciaViewSet(ModelViewSet):
    queryset = Agencia.objects.all()
    serializer_class = AgenciaSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AgenciaDetalheSerializer
        if self.action == 'list':
            return AgenciaResumidaSerializer
        return AgenciaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        pais_id = self.request.query_params.get('pais')
        regiao = self.request.query_params.get('regiao')
        if pais_id:
            queryset = queryset.filter(id_estado__id_pais_id=pais_id)
        if regiao:
            queryset = queryset.filter(id_estado__id_pais__regiao=regiao)
        return queryset
