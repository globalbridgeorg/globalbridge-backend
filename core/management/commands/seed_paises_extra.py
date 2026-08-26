from django.core.management.base import BaseCommand

from core.models import Pais

# Amplia o catálogo de países pra bater com a promessa de "mais de 40
# países" que já existe no texto do site — antes desse seed só havia 8
# cadastrados. Dados reais e verificáveis (idioma oficial, região,
# descrição, cultura); intercambistas/universidades são um índice
# ilustrativo de popularidade (mesmo espírito dos 8 países já existentes,
# que também não vêm de uma fonte estatística oficial) — não confundir com
# estatística confirmada.
#
# imagem_url vem da bandeira oficial de cada país (Wikimedia Commons, uso
# livre) — não achei uma foto de paisagem real por país sem risco de
# licença, então a bandeira ficou como imagem provisória. Trocar por uma
# foto de destino quando tiver uma fonte confiável por país.
PAISES_NOVOS = [
    {
        'nome': 'Portugal', 'nome_ingles': 'Portugal', 'codigo_iso': 'PT', 'regiao': 'europa',
        'idioma': 'Português', 'custo_de_vida': 'Médio',
        'descricao': 'Destino cada vez mais procurado por brasileiros pela língua compartilhada, custo de vida menor que o resto da Europa Ocidental e facilidade de cidadania.',
        'cultura': 'Fado, gastronomia à base de bacalhau e frutos do mar, e uma rotina bem mais tranquila que a de outras capitais europeias.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Flag_of_Portugal_%28official%29.svg/960px-Flag_of_Portugal_%28official%29.svg.png',
        'intercambistas': 512, 'universidades': 240,
    },
    {
        'nome': 'Espanha', 'nome_ingles': 'Spain', 'codigo_iso': 'ES', 'regiao': 'europa',
        'idioma': 'Espanhol', 'custo_de_vida': 'Médio',
        'descricao': 'Um dos destinos mais procurados do mundo pra aprender espanhol, com forte tradição universitária e vida cultural intensa.',
        'cultura': 'Flamenco, gastronomia regional (tapas, paella) e uma vida noturna que começa tarde e vai até o amanhecer.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Flag_of_Spain.svg/960px-Flag_of_Spain.svg.png',
        'intercambistas': 631, 'universidades': 310,
    },
    {
        'nome': 'França', 'nome_ingles': 'France', 'codigo_iso': 'FR', 'regiao': 'europa',
        'idioma': 'Francês', 'custo_de_vida': 'Alto',
        'descricao': 'Berço do ensino formal de idiomas (Alliance Française) e de uma das tradições acadêmicas mais respeitadas da Europa.',
        'cultura': 'Arte, gastronomia refinada e uma vida cultural com museus e centros de moda entre os mais influentes do mundo.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Flag_of_France.svg/960px-Flag_of_France.svg.png',
        'intercambistas': 498, 'universidades': 289,
    },
    {
        'nome': 'Itália', 'nome_ingles': 'Italy', 'codigo_iso': 'IT', 'regiao': 'europa',
        'idioma': 'Italiano', 'custo_de_vida': 'Médio',
        'descricao': 'História e patrimônio artístico em cada esquina, com cursos de idioma e gastronomia muito procurados por quem já fala português.',
        'cultura': 'Arte renascentista, culinária regional e uma relação com comida e família que atravessa qualquer conversa.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/960px-Flag_of_Italy.svg.png',
        'intercambistas': 407, 'universidades': 198,
    },
    {
        'nome': 'Holanda', 'nome_ingles': 'Netherlands', 'codigo_iso': 'NL', 'regiao': 'europa',
        'idioma': 'Holandês', 'custo_de_vida': 'Alto',
        'descricao': 'Universidades bem ranqueadas com cursos inteiros em inglês, o que facilita muito a vida de quem ainda não fala holandês.',
        'cultura': 'Bicicletas em vez de carro, mentalidade aberta e uma vida ao ar livre mesmo com o clima nem sempre favorável.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Flag_of_the_Netherlands.svg/960px-Flag_of_the_Netherlands.svg.png',
        'intercambistas': 289, 'universidades': 176,
    },
    {
        'nome': 'Malta', 'nome_ingles': 'Malta', 'codigo_iso': 'MT', 'regiao': 'europa',
        'idioma': 'Inglês e maltês', 'custo_de_vida': 'Médio',
        'descricao': 'Um dos destinos mais em conta da Europa pra estudar inglês, com clima mediterrâneo o ano todo.',
        'cultura': 'Ilha pequena, história marcada por fenícios, romanos e cavaleiros, e praias a poucos minutos de qualquer escola.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Flag_of_Malta.svg/960px-Flag_of_Malta.svg.png',
        'intercambistas': 214, 'universidades': 42,
    },
    {
        'nome': 'Japão', 'nome_ingles': 'Japan', 'codigo_iso': 'JP', 'regiao': 'asia',
        'idioma': 'Japonês', 'custo_de_vida': 'Alto',
        'descricao': 'Tecnologia de ponta ao lado de tradições milenares, com forte apelo pra quem se interessa por cultura pop japonesa.',
        'cultura': 'Etiqueta bem definida, pontualidade quase religiosa e uma culinária que vai muito além do que chega no Brasil.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Flag_of_Japan.svg/960px-Flag_of_Japan.svg.png',
        'intercambistas': 356, 'universidades': 287,
    },
    {
        'nome': 'Coreia do Sul', 'nome_ingles': 'South Korea', 'codigo_iso': 'KR', 'regiao': 'asia',
        'idioma': 'Coreano', 'custo_de_vida': 'Médio',
        'descricao': 'Popularidade crescente puxada pela cultura pop coreana, com universidades fortes em tecnologia e design.',
        'cultura': 'K-pop, k-dramas e uma gastronomia picante que já conquistou fãs no mundo todo.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Flag_of_South_Korea.svg/960px-Flag_of_South_Korea.svg.png',
        'intercambistas': 298, 'universidades': 191,
    },
    {
        'nome': 'Singapura', 'nome_ingles': 'Singapore', 'codigo_iso': 'SG', 'regiao': 'asia',
        'idioma': 'Inglês', 'custo_de_vida': 'Alto',
        'descricao': 'Hub educacional multicultural da Ásia, com ensino em inglês e universidades tecnológicas de referência.',
        'cultura': 'Mistura de tradições chinesa, malaia e indiana, cidade extremamente organizada e gastronomia de rua premiada.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Flag_of_Singapore.svg/960px-Flag_of_Singapore.svg.png',
        'intercambistas': 187, 'universidades': 34,
    },
    {
        'nome': 'México', 'nome_ingles': 'Mexico', 'codigo_iso': 'MX', 'regiao': 'america_norte',
        'idioma': 'Espanhol', 'custo_de_vida': 'Baixo',
        'descricao': 'Proximidade cultural com o Brasil e custo baixo tornam o país uma porta de entrada popular pra cursos intensivos de espanhol.',
        'cultura': 'Herança pré-colombiana viva no dia a dia, gastronomia riquíssima e festividades que tomam as ruas o ano inteiro.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Flag_of_Mexico.svg/960px-Flag_of_Mexico.svg.png',
        'intercambistas': 276, 'universidades': 165,
    },
    {
        'nome': 'Argentina', 'nome_ingles': 'Argentina', 'codigo_iso': 'AR', 'regiao': 'america_sul',
        'idioma': 'Espanhol', 'custo_de_vida': 'Baixo',
        'descricao': 'Vizinho de fronteira com universidades tradicionais e custo de vida baixo pra quem já entende um pouco de espanhol.',
        'cultura': 'Tango, futebol como religião e uma cultura de café e conversa que lembra bastante o Brasil.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Flag_of_Argentina.svg/960px-Flag_of_Argentina.svg.png',
        'intercambistas': 341, 'universidades': 128,
    },
    {
        'nome': 'Chile', 'nome_ingles': 'Chile', 'codigo_iso': 'CL', 'regiao': 'america_sul',
        'idioma': 'Espanhol', 'custo_de_vida': 'Médio',
        'descricao': 'Estabilidade econômica na região, com paisagens que vão do deserto do Atacama à Patagônia.',
        'cultura': 'Vinhos reconhecidos internacionalmente, forte cena musical e uma geografia que muda completamente a cada poucas horas de viagem.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Flag_of_Chile.svg/960px-Flag_of_Chile.svg.png',
        'intercambistas': 198, 'universidades': 94,
    },
    {
        'nome': 'Colômbia', 'nome_ingles': 'Colombia', 'codigo_iso': 'CO', 'regiao': 'america_sul',
        'idioma': 'Espanhol', 'custo_de_vida': 'Baixo',
        'descricao': 'Popularidade crescente pra intercâmbio de espanhol, com custo acessível e cidades cada vez mais procuradas por estrangeiros.',
        'cultura': 'Música (salsa, cumbia), café de qualidade internacional e uma biodiversidade entre as maiores do planeta.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Flag_of_Colombia.svg/960px-Flag_of_Colombia.svg.png',
        'intercambistas': 176, 'universidades': 88,
    },
    {
        'nome': 'África do Sul', 'nome_ingles': 'South Africa', 'codigo_iso': 'ZA', 'regiao': 'africa',
        'idioma': 'Inglês', 'custo_de_vida': 'Baixo',
        'descricao': 'Ensino em inglês com custo de vida baixo e uma natureza exuberante, cada vez mais procurada por quem quer fugir do óbvio.',
        'cultura': 'País com 11 línguas oficiais, forte diversidade étnica e uma história recente marcada pelo fim do apartheid.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Flag_of_South_Africa.svg/960px-Flag_of_South_Africa.svg.png',
        'intercambistas': 143, 'universidades': 71,
    },
    {
        'nome': 'Marrocos', 'nome_ingles': 'Morocco', 'codigo_iso': 'MA', 'regiao': 'africa',
        'idioma': 'Árabe e francês', 'custo_de_vida': 'Baixo',
        'descricao': 'Mistura de culturas árabe, berbere e francesa bem na porta de entrada do continente africano com a Europa.',
        'cultura': 'Souks, arquitetura mourisca e uma gastronomia de especiarias que marca qualquer visitante.',
        'imagem_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Flag_of_Morocco.svg/960px-Flag_of_Morocco.svg.png',
        'intercambistas': 96, 'universidades': 53,
    },
]

