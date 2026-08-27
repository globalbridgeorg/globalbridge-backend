import random

from django.core.management.base import BaseCommand

from core.models import Agencia, Avaliacao, User

# Fotos reais de rosto (uso público, geradas por IA — randomuser.me é feito
# exatamente pra isso: avatar de teste sem risco de licença ou de usar foto
# de alguém de verdade sem permissão). Separadas por gênero pra combinar com
# o nome sorteado logo abaixo.
FOTOS_MULHER = [f'https://randomuser.me/api/portraits/women/{i}.jpg' for i in range(1, 20)]
FOTOS_HOMEM = [f'https://randomuser.me/api/portraits/men/{i}.jpg' for i in range(1, 20)]

# (nome, gênero) — gênero só decide qual conjunto de fotos usar.
NOMES = [
    ('Marina Torres', 'f'), ('Lucas Almeida', 'm'), ('Sofia Kaneko', 'f'), ('Pedro Vasconcelos', 'm'),
    ('Beatriz Nogueira', 'f'), ('Rafael Souza', 'm'), ('Camila Duarte', 'f'), ('Gustavo Lima', 'm'),
    ('Isabela Ferreira', 'f'), ('Thiago Barros', 'm'), ('Larissa Mendes', 'f'), ('André Ribeiro', 'm'),
    ('Juliana Castro', 'f'), ('Bruno Carvalho', 'm'), ('Fernanda Rocha', 'f'), ('Diego Martins', 'm'),
    ('Amanda Pereira', 'f'), ('Vinícius Costa', 'm'), ('Natália Gomes', 'f'), ('Felipe Araújo', 'm'),
    ('Carolina Dias', 'f'), ('Matheus Correia', 'm'), ('Letícia Santana', 'f'), ('Rodrigo Teixeira', 'm'),
    ('Gabriela Moura', 'f'),
]

# Comentários variados por faixa de nota — texto genérico o bastante pra
# combinar com qualquer agência, mas com detalhe suficiente pra não parecer
# gerado (evita repetir a mesma frase-molde em todas as avaliações).
COMENTARIOS_5 = [
    'Processo todo tranquilo, do primeiro contato até o embarque. Recomendo demais pra quem está decidindo.',
    'Atendimento excelente, sempre responderam rápido e explicaram cada etapa com clareza. Valeu muito a pena.',
    'Já indiquei pra dois amigos. Organização impecável e suporte mesmo depois que cheguei no destino.',
    'Superou minhas expectativas — resolveram até um imprevisto de documentação que eu não esperava.',
    'Equipe muito atenciosa, senti que realmente se importavam com a minha experiência, não só com a venda.',
]
COMENTARIOS_4 = [
    'Experiência boa no geral. Demorou um pouco pra confirmar a matrícula, mas no fim deu tudo certo.',
    'Atendimento bom, só senti falta de mais contato durante a fase de adaptação lá fora.',
    'Recomendo — teve uma comunicação meio lenta no início, mas depois melhorou bastante.',
    'Cumpriram o combinado, ficaram só devendo um retorno mais rápido em alguns e-mails.',
]
COMENTARIOS_3 = [
    'Cumpriu o que prometeu, mas o atendimento poderia ser mais próximo durante o processo.',
    'Deu certo no fim, só achei o processo mais burocrático do que eu esperava.',
]


class Command(BaseCommand):
    help = 'Cria usuários de teste com foto e gera de 2 a 5 avaliações por agência.'

    def handle(self, *args, **options):
        usuarios = self._garantir_usuarios()

        agencias_afetadas = 0
        avaliacoes_criadas = 0

        for agencia in Agencia.objects.all():
            existentes = Avaliacao.objects.filter(id_agencia=agencia).select_related('id_usuario')
            if existentes.count() >= 2:
                continue

            ja_avaliaram = set(existentes.values_list('id_usuario_id', flat=True))
            candidatos = [u for u in usuarios if u.id not in ja_avaliaram]
            random.shuffle(candidatos)

            alvo = random.randint(2, 5)
            faltam = max(0, alvo - existentes.count())

            for usuario in candidatos[:faltam]:
                nota = random.choices([5, 4, 3], weights=[55, 35, 10])[0]
                comentario = random.choice({5: COMENTARIOS_5, 4: COMENTARIOS_4, 3: COMENTARIOS_3}[nota])
                Avaliacao.objects.create(
                    nota=nota,
                    comentario=comentario,
                    id_usuario=usuario,
                    id_agencia=agencia,
                )
                avaliacoes_criadas += 1

            if faltam:
                agencias_afetadas += 1

        self.stdout.write(self.style.SUCCESS(
            f'{avaliacoes_criadas} avaliação(ões) criada(s) em {agencias_afetadas} agência(s).'
        ))

    def _garantir_usuarios(self):
        usuarios = []
        for i, (nome, genero) in enumerate(NOMES):
            email = f'{nome.lower().replace(" ", ".")}@avaliador.globalbridge.test'
            usuario, criado = User.objects.get_or_create(
                email=email,
                defaults={'name': nome, 'tipo': 'estudante'},
            )
            if criado:
                usuario.set_password('avaliador12345')

            # Sempre garante uma foto, mesmo pra usuário que já existia sem
            # uma — usuario.avatar.name aceita uma URL direta (o serializer
            # de avaliação já trata esse caso, ver AvaliacaoResumidaSerializer).
            if not usuario.avatar and not usuario.foto:
                fotos = FOTOS_MULHER if genero == 'f' else FOTOS_HOMEM
                usuario.avatar.name = fotos[i % len(fotos)]

            usuario.save()
            usuarios.append(usuario)

        return usuarios
