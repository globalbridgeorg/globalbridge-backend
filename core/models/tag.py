from django.db import models


class Tag(models.Model):
    """Categoria fixa usada pelo painel de filtros do mapa (emprego,
    universidade, idioma, cultura) — atribuída manualmente a países e
    agências, não editável por elas."""

    CATEGORIA_CHOICES = [
        ('emprego', 'Emprego'),
        ('universidade', 'Universidade'),
        ('idioma', 'Idioma'),
        ('cultura', 'Cultura'),
    ]

    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    valor = models.SlugField(max_length=30)
    label = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.categoria}:{self.valor}"

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        unique_together = ('categoria', 'valor')
        ordering = ['categoria', 'valor']
