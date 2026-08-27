"""
Django admin customization.
"""

import logging

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Case, IntegerField, Value, When
from django.http import HttpResponseNotAllowed
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
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


@admin.register(models.CodigoVerificacaoEmail)
class CodigoVerificacaoEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'codigo', 'criado_em', 'verificado')
    list_filter = ('verificado',)
    search_fields = ('email', 'codigo')
    readonly_fields = ('email', 'codigo', 'criado_em', 'usado', 'verificado', 'verificado_em')


def _aprovar_uma_solicitacao(solicitacao):
    """Aprova uma única solicitação pendente: cria a Agencia de verdade e
    linka nela. Retorna (ok, mensagem, nível) pra quem chamou (ação em
    massa ou botão de linha única) decidir como exibir."""
    if solicitacao.status != 'pendente':
        return False, f'{solicitacao.nome}: já não está mais pendente.', messages.WARNING
    if not solicitacao.usuario_criado:
        return False, f'{solicitacao.nome}: sem usuário vinculado, pulando (pedido antigo?).', messages.ERROR

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

    try:
        enviar_pedido_aprovado(solicitacao)
        email_status = f'e-mail de aprovação enviado pra {solicitacao.email_responsavel}'
    except Exception:
        logger.exception('Falha ao enviar e-mail de aprovação para %s', solicitacao.email_responsavel)
        email_status = 'ATENÇÃO: falha ao enviar o e-mail de aprovação, avise por outro canal'

    return True, (
        f'{solicitacao.nome}: agência criada e vinculada a {solicitacao.email_responsavel} — '
        f'a pessoa já loga com a senha que escolheu no pedido ({email_status}).'
    ), messages.SUCCESS


def _recusar_uma_solicitacao(solicitacao):
    """Recusa uma única solicitação pendente. Retorna (ok, mensagem, nível)."""
    if solicitacao.status != 'pendente':
        return False, f'{solicitacao.nome}: já não está mais pendente.', messages.WARNING

    if not solicitacao.motivo_recusa:
        solicitacao.motivo_recusa = (
            'Não conseguimos confirmar as informações enviadas. Entre em '
            'contato com a gente se quiser mais detalhes.'
        )

    solicitacao.status = 'recusado'
    solicitacao.revisado_em = timezone.now()
    solicitacao.save()

    try:
        enviar_pedido_recusado(solicitacao)
        email_status = f'e-mail enviado pra {solicitacao.email_responsavel}'
    except Exception:
        logger.exception('Falha ao enviar e-mail de recusa para %s', solicitacao.email_responsavel)
        email_status = 'ATENÇÃO: falha ao enviar o e-mail de recusa, avise por outro canal'

    return True, f'{solicitacao.nome}: pedido recusado ({email_status}).', messages.SUCCESS


_STATUS_CORES = {
    'pendente': ('#8a6100', '#fff3cd'),
    'aprovado': ('#1e6b32', '#d9f2e0'),
    'recusado': ('#8a1f1f', '#fbdada'),
}


