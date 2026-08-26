from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.models import SolicitacaoAgencia
from core.serializers import SolicitacaoAgenciaCreateSerializer, SolicitacaoAgenciaStatusSerializer


class SolicitacaoAgenciaViewSet(CreateModelMixin, RetrieveModelMixin, GenericViewSet):
    """Só criar (enviar pedido) e consultar status por id — sem listar
    (não é público ver o pedido de outra agência) e sem editar/apagar por
    aqui (aprovação/recusa é ação de time interno, feita no admin)."""

    queryset = SolicitacaoAgencia.objects.all()
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'create':
            return SolicitacaoAgenciaCreateSerializer
        return SolicitacaoAgenciaStatusSerializer

    def get_permissions(self):
        if self.action == 'minha':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='minha')
    def minha(self, request):
        """Status do próprio pedido de quem está logado — é assim que a
        pessoa acompanha depois de fechar a aba, sem depender de guardar
        um link. Só existe pra quem realmente veio desse fluxo (conta
        business criada manualmente, tipo as agências seed, não tem
        solicitação associada — nesses casos o front trata como já
        aprovado, porque a Agencia já existe)."""
        try:
            solicitacao = SolicitacaoAgencia.objects.get(usuario_criado=request.user)
        except SolicitacaoAgencia.DoesNotExist:
            raise NotFound('Nenhuma solicitação encontrada pra essa conta.')
        return Response(SolicitacaoAgenciaStatusSerializer(solicitacao).data)
