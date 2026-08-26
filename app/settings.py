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
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
]
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
    'core',
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

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # React padrão
    "http://127.0.0.1:3000",
    "http://localhost:5173",   # Vite (Vue/React) local dev
    "https://globalbridge-frontend-production-ea1b.up.railway.app",  # Railway production
]

WSGI_APPLICATION = 'app.wsgi.application'

# Banco de dados
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

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
# Sem isso, o WhiteNoise (que já intercepta toda request de /static/ antes
# de qualquer outra coisa, por causa do middleware) só sabe servir o que
# tiver sido coletado em STATIC_ROOT via collectstatic — e no modo
# DEVELOPMENT esse STATIC_ROOT nem existe. Resultado: o CSS/JS do admin do
# Django (e de qualquer outro app) dava 404 e a página carregava sem
# nenhum estilo. Com WHITENOISE_USE_FINDERS, ele passa a servir direto dos
# diretórios estáticos de cada app (o mesmo mecanismo do runserver em
# DEBUG), sem precisar rodar collectstatic — ideal pra dev; em produção
# (MODE != DEVELOPMENT) o STATIC_ROOT normal continua sendo usado.
WHITENOISE_USE_FINDERS = True

# Configurações de arquivos de mídia (App Uploader)
MEDIA_ENDPOINT = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
FILE_UPLOAD_PERMISSIONS = 0o640

# Configurações específicas para desenvolvimento, migração e produção
CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')

if MODE == 'DEVELOPMENT':
    MY_IP = os.getenv('MY_IP', '127.0.0.1')
    MEDIA_URL = 'http://127.0.0.1:8000/media/'
    if CLOUDINARY_URL:
        STORAGES = {
            'default': {
                'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
            },
            'staticfiles': {
                'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
            },
        }
else:
    # Sempre expõe a mesma URL de mídia por padrão
    MEDIA_URL = '/media/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

    # Se CLOUDINARY_URL estiver configurado, usa o storage do Cloudinary para media
    if CLOUDINARY_URL:
        STORAGES = {
            'default': {
                'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
            },
            'staticfiles': {
                'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
            },
        }
    else:
        # Fallback seguro: usa FileSystemStorage para uploads locais quando Cloudinary não estiver configurado
        DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
        STORAGES = {
            'staticfiles': {
                'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
            },
        }
        print('WARNING: CLOUDINARY_URL not set — usando armazenamento local para mídia')

# Configurações de e-mail — 3 modos, na ordem de prioridade abaixo:
# 1. BREVO_API_KEY definida: envia via API transacional do Brevo
#    (core/email_backends.py) — o que este projeto usa em produção.
# 2. Sem BREVO_API_KEY mas com EMAIL_HOST definido: SMTP genérico —
#    funciona com qualquer provedor compatível (Gmail com senha de app,
#    SendGrid, SES etc), útil se um dia trocar de provedor.
# 3. Nenhum dos dois (padrão em DEVELOPMENT): backend de console — só
#    imprime o e-mail no terminal, não envia de verdade.
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
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
    'TITLE': '<PROJETO> API',
    'DESCRIPTION': 'API para o projeto <descreva aqui seu projeto>.',
    'VERSION': '1.0.0',
}

# Modelo de usuário personalizado
AUTH_USER_MODEL = 'core.User'

# Configurações do Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PAGINATION_CLASS': 'app.pagination.CustomPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'PAGE_SIZE': 10,
}

# Configurações do Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=180),  # Tokens de acesso expiram em 3 horas
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),  # Tokens de atualização expiram em 1 dia
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Exibe as configurações principais para verificação
print(f'{MODE = } \n{MEDIA_URL = } \n{DATABASES = }')
