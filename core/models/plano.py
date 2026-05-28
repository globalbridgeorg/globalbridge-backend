from django.db import models

from .agencia import Agencia
from .programa import Programa

class Plano (models.Model):
    id_agencia = models.ForeignKey(Agencia, on_delete=models.CASCADE)
    id_programa = models.ForeignKey(Programa, on_delete=models.CASCADE)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField()
    inclui = models.TextField

    def __str__(self):
        return f"{self.id} - {self.nome}"
    
    class Meta: 
        verbose_name = "Plano"
        verbose_name_plural = "Planos"