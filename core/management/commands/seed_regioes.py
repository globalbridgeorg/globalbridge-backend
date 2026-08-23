from django.core.management.base import BaseCommand

from core.models import Pais

# Classificação real de região por código ISO — necessária pras páginas de
# Destinos/Região no frontend (Pais.regiao). Sem entrada aqui = país fica
# sem região até alguém cadastrar/ajustar pelo admin.
REGIAO_POR_ISO = {
    'GB': 'europa', 'DE': 'europa', 'IE': 'europa', 'FR': 'europa', 'ES': 'europa',
    'US': 'america_norte', 'CA': 'america_norte',
    'AU': 'oceania', 'NZ': 'oceania',
    'CN': 'asia', 'JP': 'asia', 'KR': 'asia', 'TH': 'asia', 'SG': 'asia', 'VN': 'asia',
}


class Command(BaseCommand):
    help = 'Preenche Pais.regiao para os países já cadastrados, a partir do código ISO.'

    def handle(self, *args, **options):
        atualizados = 0
        sem_mapeamento = []

        for pais in Pais.objects.all():
            regiao = REGIAO_POR_ISO.get(pais.codigo_iso.upper())
            if regiao is None:
                sem_mapeamento.append(f'{pais.nome} ({pais.codigo_iso})')
                continue
            if pais.regiao != regiao:
                pais.regiao = regiao
                pais.save(update_fields=['regiao'])
                atualizados += 1

        self.stdout.write(self.style.SUCCESS(f'{atualizados} país(es) atualizado(s).'))
        if sem_mapeamento:
            self.stdout.write(self.style.WARNING(
                'Sem mapeamento de região (adicione em REGIAO_POR_ISO): ' + ', '.join(sem_mapeamento)
            ))
