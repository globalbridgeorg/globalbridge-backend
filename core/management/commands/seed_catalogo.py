from django.core.management.base import BaseCommand

from core.models import Agencia, Programa, Plano

# Um programa por agência, coerente com o que cada uma realmente oferece
# (mesma pesquisa da seed_agencias) — sem isso, "programas_count" ficava
# sempre em 0 e nenhuma delas tinha catálogo. Preço é uma estimativa de
# mercado pra preencher o campo obrigatório, não um valor confirmado com
# a agência — ajuste pelo admin quando tiver o valor real.
PROGRAMA_POR_AGENCIA = {
    'EF Education': {
        'nome': 'Curso de Idiomas',
        'descricao': 'Cursos de inglês, francês ou alemão em imersão, com certificação internacional.',
        'duracao_min': 2, 'duracao_max': 48,
        'preco': 12000,
    },
    'DAAD Brasil': {
        'nome': 'Bolsa de Graduação e Pós',
        'descricao': 'Assessoria e bolsa integral para graduação, mestrado ou doutorado em universidades públicas alemãs.',
        'duracao_min': 12, 'duracao_max': 48,
        'preco': 0,
    },
    'CIEE': {
        'nome': 'Intercâmbio Acadêmico',
        'descricao': 'Programas de graduação parcial e imersão cultural em universidades parceiras.',
        'duracao_min': 3, 'duracao_max': 12,
        'preco': 25000,
    },
    'ILAC': {
        'nome': 'Curso de Inglês',
        'descricao': 'Inglês geral ou acadêmico em Toronto ou Vancouver, com opção de estágio remunerado.',
        'duracao_min': 1, 'duracao_max': 12,
        'preco': 9000,
    },
    'Navitas': {
        'nome': 'Pathway Universitário',
        'descricao': 'Programa de acesso que prepara e garante vaga em universidades australianas parceiras.',
        'duracao_min': 6, 'duracao_max': 18,
        'preco': 18000,
    },
    'Languages International': {
        'nome': 'Inglês Geral',
        'descricao': 'Curso de inglês em Auckland, do nível iniciante ao avançado, com preparação para Cambridge.',
        'duracao_min': 1, 'duracao_max': 12,
        'preco': 8500,
    },
    'Kaplan International Languages': {
        'nome': 'Inglês + Preparação para Exames',
        'descricao': 'Curso de inglês geral com módulo de preparação para IELTS ou Cambridge, em Dublin.',
        'duracao_min': 1, 'duracao_max': 12,
        'preco': 9500,
    },
    'Sogang University Korean Language Education Center': {
        'nome': 'Curso de Coreano',
        'descricao': 'Curso intensivo de coreano por níveis, ligado à Universidade Sogang, em Seul.',
        'duracao_min': 3, 'duracao_max': 12,
        'preco': 11000,
    },
    'British Council': {
        'nome': 'Curso de Inglês',
        'descricao': 'Curso de inglês geral ou preparatório para exames internacionais, com material do British Council.',
        'duracao_min': 1, 'duracao_max': 12,
        'preco': 8000,
    },
}


class Command(BaseCommand):
    help = 'Cria um programa/plano de catálogo por agência já cadastrada, se ainda não existir.'

    def handle(self, *args, **options):
        criados = 0
        ja_existiam = 0
        sem_mapeamento = []

        for agencia in Agencia.objects.all():
            dados = PROGRAMA_POR_AGENCIA.get(agencia.nome)
            if not dados:
                sem_mapeamento.append(agencia.nome)
                continue

            if Plano.objects.filter(id_agencia=agencia).exists():
                ja_existiam += 1
                continue

            programa, _ = Programa.objects.get_or_create(
                nome=dados['nome'],
                defaults={
                    'descricao': dados['descricao'],
                    'duracao_min': dados['duracao_min'],
                    'duracao_max': dados['duracao_max'],
                },
            )
            Plano.objects.create(
                id_agencia=agencia,
                id_programa=programa,
                preco=dados['preco'],
                descricao=dados['descricao'],
                inclui='',
            )
            criados += 1

        self.stdout.write(self.style.SUCCESS(f'{criados} plano(s) criado(s), {ja_existiam} agência(s) já tinham catálogo.'))
        if sem_mapeamento:
            self.stdout.write(self.style.WARNING(
                'Sem programa mapeado (adicione em PROGRAMA_POR_AGENCIA): ' + ', '.join(sem_mapeamento)
            ))
