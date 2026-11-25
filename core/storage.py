"""Storage backend do Django apontando para o Supabase Storage via REST API.

Reaproveita os buckets já existentes no projeto Supabase:
- `avatars` (público): avatares e fotos de perfil (`avatars/`, `perfil/`)
- `agencias` (público): capas e galerias de agências (`agencias/`)
- `documentos-agencia` (privado): comprovantes enviados em solicitações (`solicitacoes_agencia/`)

Usa `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` exclusivamente no servidor
(nunca expostos no frontend). URLs externas (`http://` ou `https://`) já salvas
no banco (ex.: imagens verificadas do catálogo inicial) são devolvidas direto
sem tentar reescrevê-las.
"""

import mimetypes
import os
import posixpath
import re
import uuid
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

PRIVATE_BUCKETS = {'documentos-agencia'}
_SAFE_FILENAME_RE = re.compile(r'[^a-zA-Z0-9._-]+')


def supabase_storage_ativo():
    return bool(getattr(settings, 'SUPABASE_URL', '') and getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', ''))


def resolver_bucket_e_objeto(name):
    """Mapeia o caminho relativo do Django (`upload_to`) para (bucket, object_path)."""
    clean = str(name or '').replace('\\', '/').lstrip('/')
    if clean.startswith('avatars/'):
        return 'avatars', clean[len('avatars/'):]
    if clean.startswith('perfil/'):
        return 'avatars', clean
    if clean.startswith('agencias/'):
        return 'agencias', clean[len('agencias/'):]
    if clean.startswith('solicitacoes_agencia/'):
        return 'documentos-agencia', clean[len('solicitacoes_agencia/'):]
    if clean.startswith('documentos-agencia/'):
        return 'documentos-agencia', clean[len('documentos-agencia/'):]
    return 'agencias', clean


def url_para_campo_arquivo(file_field, request=None):
    """Resolve a URL final de um ImageField/FileField, preservando URLs externas."""
    if not file_field:
        return None
    file_value = getattr(file_field, 'name', file_field)
    if isinstance(file_value, str) and (file_value.startswith('http://') or file_value.startswith('https://')):
        return file_value
    if hasattr(file_field, 'url'):
        url = file_field.url
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if request is not None:
            return request.build_absolute_uri(url)
        return url
    return file_value


def criar_url_assinada_supabase(bucket, object_path, expires_in=300):
    """Gera URL assinada temporária para objetos em buckets privados do Supabase."""
    base_url = getattr(settings, 'SUPABASE_URL', '').rstrip('/')
    service_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '')
    if not base_url or not service_key:
        raise RuntimeError('SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY não configurados.')

    encoded_path = quote(object_path.lstrip('/'), safe='/')
    endpoint = f'{base_url}/storage/v1/object/sign/{bucket}/{encoded_path}'
    resp = requests.post(
        endpoint,
        headers={
            'Authorization': f'Bearer {service_key}',
            'apikey': service_key,
            'Content-Type': 'application/json',
        },
        json={'expiresIn': int(expires_in)},
        timeout=15,
    )
    if not resp.ok:
        raise RuntimeError(f'Erro ao assinar URL no Supabase Storage ({resp.status_code}): {resp.text}')

    data = resp.json()
    signed = data.get('signedURL') or data.get('signedUrl') or ''
    if signed.startswith('http://') or signed.startswith('https://'):
        return signed
    if signed.startswith('/storage/v1/'):
        return f'{base_url}{signed}'
    return f'{base_url}/storage/v1{signed}'


@deconstructible
class SupabaseStorage(Storage):
    """Django Storage backend usando a API REST oficial do Supabase Storage."""

    def __init__(self, bucket=None):
        self.default_bucket = bucket

    @property
    def base_url(self):
        return getattr(settings, 'SUPABASE_URL', '').rstrip('/')

    @property
    def service_key(self):
        return getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '')

    def _headers(self, extra=None):
        headers = {
            'Authorization': f'Bearer {self.service_key}',
            'apikey': self.service_key,
        }
        if extra:
            headers.update(extra)
        return headers

    def _bucket_e_caminho(self, name):
        if self.default_bucket:
            clean = str(name or '').replace('\\', '/').lstrip('/')
            return self.default_bucket, clean
        return resolver_bucket_e_objeto(name)

    def _limpar_nome(self, name):
        clean = str(name or '').replace('\\', '/').lstrip('/')
        diretorio, arquivo = posixpath.split(clean)
        stem, ext = os.path.splitext(arquivo)
        stem_seguro = _SAFE_FILENAME_RE.sub('-', stem).strip('-') or 'arquivo'
        ext_segura = _SAFE_FILENAME_RE.sub('', ext.lower())[:12]
        unico = f'{uuid.uuid4().hex[:12]}-{stem_seguro[:60]}{ext_segura}'
        return posixpath.join(diretorio, unico) if diretorio else unico

    def _save(self, name, content):
        if not self.base_url or not self.service_key:
            raise RuntimeError('SupabaseStorage ativo sem SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY.')

        final_name = self._limpar_nome(name)
        bucket, object_path = self._bucket_e_caminho(final_name)
        encoded_path = quote(object_path, safe='/')

        content.seek(0)
        raw_bytes = content.read()
        content_type = (
            getattr(content, 'content_type', None)
            or mimetypes.guess_type(final_name)[0]
            or 'application/octet-stream'
        )

        endpoint = f'{self.base_url}/storage/v1/object/{bucket}/{encoded_path}'
        resp = requests.post(
            endpoint,
            headers=self._headers({'Content-Type': content_type, 'x-upsert': 'true'}),
            data=raw_bytes,
            timeout=30,
        )
        if not resp.ok:
            raise RuntimeError(f'Falha no upload para Supabase Storage ({resp.status_code}): {resp.text}')

        return final_name

    def _open(self, name, mode='rb'):
        if str(name).startswith(('http://', 'https://')):
            resp = requests.get(name, timeout=20)
            resp.raise_for_status()
            return ContentFile(resp.content, name=name)

        bucket, object_path = self._bucket_e_caminho(name)
        encoded_path = quote(object_path, safe='/')
        endpoint = f'{self.base_url}/storage/v1/object/authenticated/{bucket}/{encoded_path}'
        resp = requests.get(endpoint, headers=self._headers(), timeout=20)
        resp.raise_for_status()
        return ContentFile(resp.content, name=name)

    def delete(self, name):
        if not name or str(name).startswith(('http://', 'https://')):
            return
        if not self.base_url or not self.service_key:
            return
        bucket, object_path = self._bucket_e_caminho(name)
        endpoint = f'{self.base_url}/storage/v1/object/{bucket}'
        requests.delete(
            endpoint,
            headers=self._headers({'Content-Type': 'application/json'}),
            json={'prefixes': [object_path]},
            timeout=15,
        )

    def exists(self, name):
        # Cada arquivo recebe prefixo UUID em _save(), evitando roundtrip extra.
        return False

    def url(self, name):
        if not name:
            return ''
        if str(name).startswith(('http://', 'https://')):
            return str(name)
        bucket, object_path = self._bucket_e_caminho(name)
        if bucket in PRIVATE_BUCKETS:
            try:
                return criar_url_assinada_supabase(bucket, object_path, expires_in=300)
            except Exception:
                return ''
        encoded_path = quote(object_path, safe='/')
        return f'{self.base_url}/storage/v1/object/public/{bucket}/{encoded_path}'
