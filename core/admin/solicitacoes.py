"""Admin dos pedidos de verificação de agência (SolicitacaoAgencia)."""

from django.contrib import admin, messages
from django.db.models import Case, IntegerField, Value, When
from django.http import HttpResponseNotAllowed
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.html import format_html

from core import models

from .solicitacoes_acoes import _aprovar_uma_solicitacao, _recusar_uma_solicitacao


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