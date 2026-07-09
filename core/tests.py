from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Agencia, Pais, Plano, Programa


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


class PaisApiTests(TestCase):
    def test_mais_procurados_returns_active_countries_with_programs_count(self):
        Pais.objects.create(
            nome='Brasil',
            codigo_iso='BR',
            custo_de_vida='Médio',
            idioma='Português',
            cultura='Cultura brasileira',
            descricao='Descrição do Brasil',
            imagem_url='https://example.com/brasil.png',
            intercambistas=2500,
            universidades=120,
            ativo=True,
        )
        Pais.objects.create(
            nome='Canadá',
            codigo_iso='CA',
            custo_de_vida='Alto',
            idioma='Inglês',
            cultura='Cultura canadense',
            descricao='Descrição do Canadá',
            imagem_url='https://example.com/canada.png',
            intercambistas=1900,
            universidades=95,
            ativo=True,
        )
        Pais.objects.create(
            nome='Alemanha',
            codigo_iso='DE',
            custo_de_vida='Médio',
            idioma='Alemão',
            cultura='Cultura alemã',
            descricao='Descrição da Alemanha',
            imagem_url='https://example.com/alemanha.png',
            intercambistas=1600,
            universidades=85,
            ativo=False,
        )

        client = APIClient()
        response = client.get(reverse('paises-mais-procurados'), {'quantidade': 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(all(item['ativo'] for item in response.data))
        self.assertIn('programas_disponiveis', response.data[0])
