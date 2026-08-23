from django.conf import settings
from django.db import models

class Agencia(models.Model):
    nome = models.CharField(max_length=50)
    descricao = models.TextField()
    contato =   models.CharField(max_length=100)
    telefone =  models.CharField(max_length=20)
    site = models.CharField(max_length=255)
    endereco = models.TextField()
    data_cadastro = models.DateTimeField()
    ativo = models.BooleanField()
    id_estado = models.ForeignKey(
        'Estado', on_delete=models.SET_NULL, null=True, blank=True, related_name='agencias'
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='agencia'
    )
    tags = models.ManyToManyField('Tag', related_name='agencias', blank=True)

    def __str__(self):
        return f"{self.id} - {self.nome}"

    class Meta:
        verbose_name = "Agencia"
        verbose_name_plural = "Agencias"