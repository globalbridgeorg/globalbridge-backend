from rest_framework import serializers 
from core.models import Agencia

class AgenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agencia
        fields = '__all__'