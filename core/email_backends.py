"""
Backend de e-mail que envia via a API transacional do Brevo (Sendinblue)
em vez de SMTP — usado quando BREVO_API_KEY está configurada (ver
app/settings.py). Implementa só o necessário do contrato do Django
(BaseEmailBackend.send_messages), incluindo a versão HTML que
core/emails.py anexa via EmailMultiAlternatives.
"""

import requests
from django.core.mail.backends.base import BaseEmailBackend


class BrevoAPIBackend(BaseEmailBackend):
    API_URL = 'https://api.brevo.com/v3/smtp/email'

    def __init__(self, *args, api_key=None, **kwargs):
        super().__init__(*args, **kwargs)
        from django.conf import settings
        self.api_key = api_key or settings.BREVO_API_KEY

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        enviados = 0
        for message in email_messages:
            from_email = message.from_email
            nome_remetente, email_remetente = self._separar_nome_email(from_email)

            payload = {
                'sender': {'email': email_remetente, 'name': nome_remetente} if nome_remetente else {'email': email_remetente},
                'to': [{'email': destinatario} for destinatario in message.to],
                'subject': message.subject,
                'textContent': message.body,
            }

            html_content = next(
                (conteudo for conteudo, tipo in getattr(message, 'alternatives', []) if tipo == 'text/html'),
                None,
            )
            if html_content:
                payload['htmlContent'] = html_content

            try:
                resposta = requests.post(
                    self.API_URL,
                    json=payload,
                    headers={'api-key': self.api_key, 'Content-Type': 'application/json'},
                    timeout=10,
                )
                resposta.raise_for_status()
                enviados += 1
            except requests.RequestException:
                if not self.fail_silently:
                    raise

        return enviados

    @staticmethod
    def _separar_nome_email(from_email):
        """'GlobalBridge <a@b.com>' -> ('GlobalBridge', 'a@b.com'); 'a@b.com' -> (None, 'a@b.com')."""
        if '<' in from_email and from_email.endswith('>'):
            nome, email = from_email.split('<', 1)
            return nome.strip(), email.rstrip('>').strip()
        return None, from_email.strip()
