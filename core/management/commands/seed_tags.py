from django.core.management.base import BaseCommand

from core.models import Pais, Agencia, Tag

# Mesmo vocabulário de tags que já existia no painel de filtros do mapa
# (mock hardcoded em globeChoropleth.vue) — só move pra o backend em vez de
# inventar categorias novas.
TAG_LABELS = {
    'emprego': {
        'tech': 'Tecnologia', 'saude': 'Saúde', 'engenharia': 'Engenharia',
        'financas': 'Finanças', 'educacao': 'Educação', 'artes': 'Artes & Design',
    },
    'universidade': {
        'top100': 'Top 100 Mundial', 'bolsas': 'Oferece Bolsas', 'intercambio': 'Intercâmbio',
        'publicas': 'Públicas', 'privadas': 'Privadas', 'ead': 'EAD / Online',
    },
    'idioma': {
        'ingles': 'Inglês', 'espanhol': 'Espanhol', 'frances': 'Francês', 'alemao': 'Alemão',
        'mandarin': 'Mandarim', 'japones': 'Japonês', 'portugues': 'Português',
    },
    'cultura': {
        'gastronomia': 'Gastronomia', 'musica': 'Música', 'esportes': 'Esportes',
        'religiao': 'Diversidade Religiosa', 'festivais': 'Festivais', 'natureza': 'Natureza & Aventura',
    },
}

# Perfil de cada país já cadastrado — os mesmos 8 que já tinham entrada no
# mock do globo (countryMeta), só realocados pra cá.
PAIS_POR_ISO = {
    'GB': {
        'nome_ingles': 'United Kingdom',
        'tags': {'emprego': ['tech', 'financas', 'saude', 'educacao'], 'idioma': ['ingles'],
                  'cultura': ['musica', 'festivais', 'gastronomia'], 'universidade': ['top100', 'intercambio']},
    },
    'DE': {
        'nome_ingles': 'Germany',
        'tags': {'emprego': ['engenharia', 'tech', 'saude'], 'idioma': ['alemao'],
                  'cultura': ['festivais', 'gastronomia', 'musica'], 'universidade': ['top100', 'publicas', 'bolsas']},
    },
    'US': {
        'nome_ingles': 'United States of America',
        'tags': {'emprego': ['tech', 'financas', 'saude', 'engenharia', 'educacao', 'artes'], 'idioma': ['ingles'],
                  'cultura': ['gastronomia', 'musica', 'esportes', 'festivais'], 'universidade': ['top100', 'privadas', 'intercambio']},
    },
    'CA': {
        'nome_ingles': 'Canada',
        'tags': {'emprego': ['tech', 'saude', 'engenharia', 'educacao'], 'idioma': ['ingles', 'frances'],
                  'cultura': ['natureza', 'esportes'], 'universidade': ['top100', 'intercambio', 'bolsas']},
    },
    'AU': {
        'nome_ingles': 'Australia',
        'tags': {'emprego': ['tech', 'saude', 'engenharia'], 'idioma': ['ingles'],
                  'cultura': ['natureza', 'esportes'], 'universidade': ['intercambio', 'bolsas']},
    },
    'NZ': {
        'nome_ingles': 'New Zealand',
        'tags': {'emprego': ['saude', 'educacao'], 'idioma': ['ingles'],
                  'cultura': ['natureza', 'esportes'], 'universidade': ['intercambio', 'bolsas']},
    },
    'CN': {
        'nome_ingles': 'China',
        'tags': {'emprego': ['tech', 'engenharia', 'financas'], 'idioma': ['mandarin'],
                  'cultura': ['gastronomia', 'festivais'], 'universidade': ['top100', 'publicas']},
    },
    'IE': {
        'nome_ingles': 'Ireland',
        'tags': {'emprego': ['tech', 'financas'], 'idioma': ['ingles'],
                  'cultura': ['musica', 'festivais'], 'universidade': ['intercambio']},
    },
}

# Tags por agência — mesmo espírito do mock (cada agência só carrega as
# categorias em que realmente atua, não as quatro sempre).
AGENCIA_TAGS = {
    'EF Education': {'idioma': ['ingles', 'frances', 'alemao'], 'universidade': ['intercambio']},
    'DAAD Brasil': {'idioma': ['alemao'], 'universidade': ['top100', 'bolsas', 'publicas']},
    'CIEE': {'idioma': ['ingles'], 'universidade': ['intercambio', 'top100']},
    'ILAC': {'idioma': ['ingles']},
    'Navitas': {'universidade': ['intercambio', 'privadas']},
    'Languages International': {'idioma': ['ingles']},
    'Kaplan International Languages': {'idioma': ['ingles']},
}


class Command(BaseCommand):
    help = 'Cria as tags fixas do painel de filtros e categoriza países/agências já cadastrados.'

    def handle(self, *args, **options):
        tags_por_chave = {}
        criadas = 0
        for categoria, valores in TAG_LABELS.items():
            for valor, label in valores.items():
                tag, created = Tag.objects.get_or_create(
                    categoria=categoria, valor=valor, defaults={'label': label},
                )
                tags_por_chave[(categoria, valor)] = tag
                if created:
                    criadas += 1
        self.stdout.write(self.style.SUCCESS(f'{criadas} tag(s) nova(s) criada(s) (de {len(tags_por_chave)} no total).'))

        paises_atualizados = 0
        for pais in Pais.objects.all():
            dados = PAIS_POR_ISO.get(pais.codigo_iso.upper())
            if not dados:
                continue
            pais.nome_ingles = dados['nome_ingles']
            pais.save(update_fields=['nome_ingles'])
            tags = [tags_por_chave[(cat, v)] for cat, vs in dados['tags'].items() for v in vs]
            pais.tags.set(tags)
            paises_atualizados += 1
        self.stdout.write(self.style.SUCCESS(f'{paises_atualizados} país(es) com nome em inglês e tags atualizados.'))

        agencias_atualizadas = 0
        for agencia in Agencia.objects.all():
            dados = AGENCIA_TAGS.get(agencia.nome)
            if not dados:
                continue
            tags = [tags_por_chave[(cat, v)] for cat, vs in dados.items() for v in vs]
            agencia.tags.set(tags)
            agencias_atualizadas += 1
        self.stdout.write(self.style.SUCCESS(f'{agencias_atualizadas} agência(s) categorizada(s).'))
