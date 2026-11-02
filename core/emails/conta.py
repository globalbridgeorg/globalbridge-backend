"""E-mails de conta: boas-vindas, códigos de login/cadastro e redefinição de senha."""

from django.conf import settings

from .layout import _AZUL, _CINZA_CLARO, _CREME_CLARO, _ESCURO, _FONTE, _MAGENTA, _botao, _enviar, _paragrafo, _shell


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


def enviar_codigo_cadastro(email, codigo):
    codigo_espacado = f'{codigo[:3]} {codigo[3:]}' if len(codigo) == 6 else codigo
    html = _shell(
        'Confirme seu e-mail', _MAGENTA,
        'Confirme seu<br>e-mail',
        (
            _paragrafo('Use o código abaixo pra confirmar seu e-mail e concluir seu cadastro na GlobalBridge. '
                       'Ele expira em 10 minutos.')
            + f'<div style="background:{_CREME_CLARO};border-radius:14px;padding:22px;text-align:center;margin:0 0 20px;">'
              f'<span style="font-family:\'Courier New\',monospace;font-weight:700;font-size:32px;letter-spacing:8px;'
              f'color:{_ESCURO};">{codigo_espacado}</span></div>'
            + f'<p style="margin:0;color:{_CINZA_CLARO};font-family:{_FONTE};font-size:13px;line-height:1.6;">'
              f'Não pediu esse cadastro? Pode ignorar este e-mail — nenhuma conta será criada.</p>'
        ),
        'Por segurança, nunca compartilhe esse código — a GlobalBridge nunca vai pedir ele por telefone ou chat.',
    )
    _enviar(
        email,
        f'Seu código de confirmação: {codigo}',
        (
            f'Use o código abaixo pra confirmar seu e-mail e concluir seu '
            f'cadastro na GlobalBridge. Ele expira em 10 minutos.\n\n'
            f'{codigo}\n\n'
            f'Não pediu esse cadastro? Pode ignorar este e-mail — nenhuma '
            f'conta será criada.\n\n'
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
