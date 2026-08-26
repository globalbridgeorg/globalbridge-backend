from django.db.models import Avg
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from core.models import Agencia, Avaliacao, Favorito, ImagemGaleria, Pais, SolicitacaoPaisAdicional
from core.serializers import AgenciaSerializer, AgenciaDetalheSerializer, AgenciaResumidaSerializer

class AgenciaViewSet(ModelViewSet):
    queryset = Agencia.objects.all()
    serializer_class = AgenciaSerializer
    # Mesmo caso do PaisViewSet: o mapa (/mapview) busca /agencia/ inteiro
    # de uma vez pra cruzar com país/tags, e paginar cortava silenciosamente
    # o catálogo assim que passou de 10 agências.
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AgenciaDetalheSerializer
        if self.action == 'list':
            return AgenciaResumidaSerializer
        return AgenciaSerializer

    def get_permissions(self):
        # Ver agência é público; criar/editar/apagar não tinha NENHUMA
        # restrição antes disso (sem DEFAULT_PERMISSION_CLASSES no projeto,
        # o padrão do DRF é liberar tudo) — qualquer um podia alterar
        # qualquer agência via API. Editar a própria página (conta
        # business) exige estar logado; quem realmente é "dono" daquela
        # agência é conferido em perform_update.
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        agencia = self.get_object()
        if agencia.usuario_id != self.request.user.id:
            raise PermissionDenied('Você só pode editar a página da sua própria agência.')
        serializer.save()

    def perform_create(self, serializer):
        raise PermissionDenied('Conta de agência só é criada depois da verificação pelo time da GlobalBridge.')

    def perform_destroy(self, instance):
        raise PermissionDenied('Não é possível excluir uma agência por aqui.')

    def get_queryset(self):
        queryset = super().get_queryset()
        pais_id = self.request.query_params.get('pais')
        regiao = self.request.query_params.get('regiao')
        if pais_id:
            queryset = queryset.filter(paises_atendidos__id=pais_id)
        if regiao:
            queryset = queryset.filter(paises_atendidos__regiao=regiao)
        return queryset.distinct()

    @action(
        detail=True, methods=['patch'], url_path='capa',
        permission_classes=[IsAuthenticated], parser_classes=[MultiPartParser, FormParser],
    )
    def capa(self, request, pk=None):
        """Sobe a imagem de capa da agência (editor da conta business) — só
        o dono da agência pode trocar."""
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id:
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
        """Adiciona uma foto na galeria — cada chamada sobe uma imagem;
        o front chama isso uma vez por arquivo selecionado."""
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id:
            raise PermissionDenied('Você só pode editar a página da sua própria agência.')

        arquivo = request.FILES.get('imagem')
        if not arquivo:
            return Response({'detail': 'Envie uma imagem no campo imagem.'}, status=400)

        ordem = agencia.galeria.count()
        img = ImagemGaleria.objects.create(agencia=agencia, ordem=ordem)
        img.imagem.save(arquivo.name, arquivo, save=True)

        file_value = getattr(img.imagem, 'name', img.imagem)
        url = file_value if file_value.startswith('http') else request.build_absolute_uri(img.imagem.url)
        return Response({'id': img.id, 'url': url}, status=201)

    @action(detail=True, methods=['delete'], url_path=r'galeria/(?P<imagem_id>\d+)', permission_classes=[IsAuthenticated])
    def galeria_remover(self, request, pk=None, imagem_id=None):
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id:
            raise PermissionDenied('Você só pode editar a página da sua própria agência.')

        try:
            img = agencia.galeria.get(id=imagem_id)
        except ImagemGaleria.DoesNotExist:
            return Response({'detail': 'Imagem não encontrada.'}, status=404)

        img.delete()
        return Response(status=204)

    @action(detail=True, methods=['get'], url_path='painel', permission_classes=[IsAuthenticated])
    def painel(self, request, pk=None):
        """Dados agregados do dashboard da conta business — tudo real,
        nada fabricado: vem de Avaliacao, Favorito, Plano, Tag e da
        SolicitacaoAgencia original."""
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id:
            raise PermissionDenied('Você só pode ver o painel da sua própria agência.')

        avaliacoes_qs = Avaliacao.objects.filter(id_agencia=agencia).select_related('id_usuario').order_by('-id')
        total_avaliacoes = avaliacoes_qs.count()
        nota_media = avaliacoes_qs.aggregate(media=Avg('nota'))['media']
        distribuicao = []
        for estrelas in (5, 4, 3, 2, 1):
            qtd = avaliacoes_qs.filter(nota=estrelas).count()
            distribuicao.append({
                'estrelas': estrelas,
                'quantidade': qtd,
                'largura': round(qtd / total_avaliacoes * 100) if total_avaliacoes else 0,
            })

        favoritos_qs = Favorito.objects.filter(tipo='agencia', objeto_id=agencia.id).select_related('id_usuario')
        ha_30_dias = timezone.now() - timezone.timedelta(days=30)

        planos_qs = agencia.plano_set.select_related('id_programa').all()

        solicitacao = getattr(agencia, 'solicitacao_origem', None)

        paises_pendentes = SolicitacaoPaisAdicional.objects.filter(agencia=agencia, status='pendente').select_related('pais')

        # Ranking: posição da agência entre as demais com sede no mesmo
        # país, por nota média — só faz sentido comparar dentro do mesmo
        # mercado.
        ranking = None
        if agencia.id_estado_id:
            pais_sede = agencia.id_estado.id_pais
            concorrentes = (
                Agencia.objects.filter(id_estado__id_pais=pais_sede, ativo=True)
                .annotate(nota=Avg('avaliacao__nota'))
                .order_by('-nota')
            )
            ids_ordenados = list(concorrentes.values_list('id', flat=True))
            if agencia.id in ids_ordenados:
                ranking = {'posicao': ids_ordenados.index(agencia.id) + 1, 'total': len(ids_ordenados), 'pais': pais_sede.nome}

        campos_completude = [
            ('Descrição preenchida', bool(agencia.descricao.strip())),
            ('"Como funciona" preenchido', bool(agencia.como_funciona.strip())),
            ('Imagem de capa enviada', bool(agencia.imagem_capa)),
            ('Layout personalizado', bool(agencia.layout)),
            ('Ao menos 1 programa cadastrado', planos_qs.exists()),
            ('Ao menos 1 especialidade marcada', agencia.tags.exists()),
        ]
        feitos = sum(1 for _, feito in campos_completude if feito)

        paises_atendidos_ids = set(agencia.paises_atendidos.values_list('id', flat=True))

        return Response({
            'stats': {
                'nota': round(nota_media, 1) if nota_media is not None else None,
                'total_avaliacoes': total_avaliacoes,
                'favoritos': favoritos_qs.count(),
                'favoritos_30_dias': favoritos_qs.filter(criado_em__gte=ha_30_dias).count(),
                'programas': planos_qs.count(),
                'paises': len(paises_atendidos_ids),
            },
            'ranking': ranking,
            'distribuicao_notas': distribuicao,
            'completude': {
                'percentual': round(feitos / len(campos_completude) * 100) if campos_completude else 0,
                'itens': [{'texto': texto, 'feito': feito} for texto, feito in campos_completude],
            },
            'paises_atendidos': [{'id': p.id, 'nome': p.nome, 'sigla': p.codigo_iso} for p in agencia.paises_atendidos.all()],
            'paises_pendentes': [{'id': s.pais.id, 'nome': s.pais.nome, 'sigla': s.pais.codigo_iso} for s in paises_pendentes],
            'planos': [
                {
                    'id': p.id, 'nome': p.id_programa.nome,
                    'duracao': f'{p.id_programa.duracao_min} a {p.id_programa.duracao_max} semanas',
                    'preco': float(p.preco),
                }
                for p in planos_qs
            ],
            'tags': [t.label or t.valor for t in agencia.tags.all()],
            'contato': {
                'email': agencia.contato, 'telefone': agencia.telefone,
                'site': agencia.site, 'endereco': agencia.endereco,
            },
            'verificacao': {
                'responsavel': solicitacao.nome_responsavel if solicitacao else None,
                'cargo': solicitacao.cargo_responsavel if solicitacao else None,
                'enviado_em': solicitacao.criado_em if solicitacao else None,
                'aprovado_em': solicitacao.revisado_em if solicitacao else None,
            } if solicitacao else None,
            'avaliacoes_recentes': [
                {
                    'nome': a.id_usuario.name or a.id_usuario.email,
                    'nota': a.nota,
                    'comentario': a.comentario,
                }
                for a in avaliacoes_qs[:5]
            ],
            'favoritos_recentes': [
                {
                    'nome': f.id_usuario.name or f.id_usuario.email,
                    'quando': f.criado_em,
                }
                for f in favoritos_qs.order_by('-criado_em')[:6]
            ],
        })

    @action(detail=True, methods=['post'], url_path='paises/solicitar', permission_classes=[IsAuthenticated])
    def solicitar_pais(self, request, pk=None):
        """A agência pede pra passar a atender mais um país — fica
        pendente até o time aprovar (ver SolicitacaoPaisAdicionalAdmin)."""
        agencia = self.get_object()
        if agencia.usuario_id != request.user.id:
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
