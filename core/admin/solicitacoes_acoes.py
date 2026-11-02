"""Lógica de aprovar/recusar uma SolicitacaoAgencia, compartilhada pelas
ações em massa e pelos botões de linha do SolicitacaoAgenciaAdmin."""

import logging

from django.contrib import messages
from django.utils import timezone

from core import models
from core.emails import enviar_pedido_aprovado, enviar_pedido_recusado
from core.models import Estado

logger = logging.getLogger(__name__)


def _aprovar_uma_solicitacao(solicitacao):
    """Aprova uma única solicitação pendente: cria a Agencia de verdade e
    linka nela. Retorna (ok, mensagem, nível) pra quem chamou (ação em
    massa ou botão de linha única) decidir como exibir."""
    if solicitacao.status != 'pendente':
        return False, f'{solicitacao.nome}: já não está mais pendente.', messages.WARNING
    if not solicitacao.usuario_criado:
        return False, f'{solicitacao.nome}: sem usuário vinculado, pulando (pedido antigo?).', messages.ERROR

    estado, _ = Estado.objects.get_or_create(
        cidade_principal=solicitacao.cidade, id_pais=solicitacao.pais_sede,
        defaults={'nome': solicitacao.cidade},
    )

    agencia = models.Agencia.objects.create(
        nome=solicitacao.nome,
        descricao=solicitacao.descricao or f'Agência verificada pela GlobalBridge — {solicitacao.nome}.',
        contato=solicitacao.email_responsavel,
        telefone='',
        site=solicitacao.site,
        endereco=f'{solicitacao.cidade}, {solicitacao.pais_sede.nome}',
        data_cadastro=timezone.now(),
        ativo=True,
        id_estado=estado,
        usuario=solicitacao.usuario_criado,
    )
    paises = set(solicitacao.paises_atendidos.all())
    paises.add(solicitacao.pais_sede)
    agencia.paises_atendidos.set(paises)

    solicitacao.status = 'aprovado'
    solicitacao.agencia_criada = agencia
    solicitacao.revisado_em = timezone.now()
    solicitacao.save()

    try:
        enviar_pedido_aprovado(solicitacao)
        email_status = f'e-mail de aprovação enviado pra {solicitacao.email_responsavel}'
    except Exception:
        logger.exception('Falha ao enviar e-mail de aprovação para %s', solicitacao.email_responsavel)
        email_status = 'ATENÇÃO: falha ao enviar o e-mail de aprovação, avise por outro canal'

    return True, (
        f'{solicitacao.nome}: agência criada e vinculada a {solicitacao.email_responsavel} — '
        f'a pessoa já loga com a senha que escolheu no pedido ({email_status}).'
    ), messages.SUCCESS


def _recusar_uma_solicitacao(solicitacao):
    """Recusa uma única solicitação pendente. Retorna (ok, mensagem, nível)."""
    if solicitacao.status != 'pendente':
        return False, f'{solicitacao.nome}: já não está mais pendente.', messages.WARNING

    if not solicitacao.motivo_recusa:
        solicitacao.motivo_recusa = (
            'Não conseguimos confirmar as informações enviadas. Entre em '
            'contato com a gente se quiser mais detalhes.'
        )

    solicitacao.status = 'recusado'
    solicitacao.revisado_em = timezone.now()
    solicitacao.save()

    try:
        enviar_pedido_recusado(solicitacao)
        email_status = f'e-mail enviado pra {solicitacao.email_responsavel}'
    except Exception:
        logger.exception('Falha ao enviar e-mail de recusa para %s', solicitacao.email_responsavel)
        email_status = 'ATENÇÃO: falha ao enviar o e-mail de recusa, avise por outro canal'

    return True, f'{solicitacao.nome}: pedido recusado ({email_status}).', messages.SUCCESS
