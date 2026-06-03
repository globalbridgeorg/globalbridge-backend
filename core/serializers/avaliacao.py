from rest_framework import serializers 
from core.models import avaliacao

class AvaliacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = avaliacao
        fields = '__all__'