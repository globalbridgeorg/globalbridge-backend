from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Pais, Estado, Agencia, Programa, Plano

# Cada país real só tinha 1 agência com catálogo (a pesquisada em
# seed_agencias.py + seed_catalogo.py), então "programas_count" ficava
# preso em 1 pra todo mundo — parecia um valor de placeholder. Estas são
# agências fictícias (nome inventado, sem correspondente real), criadas
# só pra dar volume de catálogo: cada uma atende todos os países já
# cadastrados e tem seu próprio programa, então toda página de país passa
# a somar pelo menos 1 (agência real, quando existir) + estas = até 4
# programas distintos em vez de ficar travada em 1.
AGENCIAS_FICTICIAS = [
    {
        'nome': 'Horizonte Intercâmbios',
        'cidade': 'Lisboa',
        'sede_iso': 'PT',
        'descricao': 'Agência com atuação em mais de 20 países, especializada em imersão cultural de longa duração.',
        'site': 'https://www.horizonteintercambios.com.br',
        'programa': {
            'nome': 'Intercâmbio Cultural (Au Pair)',
            'descricao': 'Vivência com família anfitriã no exterior, com carga horária reduzida de atividades e bolsa mensal.',
            'duracao_min': 6, 'duracao_max': 12,
            'preco': 14000,
        },
    },
    {
        'nome': 'Rota Global Educação',
        'cidade': 'Toronto',
        'sede_iso': 'CA',
        'descricao': 'Rede de assessoria educacional presente em mais de 20 países, com foco em programas de longa duração.',
        'site': 'https://www.rotaglobaleducacao.com.br',
        'programa': {
            'nome': 'Ano Letivo no Exterior (High School)',
            'descricao': 'Um ano letivo completo em escola no exterior, com acompanhamento de família anfitriã e suporte local.',
            'duracao_min': 10, 'duracao_max': 12,
            'preco': 32000,
        },
    },
    {
        'nome': 'Vértice Study Abroad',
        'cidade': 'Dublin',
        'sede_iso': 'IE',
        'descricao': 'Agência voltada a programas de curta e média duração, com parcerias em universidades e ONGs pelo mundo.',
        'site': 'https://www.verticestudyabroad.com.br',
        'programa': {
            'nome': 'Voluntariado Internacional',
            'descricao': 'Trabalho voluntário no exterior em projetos sociais ou ambientais, com hospedagem incluída.',
            'duracao_min': 1, 'duracao_max': 6,
            'preco': 9000,
        },
    },
]


class Command(BaseCommand):
    help = (
        'Cria agências fictícias (nome inventado) que atendem todos os países já cadastrados, '
        'cada uma com seu próprio programa/plano — garante um mínimo de programas por país.'
    )

    def handle(self, *args, **options):
        todos_paises = Pais.objects.all()
        if not todos_paises.exists():
            self.stdout.write(self.style.WARNING('Nenhum país cadastrado — rode os seeds de país primeiro.'))
            return

        criadas = 0
        ja_existiam = 0

        for dados in AGENCIAS_FICTICIAS:
            agencia = Agencia.objects.filter(nome=dados['nome']).first()
            if agencia is None:
                sede = Pais.objects.filter(codigo_iso=dados['sede_iso']).first()
                estado, _ = Estado.objects.get_or_create(
                    cidade_principal=dados['cidade'], id_pais=sede,
                    defaults={'nome': dados['cidade']},
                )
                agencia = Agencia.objects.create(
                    nome=dados['nome'],
                    descricao=dados['descricao'],
                    contato='',
                    telefone='',
                    site=dados['site'],
                    endereco=f"{dados['cidade']}, {sede.nome}",
                    data_cadastro=timezone.now(),
                    ativo=True,
                    id_estado=estado,
                )
                criadas += 1
            else:
                ja_existiam += 1

            agencia.paises_atendidos.set(todos_paises)

            if not Plano.objects.filter(id_agencia=agencia).exists():
                prog_dados = dados['programa']
                programa, _ = Programa.objects.get_or_create(
                    nome=prog_dados['nome'],
                    defaults={
                        'descricao': prog_dados['descricao'],
                        'duracao_min': prog_dados['duracao_min'],
                        'duracao_max': prog_dados['duracao_max'],
                    },
                )
                Plano.objects.create(
                    id_agencia=agencia,
                    id_programa=programa,
                    preco=prog_dados['preco'],
                    descricao=prog_dados['descricao'],
                    inclui='',
                )

        self.stdout.write(self.style.SUCCESS(
            f'{criadas} agência(s) fictícia(s) criada(s), {ja_existiam} já existiam. '
            f'Todas atualizadas para atender os {todos_paises.count()} país(es) cadastrados.'
        ))
