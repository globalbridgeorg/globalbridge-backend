from rest_framework.viewsets import ModelViewSet
from core.models import Programa
from core.serializers import ProgramaSerializer

class ProgramaViewSet(ModelViewSet):
    queryset = Programa.objects.all()
    serializer_class = ProgramaSerializer