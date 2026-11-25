from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Plano
from core.serializers import PlanoSerializer


class PlanoViewSet(ModelViewSet):
    queryset = Plano.objects.select_related('id_agencia', 'id_programa').all().order_by('id')
    serializer_class = PlanoSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def _garantir_dono_ou_admin(self, agencia):
        user = self.request.user
        if user.is_staff:
            return
        if not agencia or agencia.usuario_id != user.id:
            raise PermissionDenied('Você só pode gerenciar planos da sua própria agência.')

    def perform_create(self, serializer):
        agencia = serializer.validated_data.get('id_agencia')
        self._garantir_dono_ou_admin(agencia)
        serializer.save()

    def perform_update(self, serializer):
        plano = self.get_object()
        self._garantir_dono_ou_admin(plano.id_agencia)
        # Impede transferir o plano para outra agência via PATCH
        serializer.save(id_agencia=plano.id_agencia)

    def perform_destroy(self, instance):
        self._garantir_dono_ou_admin(instance.id_agencia)
        instance.delete()
