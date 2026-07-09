from rest_framework import serializers 
from core.models import Pais

class PaisSerializer(serializers.ModelSerializer):
    programas_disponiveis = serializers.IntegerField(required=False, allow_null=True, default=0)

    class Meta:
        model = Pais
        fields = '__all__'