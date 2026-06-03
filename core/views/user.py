from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

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
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """ Retorna os dados do usuário autenticado."""
        user = request.user
        serializer = self.get_serializer(user)
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