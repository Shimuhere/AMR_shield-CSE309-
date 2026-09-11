from rest_framework import serializers

from .forms import resolve_antibiotic
from .models import SaleRecord


class SaleRecordSerializer(serializers.ModelSerializer):
    antibiotic_name = serializers.CharField(write_only=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

    class Meta:
        model = SaleRecord
        fields = ['antibiotic_name', 'quantity']

    def validate_antibiotic_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError('This field may not be blank.')
        return name

    def create(self, validated_data):
        antibiotic = resolve_antibiotic(validated_data.pop('antibiotic_name'))
        # The pharmacy comes from the authenticated user, never from the payload.
        pharmacy = self.context['request'].user.pharmacy_profile
        return SaleRecord.objects.create(antibiotic=antibiotic, pharmacy=pharmacy, **validated_data)
