from django.db import models

from .user import User

class Agencia(models.Model):
    nome = models.CharField(max_length=50)
    descricao = models.TextField()
    contato =   models.CharField(max_length=100)
    telefone =  models.CharField(max_length=20)
    site = models.CharField(max_length=255)
    endereco = models.TextField()
    data_cadastro = models.DateTimeField()
    ativo = models.BooleanField()
    id_user = models.ForeignKey(User, on_delete=CASCADE)


    def __str__(self):
        return f"{self.id} - {self.nome}"

    class Meta:
        verbose_name = "Agencia"
        verbose_name_plural = "Agencias"