@admin.register(models.SolicitacaoAgencia)
class SolicitacaoAgenciaAdmin(admin.ModelAdmin):
    """O User (tipo=agencia) já existe desde o momento do pedido — quem
    pediu escolheu a própria senha no formulário, pra poder acompanhar o
    status logando normalmente. Aprovar aqui só cria a Agencia de verdade
    e linka nela; não mexe em senha nem em login nenhum. Recusar preenche
    "motivo_recusa" com um texto padrão (edite antes de recusar se quiser
    algo mais específico) e muda o status. Os dois disparam um e-mail
    real pra quem pediu.

    Além das ações em massa (selecionar + escolher ação no dropdown, que
    continuam funcionando), a lista mostra um selo colorido de status, uma
    prévia do documento enviado e botões de Aprovar/Recusar por linha —
    pra revisar um pedido sem precisar abrir o detalhe nem usar o dropdown."""

    list_display = ('nome', 'status_badge', 'documento_preview', 'email_responsavel', 'pais_sede', 'criado_em', 'acoes_rapidas')
    list_filter = ('status', 'pais_sede')
    search_fields = ('nome', 'email_responsavel', 'nome_responsavel')
    fieldsets = (
        ('Revisão', {'fields': ('status', 'documento_preview_grande', 'descricao')}),
        ('Sobre a agência', {'fields': ('nome', 'site', 'cidade', 'pais_sede', 'paises_atendidos', 'ano_fundacao')}),
        ('Quem está pedindo', {'fields': ('nome_responsavel', 'cargo_responsavel', 'email_responsavel')}),
        ('Documento original', {'fields': ('documento',)}),
        ('Resultado da análise', {'fields': ('motivo_recusa', 'agencia_criada', 'usuario_criado', 'criado_em', 'revisado_em')}),
    )
    # `status` é readonly de propósito: mudar aqui direto (em vez de usar as
    # ações "Aprovar"/"Recusar") deixava o pedido marcado como aprovado sem
    # nunca criar a Agencia de verdade nem mandar o e-mail — um pedido real
    # ficou preso assim até eu notar e corrigir manualmente.
    readonly_fields = (
        'status', 'documento_preview_grande', 'agencia_criada', 'usuario_criado', 'criado_em', 'revisado_em',
    )
    actions = ['aprovar_solicitacoes', 'recusar_solicitacoes']

    def get_queryset(self, request):
        # Pendentes primeiro (é o que precisa de atenção), mais recentes
        # dentro de cada grupo de status.
        qs = super().get_queryset(request)
        return qs.annotate(
            _ordem_status=Case(When(status='pendente', then=Value(0)), default=Value(1), output_field=IntegerField())
        ).order_by('_ordem_status', '-criado_em')

    def status_badge(self, obj):
        cor_texto, cor_fundo = _STATUS_CORES.get(obj.status, ('#444', '#eee'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; border-radius:12px; '
            'font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.04em;">{}</span>',
            cor_fundo, cor_texto, obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def _preview_documento(self, obj, altura):
        if not obj.documento:
            return '—'
        url = obj.documento.url
        extensao = url.rsplit('.', 1)[-1].lower().split('?')[0]
        if extensao in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">'
                '<img src="{}" style="height:{}px; border-radius:6px; border:1px solid #ddd; display:block;" />'
                '</a>', url, url, altura,
            )
        return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">📄 Abrir documento</a>', url)

    def documento_preview(self, obj):
        return self._preview_documento(obj, altura=40)
    documento_preview.short_description = 'Documento'

    def documento_preview_grande(self, obj):
        return self._preview_documento(obj, altura=280)
    documento_preview_grande.short_description = 'Documento enviado'

    def acoes_rapidas(self, obj):
        if obj.status != 'pendente':
            return '—'
        # Nada de <form> aqui: a linha já vive dentro do <form id="changelist-form">
        # do próprio Django admin (é o que faz a seleção em massa funcionar), e
        # HTML não permite form aninhado — o navegador simplesmente descarta a
        # tag de abertura de um <form> dentro de outro. Por isso o clique vira
        # um fetch() direto pro endpoint, com o token CSRF no header.
        request = getattr(self, '_request_atual', None)
        csrf_token = get_token(request) if request else ''
        url_aprovar = reverse('admin:core_solicitacaoagencia_aprovar_rapido', args=[obj.pk])
        url_recusar = reverse('admin:core_solicitacaoagencia_recusar_rapido', args=[obj.pk])

        def fazer_post(url):
            return (
                "fetch('%s', {method: 'POST', headers: {'X-CSRFToken': '%s'}}).then(function () { location.reload(); });"
                % (url, csrf_token)
            )

        onclick_aprovar = fazer_post(url_aprovar)
        onclick_recusar = "if (confirm('Recusar esse pedido?')) { %s }" % fazer_post(url_recusar)

        return format_html(
            '<div style="display:flex; gap:6px;">'
            '<button type="button" onclick="{}" style="background:#1e6b32; color:#fff; border:none; '
            'border-radius:5px; padding:5px 12px; cursor:pointer; font-size:12px; font-weight:600;">Aprovar</button>'
            '<button type="button" onclick="{}" style="background:#8a1f1f; color:#fff; border:none; '
            'border-radius:5px; padding:5px 12px; cursor:pointer; font-size:12px; font-weight:600;">Recusar</button>'
            '</div>',
            onclick_aprovar, onclick_recusar,
        )
    acoes_rapidas.short_description = 'Ação rápida'

    def changelist_view(self, request, extra_context=None):
        # Guardado só pra `acoes_rapidas` conseguir montar a URL/CSRF de
        # cada botão — list_display não recebe `request` diretamente.
        self._request_atual = request
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = [
            path('<int:solicitacao_id>/aprovar-rapido/', self.admin_site.admin_view(self._aprovar_rapido), name='core_solicitacaoagencia_aprovar_rapido'),
            path('<int:solicitacao_id>/recusar-rapido/', self.admin_site.admin_view(self._recusar_rapido), name='core_solicitacaoagencia_recusar_rapido'),
        ]
        return urls + super().get_urls()

    def _aprovar_rapido(self, request, solicitacao_id):
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        solicitacao = get_object_or_404(models.SolicitacaoAgencia, pk=solicitacao_id)
        ok, mensagem, nivel = _aprovar_uma_solicitacao(solicitacao)
        self.message_user(request, mensagem, level=nivel)
        return redirect('admin:core_solicitacaoagencia_changelist')

    def _recusar_rapido(self, request, solicitacao_id):
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        solicitacao = get_object_or_404(models.SolicitacaoAgencia, pk=solicitacao_id)
        ok, mensagem, nivel = _recusar_uma_solicitacao(solicitacao)
        self.message_user(request, mensagem, level=nivel)
        return redirect('admin:core_solicitacaoagencia_changelist')

    @admin.action(description='Aprovar e criar a Agencia')
    def aprovar_solicitacoes(self, request, queryset):
        aprovadas = 0
        ignoradas = 0
        for solicitacao in queryset:
            ok, mensagem, nivel = _aprovar_uma_solicitacao(solicitacao)
            self.message_user(request, mensagem, level=nivel)
            if ok:
                aprovadas += 1
            else:
                ignoradas += 1

        if ignoradas:
            self.message_user(request, f'{ignoradas} solicitação(ões) ignorada(s) por já não estar(em) pendente(s).', level=messages.WARNING)
        if aprovadas:
            self.message_user(request, f'{aprovadas} agência(s) aprovada(s) e criada(s).', level=messages.SUCCESS)

    @admin.action(description='Recusar e notificar por e-mail')
    def recusar_solicitacoes(self, request, queryset):
        recusadas = 0
        ignoradas = 0
        for solicitacao in queryset:
            ok, mensagem, nivel = _recusar_uma_solicitacao(solicitacao)
            self.message_user(request, mensagem, level=nivel)
            if ok:
                recusadas += 1
            else:
                ignoradas += 1

        if ignoradas:
            self.message_user(request, f'{ignoradas} solicitação(ões) ignorada(s) por já não estar(em) pendente(s).', level=messages.WARNING)
        if recusadas:
            self.message_user(request, f'{recusadas} pedido(s) recusado(s).', level=messages.SUCCESS)