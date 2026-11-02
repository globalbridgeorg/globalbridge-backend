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

