from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet
from core.models import Programa
from core.serializers import ProgramaSerializer

class ProgramaViewSet(ModelViewSet):
    queryset = Programa.objects.all()
    serializer_class = ProgramaSerializer

    def get_permissions(self):
        # Catálogo compartilhado entre agências — ler é público, mas
        # criar/editar/apagar é operação de time interno (admin). Antes não
        # tinha permissão nenhuma e qualquer um alterava sem login.
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]
