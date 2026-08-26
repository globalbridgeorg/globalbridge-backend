from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Favorito
from core.serializers import FavoritoSerializer


class FavoritoViewSet(ModelViewSet):
    """Favoritos do usuário autenticado — sempre escopado a ele mesmo, nunca
    lista ou altera favorito de outra pessoa."""

    serializer_class = FavoritoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Favorito.objects.filter(id_usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(id_usuario=self.request.user)
