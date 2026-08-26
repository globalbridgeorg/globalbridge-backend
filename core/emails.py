"""
E-mails transacionais do site. Cada função monta um e-mail com versão em
texto puro (fallback) e uma versão em HTML estilizada com a identidade
visual da GlobalBridge, e manda com EmailMultiAlternatives — em
DEVELOPMENT sem EMAIL_HOST configurado, isso só imprime no console (ver
EMAIL_BACKEND em app/settings.py); em produção envia de verdade via SMTP.

Fontes web (Google Fonts) não são usadas aqui de propósito — muitos
clientes de e-mail (Outlook, apps de e-mail corporativo) bloqueiam ou
ignoram @import/<link> em HTML de e-mail, então a marca fica só nas
cores e no wordmark, com uma fonte segura (Arial/Helvetica) no texto.
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

# Paleta da marca (ver src/assets/css/global.css no frontend)
_CREME = '#FFFFFF'
_CREME_CLARO = '#F4F4F5'
_ESCURO = '#17111A'
_MAGENTA = '#B01FB0'
_MAGENTA_FORTE = '#7A0F74'
_MAUVE = '#5A4757'
_AZUL = '#3972DE'
_VERDE = '#3D9A4B'
_VERMELHO = '#dc2626'
_CINZA_TEXTO = '#55505A'
_CINZA_CLARO = '#757067'
_LINHA = 'rgba(46,10,46,0.16)'

_FONTE = "Arial, Helvetica, sans-serif"

_WORDMARK = (
    f'<span style="font-family:{_FONTE};font-weight:800;font-size:20px;'
    f'letter-spacing:-0.01em;color:{_ESCURO};">GLOBAL'
    f'<span style="color:{_MAGENTA};">BRIDGE</span></span>'
)


def _botao(texto, link):
    return (
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td '
        f'style="background:{_ESCURO};border-radius:12px;">'
        f'<a href="{link}" style="display:inline-block;padding:14px 28px;color:#ffffff;'
        f'font-family:{_FONTE};font-weight:700;font-size:12.5px;letter-spacing:0.06em;'
        f'text-transform:uppercase;text-decoration:none;">{texto}</a>'
        f'</td></tr></table>'
    )


def _shell(eyebrow, eyebrow_cor, titulo_html, corpo_html, footer_html):
    return f"""\
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_CREME};padding:40px 16px;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#ffffff;border:1px solid {_LINHA};border-radius:20px;">
<tr><td style="padding:36px 40px 8px;font-family:{_FONTE};">
  {_WORDMARK}
  <div style="height:24px;line-height:24px;font-size:1px;">&nbsp;</div>
  <span style="display:block;font-family:{_FONTE};font-weight:700;font-size:12px;letter-spacing:0.14em;
    text-transform:uppercase;color:{eyebrow_cor};margin-bottom:10px;">{eyebrow}</span>
  <h1 style="margin:0 0 16px;font-family:{_FONTE};font-weight:800;letter-spacing:-0.01em;
    line-height:1.2;color:{_ESCURO};font-size:24px;">{titulo_html}</h1>
  {corpo_html}
</td></tr>
<tr><td style="padding:8px 40px 0;">
  <div style="height:1px;line-height:1px;font-size:1px;background:{_LINHA};">&nbsp;</div>
</td></tr>
<tr><td style="padding:20px 40px 32px;font-family:{_FONTE};color:{_CINZA_CLARO};font-size:12.5px;line-height:1.6;">
  {footer_html}
