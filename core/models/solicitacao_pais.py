from django.db import models


class SolicitacaoPaisAdicional(models.Model):
    """Pedido de uma agência JÁ aprovada pra passar a atender mais um
    país. Mesma lógica de confiança do cadastro inicial — fica pendente
    até o time aprovar, que aí sim adiciona o país em
    Agencia.paises_atendidos (ver SolicitacaoPaisAdicionalAdmin)."""

    STATUS_CHOICES = [('pendente', 'Pendente'), ('aprovado', 'Aprovado'), ('recusado', 'Recusado')]

    agencia = models.ForeignKey('Agencia', on_delete=models.CASCADE, related_name='solicitacoes_pais')
    pais = models.ForeignKey('Pais', on_delete=models.PROTECT, related_name='solicitacoes_adicionais')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    motivo_recusa = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    revisado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Solicitação de país adicional'
        verbose_name_plural = 'Solicitações de país adicional'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.agencia.nome} -> {self.pais.nome} ({self.status})'
