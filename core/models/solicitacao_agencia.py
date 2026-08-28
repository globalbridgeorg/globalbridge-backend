import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models


def _storage_documento():
    """O storage padrão do Cloudinary (STORAGES['default'] no settings.py)
    manda tudo como resource_type="image" — funciona pros outros campos de
    imagem do site, mas aqui o campo guarda o COMPROVANTE que a agência
    envia (PDF, foto de documento, etc.), não uma imagem garantida. Subir
    um PDF como "image" o Cloudinary recusa, e sem isso o pedido inteiro
    quebrava com erro 500 sem nenhuma solicitação chegar a ser salva.
    RawMediaCloudinaryStorage manda como resource_type="raw", que aceita
    qualquer tipo de arquivo. Só troca pra ele quando o Cloudinary está de
    fato configurado (mesma checagem do settings.py) — em dev sem
    CLOUDINARY_URL, cai no storage padrão de sempre (arquivo local)."""
    if os.getenv('CLOUDINARY_URL'):
        from cloudinary_storage.storage import RawMediaCloudinaryStorage
        return RawMediaCloudinaryStorage()
    return default_storage


class SolicitacaoAgencia(models.Model):
    """Pedido de verificação pra virar conta business — quem preenche
    ainda não tem login nenhum na plataforma. Só vira User + Agencia de
    verdade quando alguém do time aprova (ação no Django admin)."""

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
    ]

    # Sobre a agência
    nome = models.CharField(max_length=100)
    site = models.CharField(max_length=255, blank=True)
    cidade = models.CharField(max_length=100)
    pais_sede = models.ForeignKey('Pais', on_delete=models.PROTECT, related_name='solicitacoes_sede')
    paises_atendidos = models.ManyToManyField('Pais', related_name='solicitacoes_atendidas', blank=True)
    ano_fundacao = models.PositiveIntegerField(null=True, blank=True)

    # Quem está pedindo
    nome_responsavel = models.CharField(max_length=100)
    cargo_responsavel = models.CharField(max_length=100, blank=True)
    email_responsavel = models.EmailField()

    # Provas e contexto
    documento = models.FileField(upload_to='solicitacoes_agencia/documentos/', storage=_storage_documento)
    descricao = models.TextField(blank=True, help_text='Por que a agência deveria estar na GlobalBridge.')

    # Fluxo de aprovação
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    motivo_recusa = models.TextField(blank=True)
    agencia_criada = models.OneToOneField(
        'Agencia', on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitacao_origem'
    )
    usuario_criado = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitacao_agencia'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    revisado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Solicitação de agência'
        verbose_name_plural = 'Solicitações de agência'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.nome} ({self.get_status_display()})'
