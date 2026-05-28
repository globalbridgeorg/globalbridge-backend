from rest_framework.viewsets import ModelViewSet
from core.models import Agencia
from core.serializers import AgenciaSerializer

class AgenciaViewSet(ModelViewSet):
    queryset = Agencia.objects.all()
    serializer_class = AgenciaSerializer