"""Popula o banco do Django com o catálogo completo da GlobalBridge.

Inclui:
- 23 países, 23 estados/cidades, 25 tags e 11 programas
- 26 agências ativas + 1 agência demo oculta (#51 Bridgeway Intercâmbios)
  com capas verificadas, layouts únicos, galerias (76 fotos) e retratos de equipe
- Estudantes reais e 88 avaliações (alimentando "Quem já foi" na home)
- Conta demo admin/business: demo@globalbridge.com / GlobalBridge2026!

Uso:
  python manage.py seed_globalbridge            # cria/atualiza catálogo completo
  python manage.py seed_globalbridge --if-empty # só executa se o banco ainda não tiver países
"""

import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from core.models import (
    Agencia,
    Avaliacao,
    Estado,
    ImagemGaleria,
    Pais,
    Plano,
    Programa,
    Tag,
    User,
)

FIXTURE_PATH = Path(__file__).resolve().parents[2] / 'fixtures' / 'globalbridge_seed.json'

DEMO_EMAIL = 'demo@globalbridge.com'
DEMO_SENHA = 'GlobalBridge2026!'
DEMO_AGENCIA = {
    'id': 51,
    'nome': 'Bridgeway Intercâmbios (Demo)',
    'descricao': (
        'Agência modelo da área GlobalBridge Business: programas personalizados em Londres, '
        'Dublin e Toronto com mentoria completa de visto, moradia e carreira internacional.'
    ),
    'como_funciona': (
        '1. Agende uma conversa rápida para definirmos seu perfil e orçamento.\n'
        '2. Escolhemos juntos escola, cidade e acomodação sob medida.\n'
        '3. Nossa equipe cuida da matrícula, visto, seguro e embarque com suporte 24h.'
    ),
    'contato': 'demo@globalbridge.com',
    'telefone': '+55 11 98765-4321',
    'site': 'https://globalbridge-gamma.vercel.app',
    'endereco': 'Regent Street, 140 — Londres, Reino Unido',
    'ativo': False,
    'imagem_capa': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Regent_Street_2011-04-25.jpg/1280px-Regent_Street_2011-04-25.jpg',
    'imagem_capa_foco_x': 50,
    'imagem_capa_foco_y': 48,
    'layout': [
        {'tipo': 'hero', 'variante': 'banner'},
        {'tipo': 'como_funciona', 'variante': 'destaque'},
        {'tipo': 'galeria'},
        {'tipo': 'catalogo', 'variante': 'grade'},
        {'tipo': 'equipe'},
        {'tipo': 'certificacoes'},
        {'tipo': 'faq'},
        {'tipo': 'avaliacoes', 'variante': 'grade'},
        {'tipo': 'contato_whatsapp'},
    ],
    'conteudo_blocos': {
        'equipe': {
            'membros': [
                {
                    'nome': 'Beatriz Nogueira',
                    'cargo': 'Consultora de Intercâmbio',
                    'foto': 'https://randomuser.me/api/portraits/women/62.jpg',
                },
                {
                    'nome': 'Lucas Ferreira',
                    'cargo': 'Especialista em Vistos UK',
                    'foto': 'https://randomuser.me/api/portraits/men/63.jpg',
                },
                {
                    'nome': 'Sofia Mendes',
                    'cargo': 'Apoio ao Estudante em Londres',
                    'foto': 'https://randomuser.me/api/portraits/women/64.jpg',
                },
            ]
        },
        'certificacoes': {
            'itens': [
                {
                    'nome': 'Selo Parceira Verificada',
                    'descricao': 'Agência modelo de demonstração da área GlobalBridge Business.',
                },
                {
                    'nome': 'Suporte Bilíngue Completo',
                    'descricao': 'Atendimento em português antes, durante e após o embarque.',
                },
            ]
        },
        'faq': {
            'perguntas': [
                {
                    'pergunta': 'Posso personalizar todas essas seções na área Business?',
                    'resposta': (
                        'Sim! No editor de página você reordena blocos, troca variantes, '
                        'ajusta o foco da capa e adiciona fotos na galeria.'
                    ),
                }
            ]
        },
        'contato_whatsapp': {
            'numero': '+55 11 98765 4321',
            'mensagem': 'Olá Bridgeway! Testando o botão de WhatsApp na demonstração GlobalBridge.',
        },
    },
    'galeria': [
        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Thames_Panorama%2C_London_-_June_2009.jpg/1280px-Thames_Panorama%2C_London_-_June_2009.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Radcliffe_Camera%2C_Oxford.jpg/1280px-Radcliffe_Camera%2C_Oxford.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/King%27s_College_Chapel%2C_Cambridge.jpg/1280px-King%27s_College_Chapel%2C_Cambridge.jpg',
    ],
}


