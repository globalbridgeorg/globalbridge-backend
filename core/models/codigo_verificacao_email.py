from django.db import models
from django.utils import timezone


class CodigoVerificacaoEmail(models.Model):
    """Código numérico de 6 dígitos pra confirmar o e-mail durante o
    cadastro — pedido em /auth/cadastro/codigo/solicitar/ e confirmado em
    /auth/cadastro/codigo/verificar/. Guarda o e-mail direto (não uma FK
    pro usuário) porque nesse ponto do cadastro o usuário ainda não
    existe. /registro/ confere de novo se há um registro `verificado=True`
    recente pra esse e-mail antes de criar a conta de verdade."""

    VALIDADE_MINUTOS = 10
    JANELA_REGISTRO_MINUTOS = 30

    email = models.EmailField()
    codigo = models.CharField(max_length=6)
    criado_em = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)
    verificado = models.BooleanField(default=False)
    verificado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Código de verificação de e-mail'
        verbose_name_plural = 'Códigos de verificação de e-mail'
        ordering = ['-criado_em']

    def valido(self):
        expira_em = self.criado_em + timezone.timedelta(minutes=self.VALIDADE_MINUTOS)
        return not self.usado and timezone.now() < expira_em

    @classmethod
    def email_verificado_recentemente(cls, email):
        janela = timezone.now() - timezone.timedelta(minutes=cls.JANELA_REGISTRO_MINUTOS)
        return cls.objects.filter(email=email, verificado=True, verificado_em__gte=janela).exists()

    def __str__(self):
        return f'{self.email} — {self.codigo}'
