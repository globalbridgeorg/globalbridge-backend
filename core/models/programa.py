from django.db import models

class Programa(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    duracao_min = models.IntegerField()
    duracao_max = models.IntegerField()

    def __str__(self):
        return f"{self.id} - {self.nome}"