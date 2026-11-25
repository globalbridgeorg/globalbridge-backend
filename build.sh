#!/usr/bin/env bash
# Sai do script se houver algum erro
set -o errexit

# Atualiza o pip
pip install --upgrade pip

# Instala as dependências
pip install -r requirements.txt

# Cria o schema isolado no Postgres (se DB_SCHEMA estiver configurado)
python manage.py ensure_schema

# Coleta os arquivos estáticos (Admin + DRF + Swagger)
python manage.py collectstatic --no-input

# Aplica as migrações do Django
python manage.py migrate --no-input

# Popula o catálogo inicial se o banco estiver vazio
python manage.py seed_globalbridge --if-empty
