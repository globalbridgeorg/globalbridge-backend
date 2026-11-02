"""Admin de agências e do que pertence a elas (avaliações, planos, favoritos, galeria, países adicionais)."""

from django.contrib import admin, messages
from django.utils import timezone

from core import models
from core.models import Agencia, Avaliacao, Plano


@admin.register(Agencia)
class AgenciaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'id_estado', 'telefone', 'site', 'ativo')
    search_fields = ('nome', 'contato', 'telefone')
    list_filter = ('ativo', 'id_estado__id_pais')
    filter_horizontal = ('tags',)


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_usuario', 'id_agencia', 'nota')
    list_filter = ('nota',)


@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_agencia', 'id_programa', 'preco')
    search_fields = ('descricao',)
    list_filter = ('id_agencia', 'id_programa')


@admin.register(models.Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'tipo', 'objeto_id', 'criado_em')
    list_filter = ('tipo',)


@admin.register(models.ImagemGaleria)
class ImagemGaleriaAdmin(admin.ModelAdmin):
    list_display = ('agencia', 'ordem')
    list_filter = ('agencia',)


@admin.register(models.SolicitacaoPaisAdicional)
class SolicitacaoPaisAdicionalAdmin(admin.ModelAdmin):
    list_display = ('agencia', 'pais', 'status', 'criado_em')
    list_filter = ('status', 'pais')
    search_fields = ('agencia__nome',)
    readonly_fields = ('status', 'agencia', 'pais', 'criado_em', 'revisado_em')
    actions = ['aprovar_paises', 'recusar_paises']

    @admin.action(description='Aprovar e adicionar o país à agência')
    def aprovar_paises(self, request, queryset):
        aprovados = 0
        for solicitacao in queryset.filter(status='pendente'):
            solicitacao.agencia.paises_atendidos.add(solicitacao.pais)
            solicitacao.status = 'aprovado'
            solicitacao.revisado_em = timezone.now()
            solicitacao.save()
            aprovados += 1
        if aprovados:
            self.message_user(request, f'{aprovados} país(es) adicionado(s) à(s) agência(s).', level=messages.SUCCESS)

    @admin.action(description='Recusar pedido')
    def recusar_paises(self, request, queryset):
        recusados = 0
        for solicitacao in queryset.filter(status='pendente'):
            solicitacao.status = 'recusado'
            solicitacao.revisado_em = timezone.now()
            solicitacao.save()
            recusados += 1
        if recusados:
            self.message_user(request, f'{recusados} pedido(s) recusado(s).', level=messages.WARNING)
