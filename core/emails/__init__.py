"""E-mails transacionais do site — ver core/emails/layout.py pro layout compartilhado."""

from .agencia import enviar_pedido_aprovado, enviar_pedido_recebido, enviar_pedido_recusado
from .conta import enviar_boas_vindas, enviar_codigo_cadastro, enviar_codigo_login, enviar_redefinir_senha

__all__ = [
    'enviar_pedido_recebido', 'enviar_pedido_aprovado', 'enviar_pedido_recusado',
    'enviar_boas_vindas', 'enviar_codigo_login', 'enviar_codigo_cadastro', 'enviar_redefinir_senha',
]
