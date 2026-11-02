"""Admin de usuários e códigos de login/verificação de e-mail."""

from django.contrib import admin

from core import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('id',)



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

