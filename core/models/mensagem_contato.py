from django.db import models


class MensagemContato(models.Model):
    """Mensagens enviadas pelo formulário público /contato (estudantes ou agências)."""

    PUBLICO_CHOICES = [
        ('estudante', 'Estudante'),
        ('agencia', 'Agência'),
    ]

    publico = models.CharField(max_length=20, choices=PUBLICO_CHOICES, default='estudante')
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    nome_agencia = models.CharField(max_length=120, blank=True, default='')
    assunto = models.CharField(max_length=160)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensagem de contato'
        verbose_name_plural = 'Mensagens de contato'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.nome} — {self.assunto}'
