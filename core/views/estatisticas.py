from django.db.models import Avg, Sum
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Agencia, Avaliacao, Pais


class EstatisticasView(APIView):
    """Números reais da plataforma para a seção de estatísticas da home —
    calculados a partir do banco, não fixos no frontend."""

    permission_classes = [AllowAny]

    def get(self, request):
        paises = Pais.objects.filter(ativo=True)
        nota_media = Avaliacao.objects.aggregate(media=Avg('nota'))['media']

        return Response({
            'total_paises': paises.count(),
            'total_agencias': Agencia.objects.filter(ativo=True).count(),
            'total_avaliacoes': Avaliacao.objects.count(),
            'total_intercambistas': paises.aggregate(total=Sum('intercambistas'))['total'] or 0,
            'nota_media': round(nota_media, 1) if nota_media is not None else None,
        })
