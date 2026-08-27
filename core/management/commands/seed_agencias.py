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
    'PT': {
        'nome': 'EF Education',
        'cidade': 'Lisboa',
        'descricao': 'Cursos de português para estrangeiros e programas de imersão cultural em Lisboa.',
        'site': 'https://www.ef.com',
    },
    'ES': {
        'nome': 'EF Education',
        'cidade': 'Barcelona',
        'descricao': 'Cursos de espanhol em imersão em Barcelona, com certificação internacional reconhecida.',
        'site': 'https://www.ef.com',
    },
    'FR': {
        'nome': 'EF Education',
        'cidade': 'Nice',
        'descricao': 'Cursos de francês em imersão na Riviera Francesa, do nível iniciante ao avançado.',
        'site': 'https://www.ef.com',
    },
    'IT': {
        'nome': 'EF Education',
        'cidade': 'Roma',
        'descricao': 'Cursos de italiano em imersão no centro de Roma, com atividades culturais incluídas.',
        'site': 'https://www.ef.com',
    },
    'NL': {
        'nome': 'EF Education',
        'cidade': 'Amsterdã',
        'descricao': 'Cursos de inglês e holandês em Amsterdã, com forte comunidade internacional de estudantes.',
        'site': 'https://www.ef.com',
    },
    'MT': {
        'nome': 'EF Education',
        'cidade': "St. Julian's",
        'descricao': 'Cursos de inglês à beira-mar em Malta, um dos destinos mais em conta da Europa.',
        'site': 'https://www.ef.com',
    },
    'JP': {
        'nome': 'EF Education',
        'cidade': 'Tóquio',
        'descricao': 'Cursos de japonês em imersão em Tóquio, com atividades de cultura e tecnologia.',
        'site': 'https://www.ef.com',
    },
    'MX': {
        'nome': 'EF Education',
        'cidade': 'Playa del Carmen',
        'descricao': 'Cursos de espanhol em imersão no Caribe mexicano, com custo mais baixo que a Europa.',
        'site': 'https://www.ef.com',
    },
    'AR': {
        'nome': 'EF Education',
        'cidade': 'Buenos Aires',
        'descricao': 'Cursos de espanhol em imersão em Buenos Aires, próximo o suficiente pra quem já fala português.',
        'site': 'https://www.ef.com',
    },
    'ZA': {
        'nome': 'EF Education',
        'cidade': 'Cidade do Cabo',
        'descricao': 'Cursos de inglês em imersão na Cidade do Cabo, com atividades de natureza e vida selvagem.',
        'site': 'https://www.ef.com',
    },
    'KR': {
        'nome': 'Sogang University Korean Language Education Center',
        'cidade': 'Seul',
        'descricao': 'Um dos centros de coreano mais tradicionais do país, ligado à Universidade Sogang, em Seul.',
        'site': 'https://klec.sogang.ac.kr',
    },
    'SG': {
        'nome': 'British Council',
        'cidade': 'Singapura',
        'descricao': 'Cursos de inglês e preparação para exames internacionais, com a credibilidade do British Council.',
        'site': 'https://www.britishcouncil.sg',
    },
    'CL': {
        'nome': 'British Council',
        'cidade': 'Santiago',
        'descricao': 'Cursos de inglês em Santiago, com professores certificados e material do British Council.',
        'site': 'https://www.britishcouncil.cl',
    },
    'CO': {
        'nome': 'British Council',
        'cidade': 'Bogotá',
        'descricao': 'Cursos de inglês em Bogotá, com foco em preparação para exames internacionais.',
        'site': 'https://www.britishcouncil.co',
    },
    'MA': {
        'nome': 'CIEE',
        'cidade': 'Rabat',
        'descricao': 'Programas de imersão cultural e árabe em Rabat, em parceria com universidades locais.',
        'site': 'https://www.ciee.org',
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

            agencia = Agencia.objects.filter(nome=dados['nome'], id_estado__id_pais=pais).first()
            if agencia is not None:
                # Já existia — mas roda de novo mesmo assim, porque uma
                # versão antiga deste comando criava a agência sem marcar
                # `paises_atendidos` (o M2M que decide quais agências
                # aparecem em cada país). Sem essa linha, a agência existe
                # no banco mas some da página do país.
                agencia.paises_atendidos.add(pais)
                ja_existiam += 1
                continue

            estado, _ = Estado.objects.get_or_create(
                cidade_principal=dados['cidade'], id_pais=pais,
                defaults={'nome': dados['cidade']},
            )
            agencia = Agencia.objects.create(
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
            agencia.paises_atendidos.add(pais)
            criadas += 1

        self.stdout.write(self.style.SUCCESS(f'{criadas} agência(s) criada(s), {ja_existiam} já existiam.'))
        if sem_mapeamento:
            self.stdout.write(self.style.WARNING(
                'Sem agência mapeada (adicione em AGENCIAS_POR_ISO): ' + ', '.join(sem_mapeamento)
            ))
