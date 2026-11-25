"""Garante a existência do schema Postgres isolado (DB_SCHEMA) antes das migrations."""

import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

_SCHEMA_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


class Command(BaseCommand):
    help = 'Verifica ou cria o schema PostgreSQL definido em DB_SCHEMA (ex.: django).'

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('Banco não é PostgreSQL — ensure_schema ignorado.')
            return

        schema = (getattr(settings, 'DB_SCHEMA', '') or '').strip()
        if not schema:
            self.stdout.write('DB_SCHEMA não definido — usando schema padrão.')
            return

        if not _SCHEMA_RE.match(schema):
            raise ValueError(f'DB_SCHEMA inválido: {schema!r}')

        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT 1 FROM information_schema.schemata WHERE schema_name = %s',
                [schema],
            )
            if cursor.fetchone() is None:
                cursor.execute(f'CREATE SCHEMA "{schema}"')
            cursor.execute(f'SET search_path TO "{schema}"')

        self.stdout.write(self.style.SUCCESS(f'Schema PostgreSQL "{schema}" pronto.'))
