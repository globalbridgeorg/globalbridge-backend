from django.db import migrations
from django.utils.text import slugify


def preencher_usernames(apps, schema_editor):
    User = apps.get_model('core', 'User')
    usados = set()
    for user in User.objects.all():
        base = slugify(user.name or user.email.split('@')[0]) or 'usuario'
        base = base[:32]
        candidato = base
        sufixo = 1
        while candidato in usados or User.objects.filter(username=candidato).exclude(pk=user.pk).exists():
            sufixo += 1
            candidato = f'{base}{sufixo}'
        user.username = candidato
        user.save(update_fields=['username'])
        usados.add(candidato)


def reverter(apps, schema_editor):
    User = apps.get_model('core', 'User')
    User.objects.update(username='')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_user_username'),
    ]

    operations = [
        migrations.RunPython(preencher_usernames, reverter),
    ]
