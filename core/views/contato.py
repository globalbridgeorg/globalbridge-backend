from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import MensagemContatoSerializer


class ContatoCreateView(APIView):
    """Recebe mensagens do formulário público /contato (estudantes ou agências)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = MensagemContatoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
