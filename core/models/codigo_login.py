from django.conf import settings
from django.db import models
from django.utils import timezone


class CodigoLogin(models.Model):
    """Código numérico de 6 dígitos pra login sem senha — pedido em
    /auth/codigo/solicitar/ e trocado por um par de tokens JWT em
    /auth/codigo/verificar/. Expira sozinho (ver `valido()`); não precisa
    de uma tarefa de limpeza porque a verificação já filtra por validade."""

    VALIDADE_MINUTOS = 10

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='codigos_login')
    codigo = models.CharField(max_length=6)
    criado_em = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Código de login'
        verbose_name_plural = 'Códigos de login'
        ordering = ['-criado_em']

    def valido(self):
        expira_em = self.criado_em + timezone.timedelta(minutes=self.VALIDADE_MINUTOS)
        return not self.usado and timezone.now() < expira_em

    def __str__(self):
        return f'{self.usuario.email} — {self.codigo}'
