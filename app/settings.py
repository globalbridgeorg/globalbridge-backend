import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Define o modo de execução da aplicação
MODE = os.getenv('MODE', 'DEVELOPMENT').upper()

# Constrói o caminho base do projeto, usado para definir caminhos relativos
BASE_DIR = Path(__file__).resolve().parent.parent

# Segurança e configuração básica
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS e CORS vêm de variável de ambiente em produção, com
# fallback aberto só em DEBUG (dev local). Em produção no Render, o próprio
# RENDER_EXTERNAL_HOSTNAME é adicionado automaticamente.
_allowed = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]
_render_host = os.getenv('RENDER_EXTERNAL_HOSTNAME', '').strip()
if _render_host and _render_host not in _allowed:
    _allowed.append(_render_host)
ALLOWED_HOSTS = _allowed or (['*'] if DEBUG else [])

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://localhost:8000',
]
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')

_cors = os.getenv('CORS_ALLOWED_ORIGINS', '')
if _cors:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors.split(',') if o.strip()]
    CORS_ALLOW_ALL_ORIGINS = False
    CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS + CORS_ALLOWED_ORIGINS
else:
    # Sem a variável configurada, mantém o comportamento antigo (aberto) pra
    # não derrubar o site antes de você setar os domínios no Render.
    CORS_ALLOW_ALL_ORIGINS = True

# Aplicações instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'corsheaders',
    'django_extensions',
    'django_filters',
    'drf_spectacular',
    'rest_framework',
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

# Banco de dados (SQLite local por padrão; PostgreSQL do Supabase via DATABASE_URL em produção)
DB_SCHEMA = os.getenv('DB_SCHEMA', '').strip()
_database_url = os.getenv('DATABASE_URL', '').strip()
_is_tx_pooler = ':6543' in _database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0 if _is_tx_pooler else 60,
        conn_health_checks=True,
    )
}
if DATABASES['default'].get('ENGINE') == 'django.db.backends.postgresql':
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
    _host = str(DATABASES['default'].get('HOST') or '')
    if 'supabase.' in _host:
        DATABASES['default'].setdefault('OPTIONS', {})
        DATABASES['default']['OPTIONS'].setdefault('sslmode', 'require')

# Validação de senhas
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configurações de internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Configurações de arquivos estáticos
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
WHITENOISE_USE_FINDERS = True

# Configurações de arquivos de mídia (Supabase Storage -> Cloudinary -> Local)
MEDIA_ENDPOINT = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
FILE_UPLOAD_PERMISSIONS = 0o640

SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip().rstrip('/')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')

_staticfiles_storage = (
    'django.contrib.staticfiles.storage.StaticFilesStorage'
    if MODE == 'DEVELOPMENT'
    else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
)

if MODE == 'DEVELOPMENT':
    MY_IP = os.getenv('MY_IP', '127.0.0.1')
    MEDIA_URL = 'http://127.0.0.1:8000/media/'
else:
    MEDIA_URL = '/media/'

if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    STORAGES = {
        'default': {'BACKEND': 'core.storage.SupabaseStorage'},
        'staticfiles': {'BACKEND': _staticfiles_storage},
    }
elif CLOUDINARY_URL:
    STORAGES = {
        'default': {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'},
        'staticfiles': {'BACKEND': _staticfiles_storage},
    }
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': _staticfiles_storage},
    }
    if MODE != 'DEVELOPMENT':
        print('WARNING: SUPABASE_URL/CLOUDINARY_URL não configurados — usando armazenamento local para mídia')

# Configurações de e-mail — 3 modos, na ordem de prioridade abaixo:
# 1. BREVO_API_KEY definida: envia via API transacional do Brevo (core/email_backends.py).
# 2. Sem BREVO_API_KEY mas com EMAIL_HOST definido: SMTP genérico.
# 3. Nenhum dos dois (padrão em DEVELOPMENT): backend de console.
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
REQUIRE_EMAIL_VERIFICATION = os.getenv('REQUIRE_EMAIL_VERIFICATION', 'False') == 'True'
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
if BREVO_API_KEY:
    EMAIL_BACKEND = 'core.email_backends.BrevoAPIBackend'
elif EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'GlobalBridge <no-reply@globalbridge.test>')

# Tipo padrão de campo para chaves primárias
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações do DRF e drf-spectacular (OpenAPI/Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'GlobalBridge API',
    'DESCRIPTION': 'API REST em Django + DRF da plataforma GlobalBridge de intercâmbios e agências verificadas.',
    'VERSION': '1.0.0',
}

# Modelo de usuário personalizado
AUTH_USER_MODEL = 'core.User'

# Configurações do Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticatedOrReadOnly',),
    'DEFAULT_PAGINATION_CLASS': 'app.pagination.CustomPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'PAGE_SIZE': 10,
}

# Configurações do Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=180),  # Tokens de acesso expiram em 3 horas
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # Tokens de atualização expiram em 7 dias
    'AUTH_HEADER_TYPES': ('Bearer',),
}
