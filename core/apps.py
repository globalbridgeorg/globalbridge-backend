import re

from django.apps import AppConfig
from django.conf import settings
from django.db.backends.signals import connection_created

_SCHEMA_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def _configurar_search_path(sender, connection, **kwargs):
    """Isola as tabelas do Django num schema próprio no Postgres (ex.: `django`)
    quando DB_SCHEMA estiver configurado — evita expor `core_user` e tabelas
    internas do Django no schema `public` do Supabase PostgREST."""
    if connection.vendor != 'postgresql':
        return
    schema = (getattr(settings, 'DB_SCHEMA', '') or '').strip()
    if not schema:
        return
    if not _SCHEMA_RE.match(schema):
        raise ValueError(f'DB_SCHEMA inválido: {schema!r}')
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema}"')


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        connection_created.connect(_configurar_search_path, dispatch_uid='core_set_postgres_search_path')