class Command(BaseCommand):
    help = 'Popula o banco de dados do Django com o catálogo enriquecido do GlobalBridge.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--if-empty',
            action='store_true',
            help='Só popula se ainda não houver países cadastrados (ideal para build.sh).',
        )

    def handle(self, *args, **options):
        if options['if_empty'] and Pais.objects.exists():
            self.stdout.write('Catálogo já populado (--if-empty) — nada a fazer.')
            return

        if not FIXTURE_PATH.exists():
            raise FileNotFoundError(f'Fixture não encontrada: {FIXTURE_PATH}')

        data = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))

        with transaction.atomic():
            # 1. Países
            for p in data['paises']:
                Pais.objects.update_or_create(
                    id=p['id'],
                    defaults={
                        'nome': p['nome'],
                        'nome_ingles': p.get('nome_ingles') or '',
                        'codigo_iso': p['codigo_iso'],
                        'regiao': p.get('regiao') or '',
                        'custo_de_vida': p['custo_de_vida'],
                        'idioma': p['idioma'],
                        'cultura': p['cultura'],
                        'descricao': p['descricao'],
                        'imagem_url': p['imagem_url'],
                        'intercambistas': p.get('intercambistas') or 0,
                        'universidades': p.get('universidades') or 0,
                        'ativo': p.get('ativo', True),
                    },
                )

            # 2. Estados
            for e in data['estados']:
                Estado.objects.update_or_create(
                    id=e['id'],
                    defaults={
                        'nome': e['nome'],
                        'cidade_principal': e['cidade_principal'],
                        'id_pais_id': e['pais_id'],
                    },
                )

            # 3. Tags + pais_tags
            for t in data['tags']:
                Tag.objects.update_or_create(
                    id=t['id'],
                    defaults={
                        'categoria': t['categoria'],
                        'valor': t['valor'],
                        'label': t.get('label') or '',
                    },
                )
            pais_tags_map = {}
            for rel in data['pais_tags']:
                pais_tags_map.setdefault(rel['pais_id'], []).append(rel['tag_id'])
            for pais_id, tag_ids in pais_tags_map.items():
                pais_obj = Pais.objects.filter(id=pais_id).first()
                if pais_obj:
                    pais_obj.tags.set(tag_ids)

            # 4. Programas
            for pr in data['programas']:
                Programa.objects.update_or_create(
                    id=pr['id'],
                    defaults={
                        'nome': pr['nome'],
                        'descricao': pr['descricao'],
                        'duracao_min': pr['duracao_min'],
                        'duracao_max': pr['duracao_max'],
                    },
                )

            # 5. Usuários estudantes (profiles)
            profile_uuid_to_user = {}
            for prof in data['profiles']:
                username = (prof.get('username') or '').strip()
                if not username or prof.get('tipo') == 'agencia':
                    continue
                email = f'{username}@estudantes.globalbridge.demo'
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'name': prof.get('name') or username,
                        'tipo': 'estudante',
                        'is_active': True,
                    },
                )
                changed = []
                if prof.get('name') and user.name != prof['name']:
                    user.name = prof['name']
                    changed.append('name')
                avatar_url = prof.get('avatar_url') or ''
                if avatar_url and str(user.avatar) != avatar_url:
                    user.avatar = avatar_url
                    changed.append('avatar')
                if created:
                    user.set_unusable_password()
                    changed.append('password')
                if changed:
                    user.save(update_fields=changed)
                profile_uuid_to_user[prof['id']] = user

            # 6. Agências ativas
            for ag in data['agencias']:
                dt = parse_datetime(ag.get('data_cadastro') or '') or timezone.now()
                ag_obj, _ = Agencia.objects.update_or_create(
                    id=ag['id'],
                    defaults={
                        'nome': ag['nome'],
                        'descricao': ag['descricao'],
                        'como_funciona': ag.get('como_funciona') or '',
                        'contato': ag.get('contato') or '',
                        'telefone': ag.get('telefone') or '',
                        'site': ag.get('site') or '',
                        'endereco': ag.get('endereco') or '',
                        'data_cadastro': dt,
                        'ativo': ag.get('ativo', True),
                        'id_estado_id': ag.get('estado_id'),
                        'layout': ag.get('layout') or [],
                        'imagem_capa': ag.get('imagem_capa_url') or None,
                        'imagem_capa_foco_x': ag.get('imagem_capa_foco_x', 50),
                        'imagem_capa_foco_y': ag.get('imagem_capa_foco_y', 50),
                        'conteudo_blocos': ag.get('conteudo_blocos') or {},
                    },
                )

            ag_tags_map = {}
            for rel in data['agencia_tags']:
                ag_tags_map.setdefault(rel['agencia_id'], []).append(rel['tag_id'])
            for ag_id, tag_ids in ag_tags_map.items():
                ag_obj = Agencia.objects.filter(id=ag_id).first()
                if ag_obj:
                    ag_obj.tags.set(tag_ids)

            ag_paises_map = {}
            for rel in data['agencia_paises_atendidos']:
                ag_paises_map.setdefault(rel['agencia_id'], []).append(rel['pais_id'])
            for ag_id, pais_ids in ag_paises_map.items():
                ag_obj = Agencia.objects.filter(id=ag_id).first()
                if ag_obj:
                    ag_obj.paises_atendidos.set(pais_ids)

            # 7. Planos
            for pl in data['planos']:
                if not Agencia.objects.filter(id=pl['agencia_id']).exists():
                    continue
                Plano.objects.update_or_create(
                    id=pl['id'],
                    defaults={
                        'id_agencia_id': pl['agencia_id'],
                        'id_programa_id': pl['programa_id'],
                        'preco': Decimal(str(pl['preco'])),
                        'descricao': pl.get('descricao') or '',
                        'inclui': pl.get('inclui') or '',
                    },
                )

            # 8. Galeria de fotos
            for img in data['imagens_galeria']:
                if not Agencia.objects.filter(id=img['agencia_id']).exists():
                    continue
                url = img.get('url') or ''
                if not url:
                    continue
                if not ImagemGaleria.objects.filter(agencia_id=img['agencia_id'], imagem=url).exists():
                    ImagemGaleria.objects.create(
                        agencia_id=img['agencia_id'],
                        imagem=url,
                        ordem=img.get('ordem', 0),
                    )

            # 9. Avaliações
            for av in data['avaliacoes']:
                usuario = profile_uuid_to_user.get(av.get('usuario_id'))
                if not usuario or not Agencia.objects.filter(id=av['agencia_id']).exists():
                    continue
                Avaliacao.objects.update_or_create(
                    id_usuario=usuario,
                    id_agencia_id=av['agencia_id'],
                    defaults={
                        'nota': av['nota'],
                        'comentario': av.get('comentario') or '',
                    },
                )

            # 10. Conta demo admin/business + agência demo #51 (oculta no catálogo público)
            demo_user, created = User.objects.get_or_create(
                email=DEMO_EMAIL,
                defaults={
                    'username': 'bridgeway-demo',
                    'name': 'Filipe (Demo Agência)',
                    'tipo': 'agencia',
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True,
                },
            )
            demo_user.tipo = 'agencia'
            demo_user.is_staff = True
            demo_user.is_superuser = True
            demo_user.set_password(DEMO_SENHA)
            demo_user.save()

            estado_sede = (
                Estado.objects.filter(cidade_principal__icontains='Londres').first()
                or Estado.objects.first()
            )
            demo_ag, _ = Agencia.objects.update_or_create(
                id=DEMO_AGENCIA['id'],
                defaults={
                    'nome': DEMO_AGENCIA['nome'],
                    'descricao': DEMO_AGENCIA['descricao'],
                    'como_funciona': DEMO_AGENCIA['como_funciona'],
                    'contato': DEMO_AGENCIA['contato'],
                    'telefone': DEMO_AGENCIA['telefone'],
                    'site': DEMO_AGENCIA['site'],
                    'endereco': DEMO_AGENCIA['endereco'],
                    'data_cadastro': timezone.now(),
                    'ativo': DEMO_AGENCIA['ativo'],
                    'id_estado': estado_sede,
                    'usuario': demo_user,
                    'layout': DEMO_AGENCIA['layout'],
                    'imagem_capa': DEMO_AGENCIA['imagem_capa'],
                    'imagem_capa_foco_x': DEMO_AGENCIA['imagem_capa_foco_x'],
                    'imagem_capa_foco_y': DEMO_AGENCIA['imagem_capa_foco_y'],
                    'conteudo_blocos': DEMO_AGENCIA['conteudo_blocos'],
                },
            )
            if estado_sede:
                paises_demo = list(Pais.objects.filter(id=estado_sede.id_pais_id))
                extras = list(Pais.objects.filter(nome__in=['Irlanda', 'Canadá']))
                demo_ag.paises_atendidos.set(paises_demo + extras)
            tags_demo = list(Tag.objects.all()[:3])
            if tags_demo:
                demo_ag.tags.set(tags_demo)

            for idx, url in enumerate(DEMO_AGENCIA['galeria']):
                if not ImagemGaleria.objects.filter(agencia=demo_ag, imagem=url).exists():
                    ImagemGaleria.objects.create(agencia=demo_ag, imagem=url, ordem=idx)

            if not Plano.objects.filter(id_agencia=demo_ag).exists():
                prog = Programa.objects.first()
                if prog:
                    Plano.objects.create(
                        id_agencia=demo_ag,
                        id_programa=prog,
                        preco=Decimal('12900.00'),
                        descricao='Pacote completo de demonstração com 4 semanas de curso, acomodação e traslado.',
                        inclui='Matrícula, material didático, homestay com café da manhã, suporte 24h em português',
                    )

            # Resetar sequências no PostgreSQL após inserções com IDs explícitos
            if connection.vendor == 'postgresql':
                sql_list = connection.ops.sequence_reset_sql(
                    no_style(),
                    [Pais, Estado, Tag, Programa, Agencia, Plano, ImagemGaleria, Avaliacao, User],
                )
                with connection.cursor() as cursor:
                    for sql in sql_list:
                        cursor.execute(sql)

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed GlobalBridge concluído: {Pais.objects.count()} países, '
                f'{Agencia.objects.filter(ativo=True).count()} agências ativas (+1 demo), '
                f'{ImagemGaleria.objects.count()} fotos de galeria, '
                f'{Avaliacao.objects.count()} avaliações.'
            )
        )
