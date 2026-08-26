from django.core.management.base import BaseCommand
from django.db.models import Count

from core.models import Agencia, Favorito, Pais


class Command(BaseCommand):
    """Corrige agências que na vida real atuam em mais de um país e que,
    até agora, só podiam ter UM país (id_estado) — cada país virava uma
    linha de Agencia duplicada com o mesmo nome (ex.: 11 linhas de
    "EF Education", uma por país).

    Passo 1 (sempre roda): garante que toda agência tem paises_atendidos
    preenchido com pelo menos o país da própria sede.

    Passo 2 (sempre roda): pra cada NOME duplicado, mantém a linha de
    id mais baixo como a agência de verdade, muda paises_atendidos dela
    pra somar os países de todas as duplicatas, e apaga as duplicatas
    (mas primeiro realoca planos, favoritos e reaproveita usuário/
    avaliações se alguma duplicata tiver o que a canônica não tem).
    """

    help = 'Preenche paises_atendidos e funde agências duplicadas (mesmo nome, países diferentes) em uma só.'

    def handle(self, *args, **options):
        # Passo 1 — toda agência passa a listar pelo menos o país da sede.
        preenchidas = 0
        for agencia in Agencia.objects.all():
            if agencia.id_estado and not agencia.paises_atendidos.filter(id=agencia.id_estado.id_pais_id).exists():
                agencia.paises_atendidos.add(agencia.id_estado.id_pais)
                preenchidas += 1

        # Passo 2 — funde duplicatas por nome.
        fundidas = 0
        apagadas = 0
        nomes_duplicados = (
            Agencia.objects.values('nome').annotate(total=Count('id')).filter(total__gt=1).values_list('nome', flat=True)
        )

        for nome in nomes_duplicados:
            linhas = list(Agencia.objects.filter(nome=nome).order_by('id'))
            canonica, duplicatas = linhas[0], linhas[1:]

            paises_ids = set(canonica.paises_atendidos.values_list('id', flat=True))
            for dup in duplicatas:
                paises_ids.update(dup.paises_atendidos.values_list('id', flat=True))

                # Se a duplicata tem algo que a canônica não tem, aproveita.
                if dup.usuario_id and not canonica.usuario_id:
                    canonica.usuario_id = dup.usuario_id
                    dup.usuario = None
                    dup.save(update_fields=['usuario'])
                if dup.como_funciona and not canonica.como_funciona:
                    canonica.como_funciona = dup.como_funciona

                dup.avaliacao_set.update(id_agencia=canonica)
                dup.plano_set.update(id_agencia=canonica)
                Favorito.objects.filter(tipo='agencia', objeto_id=dup.id).delete()

            canonica.paises_atendidos.set(Pais.objects.filter(id__in=paises_ids))
            canonica.save()

            for dup in duplicatas:
                dup.delete()
                apagadas += 1
            fundidas += 1

        self.stdout.write(self.style.SUCCESS(
            f'{preenchidas} agência(s) tiveram paises_atendidos completado(s). '
            f'{fundidas} nome(s) duplicado(s) fundido(s), {apagadas} linha(s) removida(s).'
        ))
