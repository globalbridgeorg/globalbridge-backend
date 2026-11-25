"""Admin do catálogo: países, estados, programas, tags e mensagens de contato."""

from django.contrib import admin

from core.models import Estado, MensagemContato, Pais, Programa, Tag


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


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'duracao_min', 'duracao_max')
    search_fields = ('nome', 'descricao')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'valor', 'label')
    list_filter = ('categoria',)
    search_fields = ('valor', 'label')


@admin.register(MensagemContato)
class MensagemContatoAdmin(admin.ModelAdmin):
    list_display = ('assunto', 'nome', 'email', 'publico', 'lida', 'criado_em')
    list_filter = ('lida', 'publico')
    search_fields = ('nome', 'email', 'assunto', 'mensagem', 'nome_agencia')
    readonly_fields = ('criado_em',)
