from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Avaliacao
from core.serializers import AvaliacaoSerializer
from core.storage import url_para_campo_arquivo


class AvaliacaoViewSet(ModelViewSet):
    queryset = Avaliacao.objects.all()
    serializer_class = AvaliacaoSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'depoimentos'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        agencia_id = self.request.query_params.get('agencia')
        if agencia_id:
            queryset = queryset.filter(id_agencia_id=agencia_id)
        return queryset.order_by('-id')

    @action(detail=False, methods=['get'], url_path='depoimentos', permission_classes=[AllowAny])
    def depoimentos(self, request):
        """Retorna depoimentos reais de estudantes para a seção 'Quem já foi' da home,
        priorizando comentários completos de agências ativas, autores únicos e países variados."""
        try:
            limite = max(1, min(int(request.query_params.get('limite', 3)), 12))
        except (TypeError, ValueError):
            limite = 3

        qs = (
            Avaliacao.objects.filter(nota__gte=4, id_agencia__ativo=True)
            .select_related('id_usuario', 'id_agencia', 'id_agencia__id_estado__id_pais')
            .order_by('-nota', '-id')[:60]
        )

        candidatos = [
            av for av in qs
            if av.id_usuario and (av.id_usuario.name or '').strip() and (av.comentario or '').strip()
        ]
        candidatos.sort(key=lambda a: (len(a.comentario.strip()), a.nota, a.id), reverse=True)

        escolhidos = []
        autores_vistos = set()
        textos_vistos = set()
        paises_vistos = set()

        def tentar_adicionar(av, exigir_pais_unico):
            autor_key = av.id_usuario_id
            texto_key = av.comentario.strip().lower()
            estado = av.id_agencia.id_estado
            pais_nome = estado.id_pais.nome if estado and estado.id_pais else ''
            if autor_key in autores_vistos or texto_key in textos_vistos:
                return
            if exigir_pais_unico and pais_nome and pais_nome in paises_vistos:
                return
            autores_vistos.add(autor_key)
            textos_vistos.add(texto_key)
            if pais_nome:
                paises_vistos.add(pais_nome)
            escolhidos.append({
                'id': av.id,
                'nota': av.nota,
                'texto': av.comentario.strip(),
                'autor': av.id_usuario.name,
                'autor_username': av.id_usuario.username or '',
                'autor_foto': url_para_campo_arquivo(av.id_usuario.avatar or av.id_usuario.foto, request),
                'agencia_id': av.id_agencia_id,
                'agencia_nome': av.id_agencia.nome,
                'cidade': estado.cidade_principal if estado else None,
                'pais': pais_nome or None,
            })

        for av in candidatos:
            if len(escolhidos) >= limite:
                break
            tentar_adicionar(av, exigir_pais_unico=True)

        if len(escolhidos) < limite:
            for av in candidatos:
                if len(escolhidos) >= limite:
                    break
                tentar_adicionar(av, exigir_pais_unico=False)

        return Response(escolhidos)

    @action(detail=False, methods=['get'], url_path='minhas', permission_classes=[IsAuthenticated])
    def minhas(self, request):
        """Lista as avaliações feitas pelo próprio usuário autenticado."""
        qs = (
            Avaliacao.objects.filter(id_usuario=request.user)
            .select_related('id_agencia', 'id_agencia__id_estado__id_pais')
            .order_by('-id')
        )
        dados = []
        for av in qs:
            estado = av.id_agencia.id_estado if av.id_agencia else None
            partes = [
                estado.cidade_principal if estado else None,
                estado.id_pais.nome if estado and estado.id_pais else None,
            ]
            dados.append({
                'id': av.id,
                'nota': av.nota,
                'comentario': av.comentario,
                'agencia_id': av.id_agencia_id,
                'agencia_nome': av.id_agencia.nome if av.id_agencia else 'Agência',
                'local': ' · '.join(p for p in partes if p),
            })
        return Response(dados)

    def perform_create(self, serializer):
        obj, _ = Avaliacao.objects.update_or_create(
            id_usuario=self.request.user,
            id_agencia=serializer.validated_data['id_agencia'],
            defaults={
                'nota': serializer.validated_data['nota'],
                'comentario': serializer.validated_data['comentario'],
            },
        )
        serializer.instance = obj

    def _garantir_dono(self):
        avaliacao = self.get_object()
        if avaliacao.id_usuario_id != self.request.user.id:
            raise PermissionDenied('Você só pode alterar as suas próprias avaliações.')

    def perform_update(self, serializer):
        self._garantir_dono()
        serializer.save(id_usuario=self.request.user)

    def perform_destroy(self, instance):
        if instance.id_usuario_id != self.request.user.id:
            raise PermissionDenied('Você só pode apagar as suas próprias avaliações.')
        instance.delete()
