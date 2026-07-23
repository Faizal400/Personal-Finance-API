from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'timestamp', 'counterparty', 'money_out', 'description']

    def validate(self, data):
        user = self.context['request'].user
        exists = Transaction.objects.filter(
            user=user,
            amount = data['amount'],
            timestamp = data['timestamp'],
            counterparty = data['counterparty'],
            money_out = data['money_out'],
            ).exists()
        if exists:
            raise serializers.ValidationError("This transaction already exists.")
        return data