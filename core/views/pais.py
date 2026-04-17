from rest_framework.viewsets import ModelViewSet
from core.models import Pais
from core.serializers import PaisSerializer

class PaisViewSet(ModelViewSet):
    queryset = Pais.objects.all()
    serializer_class = PaisSerializer