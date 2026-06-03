from django.db import models
from django.db.models import CASCADE 


from .pais import Pais

class Estado(models.Model):
    nome = models.CharField(max_length=100)
    cidade_principal = models.CharField(max_length=100)
    id_pais = models.ForeignKey(Pais, on_delete=CASCADE)

    def __str__(self):
        return f"{self.id}-{self.nome}"