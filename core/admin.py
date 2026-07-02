"""
Django admin customization.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models


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
)


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('id',)


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo_iso', 'ativo', 'universidades', 'intercambistas')
    search_fields = ('nome', 'codigo_iso')
    list_filter = ('ativo',)


@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade_principal', 'id_pais')
    search_fields = ('nome', 'cidade_principal')
    list_filter = ('id_pais',)


@admin.register(Agencia)
class AgenciaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'site', 'ativo')
    search_fields = ('nome', 'contato', 'telefone')
    list_filter = ('ativo',)


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