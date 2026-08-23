from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Pais, Estado, Agencia

# Uma agência real por país já cadastrado, pesquisada (não inventada) —
# mesmo espírito das agências já citadas no mock do mapa (EF Education,
# DAAD Brasil, Study USA). Sem telefone/e-mail: não temos como confirmar
# um contato direto real, então o site oficial é a única via de contato
# até uma agência de verdade se cadastrar na plataforma.
AGENCIAS_POR_ISO = {
    'GB': {
        'nome': 'EF Education',
        'cidade': 'Londres',
        'descricao': 'Cursos de idiomas em mais de 50 países com certificação internacional reconhecida.',
        'site': 'https://www.ef.com',
    },
    'DE': {
        'nome': 'DAAD Brasil',
        'cidade': 'Berlim',
        'descricao': 'Serviço Alemão de Intercâmbio Acadêmico, com bolsas para universidades alemãs.',
        'site': 'https://www.daad.org.br',
    },
    'US': {
        'nome': 'CIEE',
        'cidade': 'Shanghai',
        'descricao': 'Organização americana de intercâmbio acadêmico, com programas de graduação e imersão em parceria com universidades locais.',
        'site': 'https://www.ciee.org',
    },
    'CA': {
        'nome': 'ILAC',
        'cidade': 'Toronto',
        'descricao': 'International Language Academy of Canada — escola de inglês com unidades em Toronto e Vancouver.',
        'site': 'https://ilac.com',
    },
    'AU': {
        'nome': 'Navitas',
        'cidade': 'Perth',
        'descricao': 'Provedora de programas de acesso (pathway) em parceria com universidades australianas.',
        'site': 'https://www.navitas.com',
    },
    'NZ': {
        'nome': 'Languages International',
        'cidade': 'Auckland',
        'descricao': 'Escola de inglês fundada em 1978, uma das mais tradicionais da Nova Zelândia.',
        'site': 'https://www.languages.ac.nz',
    },
    'CN': {
        'nome': 'CIEE',
        'cidade': 'Xangai',
        'descricao': 'Programas de imersão em chinês e negócios no campus da East China Normal University, em Xangai.',
        'site': 'https://www.ciee.org',
    },
    'IE': {
        'nome': 'Kaplan International Languages',
        'cidade': 'Dublin',
        'descricao': 'Escola de inglês no centro de Dublin, com preparação para exames Cambridge e IELTS.',
        'site': 'https://www.kaplaninternational.com',
    },
}


class Command(BaseCommand):
    help = 'Cria uma agência real (pesquisada) por país já cadastrado, uma por país, se ainda não existir.'

    def handle(self, *args, **options):
        criadas = 0
        ja_existiam = 0
        sem_mapeamento = []

        for pais in Pais.objects.all():
            dados = AGENCIAS_POR_ISO.get(pais.codigo_iso.upper())
            if dados is None:
                sem_mapeamento.append(f'{pais.nome} ({pais.codigo_iso})')
                continue

            if Agencia.objects.filter(nome=dados['nome'], id_estado__id_pais=pais).exists():
                ja_existiam += 1
                continue

            estado, _ = Estado.objects.get_or_create(
                cidade_principal=dados['cidade'], id_pais=pais,
                defaults={'nome': dados['cidade']},
            )
            Agencia.objects.create(
                nome=dados['nome'],
                descricao=dados['descricao'],
                contato='',
                telefone='',
                site=dados['site'],
                endereco=f"{dados['cidade']}, {pais.nome}",
                data_cadastro=timezone.now(),
                ativo=True,
                id_estado=estado,
            )
            criadas += 1

        self.stdout.write(self.style.SUCCESS(f'{criadas} agência(s) criada(s), {ja_existiam} já existiam.'))
        if sem_mapeamento:
            self.stdout.write(self.style.WARNING(
                'Sem agência mapeada (adicione em AGENCIAS_POR_ISO): ' + ', '.join(sem_mapeamento)
            ))
