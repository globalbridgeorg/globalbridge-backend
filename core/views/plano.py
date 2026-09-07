from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet
from core.models import Plano
from core.serializers import PlanoSerializer

class PlanoViewSet(ModelViewSet):
    queryset = Plano.objects.all()
    serializer_class = PlanoSerializer

    def get_permissions(self):
        # Ler é público; criar/editar/apagar é operação de admin. Antes
        # qualquer um mudava o preço de um plano sem login.
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]
