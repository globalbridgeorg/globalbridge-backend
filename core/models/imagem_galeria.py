from django.db import models


class ImagemGaleria(models.Model):
    """Uma foto da seção 'Galeria de fotos' do editor de blocos — cada
    imagem é seu próprio registro (em vez de uma lista de URLs num JSON)
    pra aproveitar o storage de arquivo do Django/Cloudinary normalmente
    e permitir apagar uma imagem sem reenviar as outras."""

    agencia = models.ForeignKey('Agencia', on_delete=models.CASCADE, related_name='galeria')
    imagem = models.ImageField(upload_to='agencias/galeria/')
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Imagem da galeria'
        verbose_name_plural = 'Imagens da galeria'
        ordering = ['ordem', 'id']

    def __str__(self):
        return f'{self.agencia.nome} — galeria #{self.id}'
