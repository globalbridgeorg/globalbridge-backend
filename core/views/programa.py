from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from core.models import Programa
from core.serializers import ProgramaSerializer


class ProgramaViewSet(ModelViewSet):
    queryset = Programa.objects.all().order_by('nome')
    serializer_class = ProgramaSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]
