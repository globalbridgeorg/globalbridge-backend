from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Agencia, Plano, Programa


class PlanoModelTests(TestCase):
    def test_plano_inclui_is_registered_as_a_model_field(self):
        agencia = Agencia.objects.create(
            nome='Agência Teste',
            descricao='Descrição da agência',
            contato='contato@teste.com',
            telefone='11999999999',
            site='https://teste.com',
            endereco='Rua Teste, 1',
            data_cadastro='2024-01-01T00:00:00Z',
            ativo=True,
        )
        programa = Programa.objects.create(
            nome='Programa Teste',
            descricao='Descrição do programa',
            duracao_min=1,
            duracao_max=6,
        )

        plano = Plano.objects.create(
            id_agencia=agencia,
            id_programa=programa,
            preco='150.00',
            descricao='Plano básico',
            inclui='Acomodação e suporte',
        )

        self.assertTrue(isinstance(Plano._meta.get_field('inclui'), models.TextField))
        self.assertIn('Plano', str(plano))
        self.assertEqual(plano.inclui, 'Acomodação e suporte')


class UserAvatarUploadTests(TestCase):
    def test_avatar_endpoint_accepts_file_upload(self):
        user = get_user_model().objects.create_user(email='avatar@example.com', password='12345678', name='Avatar User')
        client = APIClient()
        client.force_authenticate(user=user)

        avatar = SimpleUploadedFile('avatar.png', b'fake-image-bytes', content_type='image/png')

        response = client.patch(
            '/api/usuarios/me/avatar/',
            {'avatar': avatar},
            format='multipart',
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(bool(user.avatar))

    def test_avatar_url_is_stored_without_becoming_media_path(self):
        user = get_user_model().objects.create_user(email='avatar-url@example.com', password='12345678', name='Avatar User')
        user.avatar = 'https://res.cloudinary.com/demo/image/upload/avatar.png'
        user.save(update_fields=['avatar'])

        user.refresh_from_db()
        self.assertEqual(user.avatar, 'https://res.cloudinary.com/demo/image/upload/avatar.png')
