from django.db import models

from .agencia import Agencia
from .programa import Programa
from .instituicao import Instituicao


class Plano(models.Model):
    agencia = models.ForeignKey(Agencia, on_delete=models.CASCADE, related_name='planos')
    programa = models.ForeignKey(Programa, on_delete=models.CASCADE, related_name='planos')
    instituicao = models.ForeignKey(Instituicao, on_delete=models.CASCADE, related_name='planos')
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField()
    inclui = models.TextField()

    def __str__(self):
        return f"{self.id} - {self.nome}"
    
    class Meta: 
        verbose_name = "Plano"
        verbose_name_plural = "Planos"