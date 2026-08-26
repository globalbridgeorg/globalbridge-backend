"""
Django admin customization.
"""

import logging

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core import models
from core.emails import enviar_pedido_aprovado, enviar_pedido_recusado
from core.models import Estado

logger = logging.getLogger(__name__)


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""

    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name', 'foto')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            },
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
        (_('Groups'), {'fields': ('groups',)}),
        (_('User Permissions'), {'fields': ('user_permissions',)}),
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'password1',
                    'password2',
                    'name',
                    'foto',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                ),
            },
        ),
    )


from core.models import (
    Pais,
    Estado,
    Agencia,
    Avaliacao,
    Plano,
    Programa,
    Tag,
)


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('id',)


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo_iso', 'regiao', 'ativo', 'universidades', 'intercambistas')
    search_fields = ('nome', 'codigo_iso')
    list_filter = ('ativo', 'regiao')
    filter_horizontal = ('tags',)


@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade_principal', 'id_pais')
    search_fields = ('nome', 'cidade_principal')
    list_filter = ('id_pais',)


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


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'duracao_min', 'duracao_max')
    search_fields = ('nome', 'descricao')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'valor', 'label')
    list_filter = ('categoria',)
    search_fields = ('valor', 'label')


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


@admin.register(models.CodigoLogin)
class CodigoLoginAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'codigo', 'criado_em', 'usado')
    list_filter = ('usado',)
    search_fields = ('usuario__email', 'codigo')
    readonly_fields = ('usuario', 'codigo', 'criado_em')


@admin.register(models.SolicitacaoAgencia)
class SolicitacaoAgenciaAdmin(admin.ModelAdmin):
    """O User (tipo=agencia) já existe desde o momento do pedido — quem
    pediu escolheu a própria senha no formulário, pra poder acompanhar o
    status logando normalmente. Aprovar aqui só cria a Agencia de verdade
    e linka nela; não mexe em senha nem em login nenhum. Recusar preenche
    "motivo_recusa" com um texto padrão (edite antes de recusar se quiser
    algo mais específico) e muda o status. Os dois disparam um e-mail
    real pra quem pediu."""

    list_display = ('nome', 'status', 'email_responsavel', 'pais_sede', 'criado_em')
    list_filter = ('status', 'pais_sede')
    search_fields = ('nome', 'email_responsavel', 'nome_responsavel')
    # `status` é readonly de propósito: mudar aqui direto (em vez de usar as
    # ações "Aprovar"/"Recusar") deixava o pedido marcado como aprovado sem
    # nunca criar a Agencia de verdade nem mandar o e-mail — um pedido real
    # ficou preso assim até eu notar e corrigir manualmente.
    readonly_fields = ('status', 'agencia_criada', 'usuario_criado', 'criado_em', 'revisado_em')
    actions = ['aprovar_solicitacoes', 'recusar_solicitacoes']

    @admin.action(description='Aprovar e criar a Agencia')
    def aprovar_solicitacoes(self, request, queryset):
        aprovadas = 0
        ignoradas = 0

        for solicitacao in queryset:
            if solicitacao.status != 'pendente':
                ignoradas += 1
                continue
            if not solicitacao.usuario_criado:
                self.message_user(request, f'{solicitacao.nome}: sem usuário vinculado, pulando (pedido antigo?).', level=messages.ERROR)
                ignoradas += 1
                continue

            estado, _ = Estado.objects.get_or_create(
                cidade_principal=solicitacao.cidade, id_pais=solicitacao.pais_sede,
                defaults={'nome': solicitacao.cidade},
            )

            agencia = models.Agencia.objects.create(
                nome=solicitacao.nome,
                descricao=solicitacao.descricao or f'Agência verificada pela GlobalBridge — {solicitacao.nome}.',
                contato=solicitacao.email_responsavel,
                telefone='',
                site=solicitacao.site,
                endereco=f'{solicitacao.cidade}, {solicitacao.pais_sede.nome}',
                data_cadastro=timezone.now(),
                ativo=True,
                id_estado=estado,
                usuario=solicitacao.usuario_criado,
            )
            paises = set(solicitacao.paises_atendidos.all())
            paises.add(solicitacao.pais_sede)
            agencia.paises_atendidos.set(paises)

            solicitacao.status = 'aprovado'
            solicitacao.agencia_criada = agencia
            solicitacao.revisado_em = timezone.now()
            solicitacao.save()

            aprovadas += 1

            try:
                enviar_pedido_aprovado(solicitacao)
                email_status = f'e-mail de aprovação enviado pra {solicitacao.email_responsavel}'
            except Exception:
                logger.exception('Falha ao enviar e-mail de aprovação para %s', solicitacao.email_responsavel)
                email_status = 'ATENÇÃO: falha ao enviar o e-mail de aprovação, avise por outro canal'

            self.message_user(
                request,
                f'{solicitacao.nome}: agência criada e vinculada a {solicitacao.email_responsavel} — a pessoa já loga com a senha que escolheu no pedido ({email_status}).',
                level=messages.SUCCESS,
            )

        if ignoradas:
            self.message_user(request, f'{ignoradas} solicitação(ões) ignorada(s) por já não estar(em) pendente(s).', level=messages.WARNING)
        if aprovadas:
            self.message_user(request, f'{aprovadas} agência(s) aprovada(s) e criada(s).', level=messages.SUCCESS)

    @admin.action(description='Recusar e notificar por e-mail')
    def recusar_solicitacoes(self, request, queryset):
        recusadas = 0
        ignoradas = 0

        for solicitacao in queryset:
            if solicitacao.status != 'pendente':
                ignoradas += 1
                continue

            if not solicitacao.motivo_recusa:
                solicitacao.motivo_recusa = (
                    'Não conseguimos confirmar as informações enviadas. Entre em '
                    'contato com a gente se quiser mais detalhes.'
                )

            solicitacao.status = 'recusado'
            solicitacao.revisado_em = timezone.now()
            solicitacao.save()
            recusadas += 1

            try:
                enviar_pedido_recusado(solicitacao)
                email_status = f'e-mail enviado pra {solicitacao.email_responsavel}'
            except Exception:
                logger.exception('Falha ao enviar e-mail de recusa para %s', solicitacao.email_responsavel)
                email_status = 'ATENÇÃO: falha ao enviar o e-mail de recusa, avise por outro canal'

            self.message_user(request, f'{solicitacao.nome}: pedido recusado ({email_status}).', level=messages.WARNING)

        if ignoradas:
            self.message_user(request, f'{ignoradas} solicitação(ões) ignorada(s) por já não estar(em) pendente(s).', level=messages.WARNING)
        if recusadas:
            self.message_user(request, f'{recusadas} pedido(s) recusado(s).', level=messages.SUCCESS)