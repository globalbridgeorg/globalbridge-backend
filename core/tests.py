from decimal import Decimal
import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import (
    Agencia,
    Avaliacao,
    Estado,
    ImagemGaleria,
    MensagemContato,
    Pais,
    Plano,
    Programa,
    SolicitacaoAgencia,
    SolicitacaoPaisAdicional,
    Tag,
    User,
)
from core.storage import SupabaseStorage, resolver_bucket_e_objeto


@override_settings(
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
    MEDIA_ROOT=tempfile.mkdtemp(prefix='gb-test-media-'),
    SUPABASE_URL='',
    SUPABASE_SERVICE_ROLE_KEY='',
)
class GlobalBridgeAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.pais_uk = Pais.objects.create(
            nome='Reino Unido',
            nome_ingles='United Kingdom',
            codigo_iso='GB',
            regiao='Europa',
            custo_de_vida='Alto',
            idioma='Inglês',
            cultura='Cosmopolita',
            descricao='Destino clássico.',
            imagem_url='https://example.com/uk.jpg',
            intercambistas=45000,
            universidades=160,
            ativo=True,
        )
        self.pais_ca = Pais.objects.create(
            nome='Canadá',
            nome_ingles='Canada',
            codigo_iso='CA',
            regiao='América do Norte',
            custo_de_vida='Médio',
            idioma='Inglês e Francês',
            cultura='Acolhedora',
            descricao='Ótimo para estudo e trabalho.',
            imagem_url='https://example.com/ca.jpg',
            intercambistas=52000,
            universidades=100,
            ativo=True,
        )
        self.estado_lon = Estado.objects.create(
            nome='Londres', cidade_principal='Londres', id_pais=self.pais_uk
        )
        self.tag = Tag.objects.create(categoria='perfil', valor='idiomas', label='Idiomas')
        self.programa = Programa.objects.create(
            nome='Curso de Idiomas',
            descricao='Imersão em inglês',
            duracao_min=4,
            duracao_max=24,
        )

        self.estudante = User.objects.create_user(
            email='estudante@test.com', password='Password123!', name='Letícia Santana'
        )
        self.estudante.avatar = 'https://randomuser.me/api/portraits/women/44.jpg'
        self.estudante.save(update_fields=['avatar'])

        self.outro_estudante = User.objects.create_user(
            email='outro@test.com', password='Password123!', name='Rafael Souza'
        )

        self.dono_agencia = User.objects.create_user(
            email='business@test.com', password='Password123!', name='Gestor Agência', tipo='agencia'
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com', password='AdminPassword123!'
        )

        self.agencia_ativa = Agencia.objects.create(
            nome='EF Education',
            descricao='Agência parceira ativa.',
            como_funciona='Atendimento completo.',
            contato='contato@ef.test',
            telefone='+44 20 1234',
            site='https://ef.test',
            endereco='Londres',
            data_cadastro=timezone.now(),
            ativo=True,
            id_estado=self.estado_lon,
            usuario=self.dono_agencia,
            imagem_capa='https://upload.wikimedia.org/example/london.jpg',
            layout=[{'tipo': 'hero', 'variante': 'banner'}],
            conteudo_blocos={'equipe': {'membros': [{'nome': 'Ana', 'cargo': 'Consultora', 'foto': 'https://randomuser.me/api/portraits/women/31.jpg'}]}},
        )
        self.agencia_ativa.paises_atendidos.add(self.pais_uk)
        self.agencia_ativa.tags.add(self.tag)

        self.agencia_oculta = Agencia.objects.create(
            nome='Demo Oculta',
            descricao='Não aparece no catálogo público.',
            data_cadastro=timezone.now(),
            ativo=False,
            id_estado=self.estado_lon,
        )
        self.agencia_oculta.paises_atendidos.add(self.pais_uk)

        self.plano = Plano.objects.create(
            id_agencia=self.agencia_ativa,
            id_programa=self.programa,
            preco=Decimal('9500.00'),
            descricao='4 semanas em Londres',
            inclui='Matrícula e material',
        )
        self.foto_galeria = ImagemGaleria.objects.create(
            agencia=self.agencia_ativa,
            imagem='https://upload.wikimedia.org/example/gal1.jpg',
            ordem=0,
        )
        self.avaliacao = Avaliacao.objects.create(
            nota=5,
            comentario='Experiência incrível em Londres, suporte excelente do início ao fim!',
            id_usuario=self.estudante,
            id_agencia=self.agencia_ativa,
        )

    def test_catalogo_publico_e_depoimentos(self):
        # Estatísticas
        res = self.client.get('/api/estatisticas/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['total_paises'], 2)
        self.assertEqual(res.data['total_agencias'], 1)

        # Listagem de agências oculta inativa e inclui capa
        res_ag = self.client.get('/api/agencia/')
        self.assertEqual(res_ag.status_code, 200)
        self.assertEqual(len(res_ag.data), 1)
        self.assertEqual(res_ag.data[0]['imagem_capa_url'], 'https://upload.wikimedia.org/example/london.jpg')

        # Detalhe da agência inclui programa_id, galeria com agencia_id e avaliacoes
        res_det = self.client.get(f'/api/agencia/{self.agencia_ativa.id}/')
        self.assertEqual(res_det.status_code, 200)
        self.assertEqual(res_det.data['planos'][0]['programa_id'], self.programa.id)
        self.assertEqual(res_det.data['galeria'][0]['agencia_id'], self.agencia_ativa.id)
        self.assertEqual(res_det.data['avaliacoes'][0]['autor_foto'], 'https://randomuser.me/api/portraits/women/44.jpg')

        # Depoimentos da home
        res_dep = self.client.get('/api/avaliacao/depoimentos/?limite=3')
        self.assertEqual(res_dep.status_code, 200)
        self.assertEqual(len(res_dep.data), 1)
        self.assertEqual(res_dep.data[0]['autor'], 'Letícia Santana')
        self.assertEqual(res_dep.data[0]['pais'], 'Reino Unido')

        # País detalhe com capa nas agências
        res_pais = self.client.get(f'/api/paises/{self.pais_uk.id}/')
        self.assertEqual(res_pais.status_code, 200)
        self.assertEqual(res_pais.data['agencias'][0]['imagem_capa_url'], 'https://upload.wikimedia.org/example/london.jpg')

    def test_registro_login_perfil_e_senha(self):
        res_reg = self.client.post(
            '/api/registro/',
            {'email': 'novo@test.com', 'password': 'Password123!', 'name': 'Novo Estudante'},
            format='json',
        )
        self.assertEqual(res_reg.status_code, 201)
        self.assertIn('access', res_reg.data)
        self.assertIn('refresh', res_reg.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res_reg.data['access']}")
        res_me = self.client.get('/api/usuarios/me/')
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.data['name'], 'Novo Estudante')
        self.assertFalse(res_me.data['is_admin'])

        # Atualizar nome via PATCH /usuarios/me/
        res_patch = self.client.patch('/api/usuarios/me/', {'name': 'Nome Atualizado'}, format='json')
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.data['name'], 'Nome Atualizado')

        # Atualizar senha autenticado
        res_pw = self.client.post('/api/usuarios/me/senha/', {'nova_senha': 'NovaSenhaSegura123!'}, format='json')
        self.assertEqual(res_pw.status_code, 200)

        # Login com nova senha
        res_tok = self.client.post(
            '/api/token/',
            {'email': 'novo@test.com', 'password': 'NovaSenhaSegura123!'},
            format='json',
        )
        self.assertEqual(res_tok.status_code, 200)

        # Excluir conta
        res_del = self.client.delete('/api/usuarios/me/')
        self.assertEqual(res_del.status_code, 204)
        self.assertFalse(User.objects.filter(email='novo@test.com').exists())

    def test_avaliacoes_favoritos_e_contato(self):
        # Contato público
        res_c = self.client.post(
            '/api/contato/',
            {
                'publico': 'estudante',
                'nome': 'João',
                'email': 'joao@test.com',
                'assunto': 'Dúvida',
                'mensagem': 'Quero saber sobre vistos.',
            },
            format='json',
        )
        self.assertEqual(res_c.status_code, 201)
        self.assertEqual(MensagemContato.objects.count(), 1)

        # Autentica estudante
        self.client.force_authenticate(user=self.estudante)

        # Minhas avaliações
        res_minhas = self.client.get('/api/avaliacao/minhas/')
        self.assertEqual(res_minhas.status_code, 200)
        self.assertEqual(len(res_minhas.data), 1)
        self.assertEqual(res_minhas.data[0]['agencia_nome'], 'EF Education')

        # Outro estudante não pode editar avaliação alheia
        self.client.force_authenticate(user=self.outro_estudante)
        res_forb = self.client.patch(f'/api/avaliacao/{self.avaliacao.id}/', {'nota': 1}, format='json')
        self.assertEqual(res_forb.status_code, 403)

        # Favoritos
        res_fav = self.client.post(
            '/api/favoritos/', {'tipo': 'agencia', 'objeto_id': self.agencia_ativa.id}, format='json'
        )
        self.assertEqual(res_fav.status_code, 201)
        self.assertEqual(res_fav.data['nome'], 'EF Education')

    def test_permissoes_business_e_planos(self):
        # Estudante comum não pode editar agência nem criar plano
        self.client.force_authenticate(user=self.estudante)
        self.assertEqual(
            self.client.patch(f'/api/agencia/{self.agencia_ativa.id}/', {'nome': 'Hack'}, format='json').status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                '/api/plano/',
                {'id_agencia': self.agencia_ativa.id, 'id_programa': self.programa.id, 'preco': '100.00', 'descricao': 'x'},
                format='json',
            ).status_code,
            403,
        )

        # Dono da agência pode editar página, gerenciar planos e ver painel
        self.client.force_authenticate(user=self.dono_agencia)
        res_upd = self.client.patch(
            f'/api/agencia/{self.agencia_ativa.id}/',
            {'descricao': 'Descrição atualizada', 'ativo': False},
            format='json',
        )
        self.assertEqual(res_upd.status_code, 200)
        self.agencia_ativa.refresh_from_db()
        self.assertEqual(self.agencia_ativa.descricao, 'Descrição atualizada')
        self.assertTrue(self.agencia_ativa.ativo)  # read-only!

        res_plano = self.client.post(
            '/api/plano/',
            {
                'id_agencia': self.agencia_ativa.id,
                'id_programa': self.programa.id,
                'preco': '12500.00',
                'descricao': 'Pacote 8 semanas',
                'inclui': 'Seguro e matrícula',
            },
            format='json',
        )
        self.assertEqual(res_plano.status_code, 201)

        res_painel = self.client.get(f'/api/agencia/{self.agencia_ativa.id}/painel/')
        self.assertEqual(res_painel.status_code, 200)
        self.assertEqual(res_painel.data['stats']['programas'], 2)

    def test_fluxo_solicitacao_e_painel_admin(self):
        # Usuário comum não acessa /api/admin-painel/dados/
        self.client.force_authenticate(user=self.estudante)
        self.assertEqual(self.client.get('/api/admin-painel/dados/').status_code, 403)

        # Envia solicitação de agência (usuário autenticado)
        novo_user = User.objects.create_user(email='novaag@test.com', password='Password123!', name='Carla')
        self.client.force_authenticate(user=novo_user)
        doc = SimpleUploadedFile('comprovante.pdf', b'%PDF-1.4 demo', content_type='application/pdf')
        res_sol = self.client.post(
            '/api/solicitacoes-agencia/',
            {
                'nome': 'Nova Bridge',
                'site': 'https://novabridge.test',
                'cidade': 'Toronto',
                'pais_sede': self.pais_ca.id,
                'paises_atendidos': [self.pais_ca.id],
                'nome_responsavel': 'Carla',
                'cargo_responsavel': 'Diretora',
                'email_responsavel': 'novaag@test.com',
                'descricao': 'Agência especializada no Canadá.',
                'documento': doc,
            },
            format='multipart',
        )
        self.assertEqual(res_sol.status_code, 201)
        sol_id = res_sol.data['id']

        # Consulta minha solicitação
        res_minha = self.client.get('/api/solicitacoes-agencia/minha/')
        self.assertEqual(res_minha.status_code, 200)
        self.assertEqual(res_minha.data['status'], 'pendente')

        # Solicitação de país adicional + mensagem
        sol_pais = SolicitacaoPaisAdicional.objects.create(agencia=self.agencia_ativa, pais=self.pais_ca)
        msg = MensagemContato.objects.create(
            publico='agencia', nome='Pedro', email='pedro@test.com', assunto='Parceria', mensagem='Olá!'
        )

        # Admin acessa painel e aprova tudo
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get('/api/admin-painel/dados/')
        self.assertEqual(res_admin.status_code, 200)
        self.assertEqual(len(res_admin.data['solicitacoesAgencia']), 1)
        self.assertEqual(len(res_admin.data['solicitacoesPais']), 1)
        self.assertEqual(len(res_admin.data['mensagens']), 1)

        # Proteção contra path traversal em /api/admin-painel/documento/
        self.assertEqual(self.client.get('/api/admin-painel/documento/?path=../secret.pdf').status_code, 404)
        doc_path = res_admin.data['solicitacoesAgencia'][0]['documento_path']
        res_doc = self.client.get(f'/api/admin-painel/documento/?path={doc_path}')
        self.assertEqual(res_doc.status_code, 200)
        self.assertTrue(res_doc.data['url'])

        # Aprova solicitação de agência
        res_ap = self.client.post(f'/api/admin-painel/solicitacoes-agencia/{sol_id}/aprovar/')
        self.assertEqual(res_ap.status_code, 200)
        sol_obj = SolicitacaoAgencia.objects.get(pk=sol_id)
        self.assertEqual(sol_obj.status, 'aprovado')
        self.assertIsNotNone(sol_obj.agencia_criada)

        # Aprova país adicional
        res_ap_pais = self.client.post(f'/api/admin-painel/solicitacoes-pais/{sol_pais.id}/aprovar/')
        self.assertEqual(res_ap_pais.status_code, 200)
        self.assertTrue(self.agencia_ativa.paises_atendidos.filter(id=self.pais_ca.id).exists())

        # Marca mensagem como lida
        res_msg = self.client.patch(f'/api/admin-painel/mensagens/{msg.id}/', {'lida': True}, format='json')
        self.assertEqual(res_msg.status_code, 200)
        self.assertTrue(res_msg.data['lida'])


class SupabaseStorageUnitTestCase(TestCase):
    def test_mapeamento_de_buckets(self):
        self.assertEqual(resolver_bucket_e_objeto('avatars/foto.jpg'), ('avatars', 'foto.jpg'))
        self.assertEqual(resolver_bucket_e_objeto('agencias/capas/a.jpg'), ('agencias', 'capas/a.jpg'))
        self.assertEqual(
            resolver_bucket_e_objeto('solicitacoes_agencia/documentos/c.pdf'),
            ('documentos-agencia', 'documentos/c.pdf'),
        )

    @override_settings(SUPABASE_URL='https://demo.supabase.co', SUPABASE_SERVICE_ROLE_KEY='srv-key')
    def test_url_externa_e_url_publica(self):
        storage = SupabaseStorage()
        self.assertEqual(
            storage.url('https://upload.wikimedia.org/teste.jpg'),
            'https://upload.wikimedia.org/teste.jpg',
        )
        self.assertEqual(
            storage.url('agencias/capas/capa.jpg'),
            'https://demo.supabase.co/storage/v1/object/public/agencias/capas/capa.jpg',
        )

    @override_settings(SUPABASE_URL='https://demo.supabase.co', SUPABASE_SERVICE_ROLE_KEY='srv-key')
    @patch('core.storage.requests.post')
    def test_upload_e_url_assinada_bucket_privado(self, mock_post):
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {'signedURL': '/object/sign/documentos-agencia/doc.pdf?token=abc'}

        storage = SupabaseStorage()
        signed = storage.url('solicitacoes_agencia/doc.pdf')
        self.assertEqual(
            signed,
            'https://demo.supabase.co/storage/v1/object/sign/documentos-agencia/doc.pdf?token=abc',
        )
