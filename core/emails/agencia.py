"""E-mails do fluxo de verificação de agência (pedido recebido/aprovado/recusado)."""

from django.conf import settings

from .layout import _CREME_CLARO, _ESCURO, _FONTE, _MAUVE, _VERDE, _VERMELHO, _botao, _enviar, _paragrafo, _shell


def enviar_pedido_recebido(solicitacao):
    link_status = f'{settings.FRONTEND_URL}/business/analise'
    html = _shell(
        'Verificação de agência', _MAUVE,
        'Recebemos seu<br>pedido',
        (
            _paragrafo(f'Oi, {solicitacao.nome_responsavel}! Recebemos o pedido de verificação da agência '
                       f'<strong style="color:{_ESCURO};">{solicitacao.nome}</strong> na GlobalBridge.')
            + _paragrafo('Nosso time vai conferir os dados e o documento enviado — a análise costuma levar '
                         'até 5 dias úteis. Você já pode logar a qualquer momento pra acompanhar o status.')
            + _botao('Acompanhar status', link_status)
        ),
        f'Este e-mail confirma o pedido enviado com o endereço {solicitacao.email_responsavel}. '
        f'Se não foi você, ignore esta mensagem.',
    )
    _enviar(
        solicitacao.email_responsavel,
        'Recebemos seu pedido pra virar agência parceira GlobalBridge',
        (
            f'Oi, {solicitacao.nome_responsavel}!\n\n'
            f'Recebemos o pedido de verificação da agência "{solicitacao.nome}" '
            f'na GlobalBridge. Nosso time vai conferir os dados e o documento '
            f'enviado — a análise costuma levar até 5 dias úteis.\n\n'
            f'Você já pode logar com o e-mail e a senha que escolheu no '
            f'formulário pra acompanhar o status a qualquer momento:\n'
            f'{link_status}\n\n'
            f'— Equipe GlobalBridge'
        ),
        html,
    )


def enviar_pedido_aprovado(solicitacao):
    link_login = f'{settings.FRONTEND_URL}/login'
    html = _shell(
        'Agência aprovada', _VERDE,
        f'Boas notícias,<br>{solicitacao.nome_responsavel}!',
        (
            _paragrafo(f'A agência <strong style="color:{_ESCURO};">{solicitacao.nome}</strong> foi verificada '
                       f'e aprovada pela GlobalBridge. Sua conta business já está liberada.')
            + _paragrafo('Loga com o e-mail e a senha que você escolheu no pedido — por lá você já pode '
                         'editar a página da sua agência.')
            + _botao('Ir pro login', link_login)
        ),
        f'Enviado pra {solicitacao.email_responsavel} porque essa é a conta business vinculada à agência '
        f'{solicitacao.nome} na GlobalBridge.',
    )
    _enviar(
        solicitacao.email_responsavel,
        'Sua agência foi aprovada na GlobalBridge!',
        (
            f'Boas notícias, {solicitacao.nome_responsavel}!\n\n'
            f'A agência "{solicitacao.nome}" foi verificada e aprovada pela '
            f'GlobalBridge. Sua conta business já está liberada — loga com o '
            f'e-mail e a senha que você escolheu no pedido:\n'
            f'{link_login}\n\n'
            f'Por lá você já pode editar a página da sua agência.\n\n'
            f'— Equipe GlobalBridge'
        ),
        html,
    )


def enviar_pedido_recusado(solicitacao):
    link_novo_pedido = f'{settings.FRONTEND_URL}/business/solicitar'
    motivo = solicitacao.motivo_recusa or 'Não conseguimos confirmar as informações enviadas.'
    html = _shell(
        'Sobre seu pedido', _VERMELHO,
        'Não conseguimos<br>aprovar dessa vez',
        (
            _paragrafo(f'Oi, {solicitacao.nome_responsavel}. Analisamos o pedido da agência '
                       f'<strong style="color:{_ESCURO};">{solicitacao.nome}</strong> e, por enquanto, '
                       f'não conseguimos aprovar:')
            + f'<div style="background:{_CREME_CLARO};border-radius:12px;padding:16px 20px;margin:0 0 20px;">'
              f'<p style="margin:0;color:{_ESCURO};font-family:{_FONTE};font-size:14.5px;line-height:1.6;">{motivo}</p></div>'
            + _botao('Enviar novo pedido', link_novo_pedido)
        ),
        'Dúvidas sobre essa decisão? Responde este e-mail ou fala com a gente pela página de contato.',
    )
    _enviar(
        solicitacao.email_responsavel,
        'Sobre seu pedido de verificação na GlobalBridge',
        (
            f'Oi, {solicitacao.nome_responsavel}.\n\n'
            f'Analisamos o pedido da agência "{solicitacao.nome}" e, por '
            f'enquanto, não conseguimos aprovar:\n\n'
            f'{motivo}\n\n'
            f'Se quiser corrigir as informações e tentar de novo, é só '
            f'enviar um novo pedido:\n{link_novo_pedido}\n\n'
            f'— Equipe GlobalBridge'
        ),
        html,
    )
