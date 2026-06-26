from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import User
from core.serializers import UserRegistrationSerializer, UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

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


class UserRegistrationView(CreateAPIView):
    """Endpoint para registro de novos usuários."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
