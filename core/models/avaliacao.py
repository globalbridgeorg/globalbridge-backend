from django.db import models

from .user import User
from .agencia import Agencia

class Avaliacao(models.Model):
    nota = models.IntegerField()
    comentario = models.TextField()
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    id_agencia = models.ForeignKey(Agencia, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}-{self.id_usuario}->{self.id_agencia}"
    
    class Meta:
        verbose_name = "Avaliacao"
        verbose_name_plural = "Avaliacoes"