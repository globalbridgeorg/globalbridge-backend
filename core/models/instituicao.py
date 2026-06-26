from django.db import models
from core.models.estado import Estado


class Instituicao(models.Model):
    nome = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    endereco = models.TextField()
    estado = models.ForeignKey(
        Estado,
        on_delete=models.CASCADE,
        related_name='instituicoes'
    )

    def __str__(self):
        return f"{self.nome} - {self.cidade}"

    class Meta:
        verbose_name = "instituicao"
        verbose_name_plural = "instituicoes"