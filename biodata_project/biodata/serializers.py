from rest_framework import serializers
from .models import Biodata

class BiodataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Biodata
        fields = '__all__'