from rest_framework import viewsets
from .models import Transaction
from .serializers import TransactionSerializer
from classifier_engine.transaction_classifier import classify_transactions
from rest_framework.decorators import action
from rest_framework.response import Response

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='classify-transactions')
    def get_classified_transactions(self, request):
        # These fields must match the transaction shape the classifier engine expects.
        # The engine (classifier_engine/transaction_classifier.py) reads exactly these keys —
        # amount, timestamp, counterparty, money_out, description — so this list is the
        # coupling point between the DB layer and the engine. Update both together.
        txns = list(Transaction.objects.filter(user=self.request.user).values(
            'amount', 'timestamp', 'counterparty', 'money_out', 'description'))
        return Response(classify_transactions(txns))