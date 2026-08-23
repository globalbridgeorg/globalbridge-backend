from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from core.models import Avaliacao
from core.serializers import AvaliacaoSerializer

class AvaliacaoViewSet(ModelViewSet):
    queryset = Avaliacao.objects.all()
    serializer_class = AvaliacaoSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        agencia_id = self.request.query_params.get('agencia')
        if agencia_id:
            queryset = queryset.filter(id_agencia_id=agencia_id)
        return queryset.order_by('-id')

    def perform_create(self, serializer):
        serializer.save(id_usuario=self.request.user)
