from rest_framework.viewsets import ModelViewSet
from core.models import Plano
from core.serializers import PlanoSerializer

class PlanoViewSet(ModelViewSet):
    queryset = Plano.objects.all()
    serializer_class = PlanoSerializer