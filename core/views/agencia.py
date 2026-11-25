from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Agencia, ImagemGaleria, Pais, SolicitacaoPaisAdicional
from core.serializers import AgenciaSerializer, AgenciaDetalheSerializer, AgenciaResumidaSerializer
from core.storage import url_para_campo_arquivo

from .agencia_painel import montar_painel


class AgenciaViewSet(ModelViewSet):
    queryset = Agencia.objects.all()
    serializer_class = AgenciaSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AgenciaDetalheSerializer
        if self.action == 'list':
            return AgenciaResumidaSerializer
        return AgenciaSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.usuario_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Você só pode editar a página da sua própria agência.')
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        detalhe = AgenciaDetalheSerializer(instance, context={'request': request})
        return Response(detalhe.data)

    def perform_create(self, serializer):
        raise PermissionDenied('Conta de agência só é criada depois da verificação pelo time da GlobalBridge.')

    def perform_destroy(self, instance):
        raise PermissionDenied('Não é possível excluir uma agência por aqui.')

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.filter(ativo=True)
        pais_id = self.request.query_params.get('pais')
        regiao = self.request.query_params.get('regiao')
        if pais_id:
            queryset = queryset.filter(paises_atendidos__id=pais_id)
        if regiao:
            queryset = queryset.filter(paises_atendidos__regiao=regiao)
        return queryset.distinct().order_by('id')

    @action(
        detail=True, methods=['patch'], url_path='capa',
        permission_classes=[IsAuthenticated], parser_classes=[MultiPartParser, FormParser],
    )
    def capa(self, request, pk=None):
        """Sobe a imagem de capa da agência (editor da conta business) — só
        o dono da agência pode trocar."""
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Você só pode editar a página da sua própria agência.')

        arquivo = request.FILES.get('imagem_capa')
        if not arquivo:
            return Response({'detail': 'Envie uma imagem no campo imagem_capa.'}, status=400)

        agencia.imagem_capa.save(arquivo.name, arquivo, save=True)
        serializer = AgenciaDetalheSerializer(agencia, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=True, methods=['post'], url_path='galeria',
        permission_classes=[IsAuthenticated], parser_classes=[MultiPartParser, FormParser],
    )
    def galeria_upload(self, request, pk=None):
        """Adiciona uma foto na galeria — cada chamada sobe uma imagem."""
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Você só pode editar a página da sua própria agência.')

        arquivo = request.FILES.get('imagem')
        if not arquivo:
            return Response({'detail': 'Envie uma imagem no campo imagem.'}, status=400)

        ordem_param = request.data.get('ordem')
        try:
            ordem = int(ordem_param) if ordem_param is not None else agencia.galeria.count()
        except (TypeError, ValueError):
            ordem = agencia.galeria.count()

        img = ImagemGaleria.objects.create(agencia=agencia, ordem=ordem)
        img.imagem.save(arquivo.name, arquivo, save=True)

        url = url_para_campo_arquivo(img.imagem, request)
        return Response({'id': img.id, 'agencia_id': agencia.id, 'url': url, 'ordem': img.ordem}, status=201)

    @action(detail=True, methods=['delete'], url_path=r'galeria/(?P<imagem_id>\d+)', permission_classes=[IsAuthenticated])
    def galeria_remover(self, request, pk=None, imagem_id=None):
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Você só pode editar a página da sua própria agência.')

        try:
            img = agencia.galeria.get(id=imagem_id)
        except ImagemGaleria.DoesNotExist:
            return Response({'detail': 'Imagem não encontrada.'}, status=404)

        if img.imagem:
            try:
                img.imagem.delete(save=False)
            except Exception:
                pass
        img.delete()
        return Response(status=204)

    @action(detail=True, methods=['get'], url_path='painel', permission_classes=[IsAuthenticated])
    def painel(self, request, pk=None):
        """Dados agregados do dashboard da conta business (ver agencia_painel.montar_painel)."""
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Você só pode ver o painel da sua própria agência.')
        return Response(montar_painel(agencia))

    @action(detail=True, methods=['post'], url_path='paises/solicitar', permission_classes=[IsAuthenticated])
    def solicitar_pais(self, request, pk=None):
        """A agência pede pra passar a atender mais um país — fica
        pendente até o time aprovar."""
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Você só pode pedir países pra sua própria agência.')

        pais_id = request.data.get('pais')
        if not pais_id:
            return Response({'detail': 'Informe o país (campo "pais").'}, status=400)

        try:
            pais = Pais.objects.get(pk=pais_id)
        except Pais.DoesNotExist:
            return Response({'detail': 'País não encontrado.'}, status=404)

        if agencia.paises_atendidos.filter(id=pais.id).exists():
            return Response({'detail': 'Sua agência já atende esse país.'}, status=400)

        if SolicitacaoPaisAdicional.objects.filter(agencia=agencia, pais=pais, status='pendente').exists():
            return Response({'detail': 'Já existe um pedido pendente pra esse país.'}, status=400)

        solicitacao = SolicitacaoPaisAdicional.objects.create(agencia=agencia, pais=pais)
        return Response({'id': solicitacao.id, 'pais': pais.nome, 'status': solicitacao.status}, status=201)
