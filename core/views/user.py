from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from core.models import User
from core.serializers import UserRegistrationSerializer, UserSerializer, PublicProfileSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Ver o perfil de OUTRA pessoa (retrieve/by_username) nunca deve
        # vazar email, permissões etc. — só o /usuarios/me/ (uma @action
        # separada) usa o serializer completo pro próprio usuário.
        if self.action in ('retrieve', 'by_username'):
            return PublicProfileSerializer
        return UserSerializer

    def get_permissions(self):
        # Perfil público (retrieve/by_username) precisa ser visível sem
        # login — é o que aparece no link do autor de uma avaliação, por
        # exemplo, e quem está só navegando o site ainda não logou.
        if self.action in ('retrieve', 'by_username'):
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(
        summary="Perfil público por nome de usuário",
        description="Retorna nome e foto de um usuário a partir do seu username (usado na URL /usuarios/<username>).",
        responses={200: PublicProfileSerializer, 404: None},
    )
    @action(detail=False, methods=['get'], url_path=r'u/(?P<username>[\w-]+)')
    def by_username(self, request, username=None):
        user = get_object_or_404(User, username=username)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @extend_schema(
        summary="Dados do usuário autenticado",
        description="Retorna os dados do usuário autenticado.",
        responses={200: UserSerializer, 401: None},
    )
    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
    )
    def me(self, request):
        """Retorna os dados do usuário autenticado.

        Também aceita PATCH para atualizar a foto de perfil via /usuarios/me/.
        """
        if request.method == 'PATCH':
            user = request.user
            avatar = request.FILES.get('foto') or request.FILES.get('avatar')
            if not avatar:
                return Response({'detail': 'Nenhuma imagem enviada.'}, status=status.HTTP_400_BAD_REQUEST)

            user.avatar = avatar
            user.save(update_fields=['avatar'])
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Atualizar foto do usuário autenticado",
        description="Atualiza a foto de perfil do usuário autenticado.",
        responses={200: UserSerializer, 400: None, 401: None},
    )
    @action(
        detail=False,
        methods=['patch'],
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
    )
    def foto(self, request):
        """Atualiza a foto de perfil do usuário autenticado."""
        user = request.user
        avatar = request.FILES.get('foto') or request.FILES.get('avatar')
        if not avatar:
            return Response({'detail': 'Nenhuma imagem enviada.'}, status=status.HTTP_400_BAD_REQUEST)

        user.avatar = avatar
        user.save(update_fields=['avatar'])

        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['patch'],
        url_path='me/foto',
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
    )
    def foto_me(self, request):
        """Alias para atualizar a foto de perfil em /usuarios/me/foto/."""
        return self.foto(request)

    @extend_schema(
        summary="Atualizar foto via upload direto ou URL do Cloudinary",
        description="Aceita um arquivo enviado em multipart ou uma URL do Cloudinary para atualizar o avatar do usuário.",
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
        """Atualiza a foto de perfil do usuário com upload direto ou URL do Cloudinary."""
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
    """Endpoint para registro de novos usuários."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

# core/views.py

class UploadFotoPerfilView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        user = request.user
        foto = request.FILES.get('foto')

        if not foto:
            return Response(
                {'error': 'Nenhuma foto enviada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deleta foto antiga se existir
        if user.foto:
            user.foto.delete()

        user.foto = foto
        user.save()

        return Response({
            'mensagem': 'Foto atualizada com sucesso!',
            'foto_url': request.build_absolute_uri(user.foto.url)
        })