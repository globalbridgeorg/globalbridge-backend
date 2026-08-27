import logging
import secrets

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings

from core.emails import enviar_codigo_cadastro, enviar_codigo_login, enviar_redefinir_senha
from core.models import CodigoLogin, CodigoVerificacaoEmail, User

logger = logging.getLogger(__name__)

MENSAGEM_GENERICA = 'Se esse e-mail tiver uma conta, você vai receber as instruções em instantes.'


class SolicitarRedefinicaoSenhaView(APIView):
    """Pede o link de redefinição de senha por e-mail. Resposta sempre
    genérica (mesmo se o e-mail não existir) pra não vazar quais e-mails
    têm conta — é o que os principais provedores de auth fazem."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if email:
            try:
                usuario = User.objects.get(email=email)
                uid = urlsafe_base64_encode(force_bytes(usuario.pk))
                token = default_token_generator.make_token(usuario)
                link = f'{settings.FRONTEND_URL}/redefinir-senha?uid={uid}&token={token}'
                enviar_redefinir_senha(usuario, link)
            except User.DoesNotExist:
                pass
            except Exception:
                logger.exception('Falha ao enviar e-mail de redefinição de senha para %s', email)

        return Response({'detail': MENSAGEM_GENERICA})


class RedefinirSenhaView(APIView):
    """Confirma a redefinição: recebe uid+token do link do e-mail e a
    nova senha. Usa o mesmo PasswordResetTokenGenerator do Django admin
    (stateless, expira sozinho via PASSWORD_RESET_TIMEOUT)."""

    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get('uid') or ''
        token = request.data.get('token') or ''
        nova_senha = request.data.get('nova_senha') or ''

        try:
            usuario = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({'detail': 'Link inválido ou expirado.'}, status=400)

        if not default_token_generator.check_token(usuario, token):
            return Response({'detail': 'Link inválido ou expirado.'}, status=400)

        try:
            validate_password(nova_senha, user=usuario)
        except DjangoValidationError as exc:
            return Response({'detail': ' '.join(exc.messages)}, status=400)

        usuario.set_password(nova_senha)
        usuario.save(update_fields=['password'])
        return Response({'detail': 'Senha redefinida — já pode logar com a nova senha.'})


class SolicitarCodigoLoginView(APIView):
    """Gera e manda por e-mail um código de 6 dígitos pra login sem
    senha. Mesma resposta genérica de SolicitarRedefinicaoSenhaView, pelo
    mesmo motivo (não vazar quais e-mails têm conta)."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if email:
            try:
                usuario = User.objects.get(email=email)
                codigo = f'{secrets.randbelow(1_000_000):06d}'
                CodigoLogin.objects.create(usuario=usuario, codigo=codigo)
                enviar_codigo_login(usuario, codigo)
            except User.DoesNotExist:
                pass
            except Exception:
                logger.exception('Falha ao enviar código de login para %s', email)

        return Response({'detail': MENSAGEM_GENERICA})


class VerificarCodigoLoginView(APIView):
    """Troca um código válido por um par de tokens JWT — mesmo formato
    de /token/, pra o front não precisar tratar login por senha e por
    código de forma diferente depois de autenticado."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        codigo = (request.data.get('codigo') or '').strip()

        try:
            usuario = User.objects.get(email=email)
            registro = CodigoLogin.objects.filter(usuario=usuario, codigo=codigo).latest('criado_em')
        except (User.DoesNotExist, CodigoLogin.DoesNotExist):
            return Response({'detail': 'Código inválido ou expirado.'}, status=400)

        if not registro.valido():
            return Response({'detail': 'Código inválido ou expirado.'}, status=400)

        registro.usado = True
        registro.save(update_fields=['usado'])

        refresh = RefreshToken.for_user(usuario)
        return Response({'access': str(refresh.access_token), 'refresh': str(refresh)})


class SolicitarCodigoCadastroView(APIView):
    """Manda um código de 6 dígitos pro e-mail informado no cadastro,
    antes de criar a conta. Diferente do login por código, aqui avisamos
    se o e-mail já tem conta — nesse ponto do formulário isso ajuda quem
    está se cadastrando (evita preencher tudo pra falhar só no fim), não
    é o mesmo risco de vazar dado sensível que seria no login."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'detail': 'Informe um e-mail.'}, status=400)
        if User.objects.filter(email=email).exists():
            return Response({'detail': 'Este e-mail já está em uso.'}, status=400)

        codigo = f'{secrets.randbelow(1_000_000):06d}'
        CodigoVerificacaoEmail.objects.create(email=email, codigo=codigo)
        try:
            enviar_codigo_cadastro(email, codigo)
        except Exception:
            logger.exception('Falha ao enviar código de verificação de cadastro para %s', email)
            return Response({'detail': 'Não conseguimos enviar o código agora. Tente novamente.'}, status=502)

        return Response({'detail': 'Código enviado.'})


class VerificarCodigoCadastroView(APIView):
    """Confirma o código de verificação de cadastro. Não gera token —
    só libera esse e-mail pra criar a conta de verdade em /registro/,
    que confere de novo se existe um registro `verificado=True` recente
    (ver CodigoVerificacaoEmail.email_verificado_recentemente)."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        codigo = (request.data.get('codigo') or '').strip()

        try:
            registro = CodigoVerificacaoEmail.objects.filter(email=email, codigo=codigo).latest('criado_em')
        except CodigoVerificacaoEmail.DoesNotExist:
            return Response({'detail': 'Código inválido ou expirado.'}, status=400)

        if not registro.valido():
            return Response({'detail': 'Código inválido ou expirado.'}, status=400)

        registro.usado = True
        registro.verificado = True
        registro.verificado_em = timezone.now()
        registro.save(update_fields=['usado', 'verificado', 'verificado_em'])

        return Response({'detail': 'E-mail verificado.'})
