"""Endpoints administrativos para o painel /admin do frontend (somente is_staff).

Reaproveita a mesma lógica de aprovação/recusa usada pelo Django Admin nativo
(`core.admin.solicitacoes_acoes`) para manter comportamento idêntico nos dois painéis.
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.admin.solicitacoes_acoes import _aprovar_uma_solicitacao, _recusar_uma_solicitacao
from core.models import MensagemContato, SolicitacaoAgencia, SolicitacaoPaisAdicional
from core.serializers import MensagemContatoSerializer
from core.storage import criar_url_assinada_supabase, resolver_bucket_e_objeto, supabase_storage_ativo, url_para_campo_arquivo


class AdminDadosView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        sol_ag = SolicitacaoAgencia.objects.select_related('pais_sede').order_by('-criado_em')
        sol_pais = SolicitacaoPaisAdicional.objects.select_related('agencia', 'pais').order_by('-criado_em')
        mensagens = MensagemContato.objects.all().order_by('-criado_em')[:50]

        solicitacoes_agencia = [
            {
                'id': s.id,
                'nome': s.nome,
                'site': s.site,
                'cidade': s.cidade,
                'ano_fundacao': s.ano_fundacao,
                'nome_responsavel': s.nome_responsavel,
                'cargo_responsavel': s.cargo_responsavel,
                'email_responsavel': s.email_responsavel,
                'documento_path': s.documento.name if s.documento else '',
                'descricao': s.descricao,
                'status': s.status,
                'motivo_recusa': s.motivo_recusa,
                'criado_em': s.criado_em,
                'revisado_em': s.revisado_em,
                'pais_sede': {'nome': s.pais_sede.nome} if s.pais_sede else None,
            }
            for s in sol_ag
        ]

        solicitacoes_pais = [
            {
                'id': sp.id,
                'status': sp.status,
                'motivo_recusa': sp.motivo_recusa,
                'criado_em': sp.criado_em,
                'revisado_em': sp.revisado_em,
                'agencia': {'id': sp.agencia.id, 'nome': sp.agencia.nome} if sp.agencia else None,
                'pais': {'id': sp.pais.id, 'nome': sp.pais.nome} if sp.pais else None,
            }
            for sp in sol_pais
        ]

        return Response({
            'solicitacoesAgencia': solicitacoes_agencia,
            'solicitacoesPais': solicitacoes_pais,
            'mensagens': MensagemContatoSerializer(mensagens, many=True).data,
        })


class AdminDocumentoUrlView(APIView):
    """Gera URL assinada (ou local) somente para comprovantes vinculados a uma solicitação real."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        path = (request.query_params.get('path') or '').strip()
        if not path:
            return Response({'detail': 'Informe o parâmetro path.'}, status=status.HTTP_400_BAD_REQUEST)

        sol = SolicitacaoAgencia.objects.filter(documento=path).first()
        if not sol or not sol.documento:
            return Response({'detail': 'Comprovante não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if supabase_storage_ativo() and not path.startswith(('http://', 'https://')):
            bucket, obj_path = resolver_bucket_e_objeto(path)
            url = criar_url_assinada_supabase(bucket, obj_path, expires_in=300)
        else:
            url = url_para_campo_arquivo(sol.documento, request)

        return Response({'url': url})


class AdminAprovarSolicitacaoAgenciaView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        sol = get_object_or_404(SolicitacaoAgencia, pk=pk)
        ok, mensagem, _ = _aprovar_uma_solicitacao(sol)
        if not ok:
            return Response({'detail': mensagem}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': mensagem, 'agencia_id': sol.agencia_criada_id})


class AdminRecusarSolicitacaoAgenciaView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        sol = get_object_or_404(SolicitacaoAgencia, pk=pk)
        motivo = (request.data.get('motivo') or '').strip()
        if motivo:
            sol.motivo_recusa = motivo
        ok, mensagem, _ = _recusar_uma_solicitacao(sol)
        if not ok:
            return Response({'detail': mensagem}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': mensagem})


class AdminAprovarPaisAdicionalView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        sol = get_object_or_404(SolicitacaoPaisAdicional, pk=pk)
        if sol.status != 'pendente':
            return Response({'detail': 'Esta solicitação não está mais pendente.'}, status=status.HTTP_400_BAD_REQUEST)

        sol.agencia.paises_atendidos.add(sol.pais)
        sol.status = 'aprovado'
        sol.revisado_em = timezone.now()
        sol.save(update_fields=['status', 'revisado_em'])
        return Response({'detail': f'{sol.pais.nome} liberado para {sol.agencia.nome}.'})


class AdminRecusarPaisAdicionalView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        sol = get_object_or_404(SolicitacaoPaisAdicional, pk=pk)
        if sol.status != 'pendente':
            return Response({'detail': 'Esta solicitação não está mais pendente.'}, status=status.HTTP_400_BAD_REQUEST)

        sol.motivo_recusa = (request.data.get('motivo') or '').strip()
        sol.status = 'recusado'
        sol.revisado_em = timezone.now()
        sol.save(update_fields=['status', 'motivo_recusa', 'revisado_em'])
        return Response({'detail': 'Solicitação de país recusada.'})


class AdminMensagemLidaView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        msg = get_object_or_404(MensagemContato, pk=pk)
        msg.lida = bool(request.data.get('lida', True))
        msg.save(update_fields=['lida'])
        return Response(MensagemContatoSerializer(msg).data)
