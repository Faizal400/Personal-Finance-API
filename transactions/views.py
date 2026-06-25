from django.shortcuts import render
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
    def GetClassifiedTransactions(self, request):
        txns = list(Transaction.objects.filter(user=self.request.user).values('amount', 'timestamp', 'counterparty', 'money_out', 'description'))
        return Response(classify_transactions(txns))