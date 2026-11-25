from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import User
from core.serializers import PublicProfileSerializer, UserRegistrationSerializer, UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('retrieve', 'by_username'):
            return PublicProfileSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ('retrieve', 'by_username'):
            return [AllowAny()]
        if self.action == 'list':
            return [IsAdminUser()]
        return super().get_permissions()

    def _garantir_dono_ou_admin(self):
        obj = self.get_object()
        user = self.request.user
        if obj.id != user.id and not user.is_staff:
            raise PermissionDenied('Você só pode alterar a sua própria conta.')

    def perform_update(self, serializer):
        self._garantir_dono_ou_admin()
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.id != user.id and not user.is_staff:
            raise PermissionDenied('Você só pode apagar a sua própria conta.')
        instance.delete()

    @extend_schema(
        summary="Perfil público por nome de usuário",
        description="Retorna nome, foto e histórico público de um usuário a partir do seu username.",
        responses={200: PublicProfileSerializer, 404: None},
    )
    @action(detail=False, methods=['get'], url_path=r'u/(?P<username>[\w-]+)')
    def by_username(self, request, username=None):
        user = get_object_or_404(User, username=username)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @extend_schema(
        summary="Dados do usuário autenticado",
        description="GET retorna dados da conta; PATCH atualiza nome ou foto; DELETE apaga a conta permanentemente.",
        responses={200: UserSerializer, 204: None, 401: None},
    )
    @action(
        detail=False,
        methods=['get', 'patch', 'delete'],
        permission_classes=[IsAuthenticated],
        parser_classes=[JSONParser, MultiPartParser, FormParser],
    )
    def me(self, request):
        if request.method == 'DELETE':
            user = request.user
            agencia = getattr(user, 'agencia', None)
            if agencia is not None:
                agencia.delete()
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == 'PATCH':
            user = request.user
            campos = []
            avatar = request.FILES.get('foto') or request.FILES.get('avatar')
            if avatar:
                user.avatar = avatar
                campos.append('avatar')

            if isinstance(request.data, dict):
                if 'name' in request.data:
                    user.name = str(request.data.get('name') or '').strip()
                    campos.append('name')
                avatar_url = request.data.get('avatar_url')
                if isinstance(avatar_url, str) and avatar_url.startswith(('http://', 'https://')):
                    user.avatar = avatar_url
                    if 'avatar' not in campos:
                        campos.append('avatar')

            if not campos:
                return Response({'detail': 'Nenhum campo válido enviado.'}, status=status.HTTP_400_BAD_REQUEST)

            user.save(update_fields=campos)
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Alterar senha do usuário autenticado",
        description="Atualiza a senha da conta autenticada validando as regras de segurança do Django.",
        responses={200: None, 400: None, 401: None},
    )
    @action(
        detail=False,
        methods=['post'],
        url_path='me/senha',
        permission_classes=[IsAuthenticated],
        parser_classes=[JSONParser],
    )
    def alterar_senha(self, request):
        nova_senha = request.data.get('nova_senha') or ''
        try:
            validate_password(nova_senha, user=request.user)
        except DjangoValidationError as exc:
            return Response({'detail': ' '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(nova_senha)
        request.user.save(update_fields=['password'])
        return Response({'detail': 'Senha atualizada com sucesso.'}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Atualizar foto de perfil via upload ou URL",
        description="Aceita um arquivo enviado em multipart ou uma URL válida para atualizar o avatar do usuário.",
        responses={200: UserSerializer, 400: None, 401: None},
    )
    @action(
        detail=False,
        methods=['patch'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
        parser_classes=[JSONParser, MultiPartParser, FormParser],
    )
    def avatar_cloudinary(self, request):
        user = request.user

        avatar_file = request.FILES.get('avatar') or request.FILES.get('foto')
        if avatar_file:
            try:
                user.avatar.save(avatar_file.name, avatar_file, save=True)
            except Exception as exc:
                return Response(
                    {'detail': f'Erro ao processar imagem: {str(exc)}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        avatar_url = request.data.get('avatar_url') if isinstance(request.data, dict) else None
        if not avatar_url:
            return Response(
                {'detail': 'avatar_url ou um arquivo de imagem é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not avatar_url.startswith('http://') and not avatar_url.startswith('https://'):
            return Response(
                {'detail': 'URL inválida para avatar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user.avatar = avatar_url
            user.save(update_fields=['avatar'])
        except Exception as exc:
            return Response(
                {'detail': f'Erro ao processar imagem: {str(exc)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRegistrationView(CreateAPIView):
    """Endpoint para registro de novos usuários — já devolve par JWT pronto para login."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        refresh = RefreshToken.for_user(usuario)
        return Response(
            {
                'user': UserSerializer(usuario, context={'request': request}).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )
