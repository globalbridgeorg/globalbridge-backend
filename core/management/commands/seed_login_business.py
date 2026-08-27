from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import Agencia, User

# Senha de teste única pra todos os logins business criados aqui — é dev
# local, não é a senha real de ninguém. Documentado pro usuário quando o
# comando roda.
SENHA_TESTE = 'agencia12345'


class Command(BaseCommand):
    help = 'Cria um usuário de conta business (tipo=agencia) pra cada agência que ainda não tem um, e vincula.'

    def handle(self, *args, **options):
        criados = []
        ja_tinham = 0

        for agencia in Agencia.objects.all().order_by('id'):
            if agencia.usuario_id:
                ja_tinham += 1
                continue

            # Inclui o id da agência no e-mail — sem isso, duas agências com
            # nome igual ou muito parecido (ex.: "Rota Global Educação" e
            # outra variação) geram o mesmo slug, o get_or_create abaixo
            # devolve o MESMO usuário pras duas, e a segunda falha ao salvar
            # (usuario_id é único em Agencia).
            slug = slugify(agencia.nome)
            email = f'negocios+{agencia.id}@{slug}.globalbridge.test'

            usuario, foi_criado = User.objects.get_or_create(
                email=email,
                defaults={'name': agencia.nome, 'tipo': 'agencia'},
            )
            if foi_criado:
                usuario.set_password(SENHA_TESTE)
                usuario.tipo = 'agencia'
                usuario.save()

            agencia.usuario = usuario
            agencia.save(update_fields=['usuario'])
            criados.append((agencia.nome, email))

        self.stdout.write(self.style.SUCCESS(
            f'{len(criados)} login(s) business criado(s), {ja_tinham} agência(s) já tinham conta vinculada.'
        ))
        for nome, email in criados:
            self.stdout.write(f'  {nome} -> {email} / senha: {SENHA_TESTE}')
