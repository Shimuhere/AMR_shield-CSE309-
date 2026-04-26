from rest_framework import serializers
from .models import SaleRecord, Antibiotic, PharmacyProfile

class SaleRecordSerializer(serializers.ModelSerializer):
    antibiotic_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = SaleRecord
        fields = ['antibiotic_name', 'quantity']

    def create(self, validated_data):
        antibiotic_name = validated_data.pop('antibiotic_name')
        antibiotic, _ = Antibiotic.objects.get_or_create(name=antibiotic_name)
        # Pharmacy is determined by the logged-in user in the view
        pharmacy = self.context['request'].user.pharmacy_profile
        return SaleRecord.objects.create(antibiotic=antibiotic, pharmacy=pharmacy, **validated_data)
