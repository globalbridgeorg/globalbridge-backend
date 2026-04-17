from django.db import models

class Pais(models.Model):
    nome = models.CharField(max_length=51)
    codigo_iso = models.CharField(max_length=2)
    custo_de_vida = models.CharField(max_length=20)
    idioma = models.CharField(max_length=50)
    cultura = models.TextField()
    descricao = models.TextField()
    imagem_url = models.CharField(max_length=250)
    intercambistas = models.IntegerField()
    universidades = models.IntegerField()
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id} - {self.nome} ({self.codigo_iso})"

    class Meta:
        verbose_name = "pais"
        verbose_name_plural = "Países"