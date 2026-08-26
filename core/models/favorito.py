from django.conf import settings
from django.db import models


class Favorito(models.Model):
    TIPO_CHOICES = [
        ('pais', 'País'),
        ('agencia', 'Agência'),
    ]

    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoritos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    objeto_id = models.PositiveIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        unique_together = ('id_usuario', 'tipo', 'objeto_id')
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.id_usuario} -> {self.tipo}:{self.objeto_id}'