</td></tr>
</table>
</td></tr>
</table>"""


def _paragrafo(texto):
    return f'<p style="margin:0 0 20px;color:{_CINZA_TEXTO};font-family:{_FONTE};font-size:15px;line-height:1.65;">{texto}</p>'


def _enviar(destinatario, assunto, texto_puro, html):
    email = EmailMultiAlternatives(
        subject=assunto,
        body=texto_puro,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[destinatario],
    )
    email.attach_alternative(html, 'text/html')
    email.send(fail_silently=False)


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


def enviar_boas_vindas(usuario):
    link = f'{settings.FRONTEND_URL}/destinos'
    nome = usuario.name or usuario.email
    html = _shell(
        'Bem-vindo(a)', _MAGENTA,
        'Sua conta na<br>GlobalBridge está pronta',
        (
            _paragrafo(f'Oi, {nome}! Sua conta foi criada — agora você já pode explorar destinos, comparar '
                       f'agências e favoritar programas de intercâmbio pra decidir com calma.')
            + _botao('Começar a explorar', link)
        ),
        f'Você recebeu este e-mail porque criou uma conta em globalbridge.com.br com o endereço '
        f'{usuario.email}. Se não foi você, ignore esta mensagem.',
    )
    _enviar(
        usuario.email,
        'Sua conta na GlobalBridge está pronta',
        (
            f'Oi, {nome}!\n\n'
            f'Sua conta foi criada — agora você já pode explorar destinos, '
            f'comparar agências e favoritar programas de intercâmbio pra '
            f'decidir com calma.\n\n'
            f'{link}\n\n'
            f'— Equipe GlobalBridge'
        ),
        html,
    )


def enviar_codigo_login(usuario, codigo):
    codigo_espacado = f'{codigo[:3]} {codigo[3:]}' if len(codigo) == 6 else codigo
    html = _shell(
        'Código de acesso', _MAGENTA,
        'Seu código<br>de login',
        (
            _paragrafo('Use o código abaixo pra entrar na sua conta GlobalBridge. Ele expira em 10 minutos.')
            + f'<div style="background:{_CREME_CLARO};border-radius:14px;padding:22px;text-align:center;margin:0 0 20px;">'
              f'<span style="font-family:\'Courier New\',monospace;font-weight:700;font-size:32px;letter-spacing:8px;'
              f'color:{_ESCURO};">{codigo_espacado}</span></div>'
            + f'<p style="margin:0;color:{_CINZA_CLARO};font-family:{_FONTE};font-size:13px;line-height:1.6;">'
              f'Não pediu esse código? Pode ignorar este e-mail — sua conta continua segura.</p>'
        ),
        'Por segurança, nunca compartilhe esse código — a GlobalBridge nunca vai pedir ele por telefone ou chat.',
    )
    _enviar(
        usuario.email,
        f'Seu código de login: {codigo}',
        (
            f'Use o código abaixo pra entrar na sua conta GlobalBridge. '
            f'Ele expira em 10 minutos.\n\n'
            f'{codigo}\n\n'
            f'Não pediu esse código? Pode ignorar este e-mail — sua conta '
            f'continua segura.\n\n'
            f'— Equipe GlobalBridge'
        ),
        html,
    )


def enviar_redefinir_senha(usuario, link):
    html = _shell(
        'Redefinição de senha', _AZUL,
        'Vamos trocar<br>sua senha',
        (
            _paragrafo(f'Recebemos um pedido pra redefinir a senha da sua conta ({usuario.email}). '
                       f'Clica no botão abaixo pra escolher uma nova — o link expira em algumas horas.')
            + _botao('Redefinir senha', link)
            + f'<p style="margin:20px 0 0;color:{_CINZA_CLARO};font-family:{_FONTE};font-size:13px;line-height:1.6;">'
              f'Não pediu essa troca? Ignora este e-mail — sua senha continua a mesma e sua conta está segura.</p>'
        ),
        f'Se o botão não funcionar, copie e cole este link no navegador: {link}',
    )
    _enviar(
        usuario.email,
        'Redefinir sua senha na GlobalBridge',
        (
            f'Recebemos um pedido pra redefinir a senha da sua conta '
            f'({usuario.email}). Clica no link abaixo pra escolher uma '
            f'nova — ele expira em algumas horas:\n\n'
            f'{link}\n\n'
            f'Não pediu essa troca? Ignora este e-mail — sua senha continua '
            f'a mesma e sua conta está segura.\n\n'
            f'— Equipe GlobalBridge'
        ),
        html,
    )