# Bandeira oficial (Wikimedia Commons) dos 8 países que já existiam sem
# nenhuma imagem cadastrada — mesmo raciocínio dos novos acima.
IMAGENS_PAISES_EXISTENTES = {
    'GB': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Flag_of_the_United_Kingdom_%281-2%29.svg/960px-Flag_of_the_United_Kingdom_%281-2%29.svg.png',
    'CN': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Flag_of_the_People%27s_Republic_of_China.svg/960px-Flag_of_the_People%27s_Republic_of_China.svg.png',
    'DE': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/960px-Flag_of_Germany.svg.png',
    'US': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Flag_of_the_United_States_%28DDD-F-416E_specifications%29.svg/960px-Flag_of_the_United_States_%28DDD-F-416E_specifications%29.svg.png',
    'CA': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Flag_of_Canada_%28Pantone%29.svg/960px-Flag_of_Canada_%28Pantone%29.svg.png',
    'AU': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Flag_of_Australia_%28converted%29.svg/960px-Flag_of_Australia_%28converted%29.svg.png',
    'NZ': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Flag_of_New_Zealand.svg/960px-Flag_of_New_Zealand.svg.png',
    'IE': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Flag_of_Ireland.svg/960px-Flag_of_Ireland.svg.png',
}


class Command(BaseCommand):
    help = 'Adiciona novos países reais ao catálogo e preenche a imagem (bandeira) dos que ainda não têm.'

    def handle(self, *args, **options):
        criados = 0
        for dados in PAISES_NOVOS:
            if Pais.objects.filter(codigo_iso=dados['codigo_iso']).exists():
                continue
            Pais.objects.create(**dados, ativo=True)
            criados += 1

        atualizados = 0
        for pais in Pais.objects.filter(imagem_url=''):
            url = IMAGENS_PAISES_EXISTENTES.get(pais.codigo_iso.upper())
            if url:
                pais.imagem_url = url
                pais.save(update_fields=['imagem_url'])
                atualizados += 1

        total = Pais.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'{criados} país(es) novo(s) criado(s), {atualizados} imagem(ns) preenchida(s). Total agora: {total}.'
        ))
