from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
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

    def _garantir_dono(self):
        # Sem isso, qualquer conta logada conseguia editar/apagar a
        # avaliação de OUTRA pessoa (reescrever nota e texto) — manipulação
        # de reputação. Só o autor da avaliação pode mexer nela.
        avaliacao = self.get_object()
        if avaliacao.id_usuario_id != self.request.user.id:
            raise PermissionDenied('Você só pode alterar as suas próprias avaliações.')

    def perform_update(self, serializer):
        self._garantir_dono()
        # id_usuario nunca muda por update — fica sempre o autor original.
        serializer.save(id_usuario=self.request.user)

    def perform_destroy(self, instance):
        if instance.id_usuario_id != self.request.user.id:
            raise PermissionDenied('Você só pode apagar as suas próprias avaliações.')
        instance.delete()
