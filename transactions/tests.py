from datetime import datetime, timezone
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import Transaction

class TransactionAPITests(APITestCase):
    def test_no_token_returns_401(self):
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, 401)
    
    def test_authenticated_user_sees_their_transactions(self):
        # Arrange: make a user, give them a transaction, authenticate
        # Act: GET /api/transactions/
        # Assert: status 200, and the data contains their transaction
        user = User.objects.create_user(username='alice', password='testpass123')
        transactions = [ Transaction(user=user, amount=9.99, timestamp=datetime(2026,1,1,14,30, tzinfo=timezone.utc), counterparty='Netflix', money_out=True, description='NETFLIX.COM'),]
        Transaction.objects.bulk_create(transactions)
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, 200)
    
    def test_is_user_data_isolated(self):
        user_alice = User.objects.create_user(username='alice', password='testpass123')
        user_bob = User.objects.create_user(username='bob', password='testpass123')
        transactions_alice = [ Transaction(user=user_alice, amount=9.99, timestamp=datetime(2026,1,1,14,30, tzinfo=timezone.utc), counterparty='Netflix', money_out=True, description='NETFLIX.COM'),]
        transactions_bob = [ Transaction(user=user_bob, amount=23.99, timestamp=datetime(2026,5,1,14,30, tzinfo=timezone.utc), counterparty='Netflix', money_out=True, description='PureGym'),]
        Transaction.objects.bulk_create(transactions_alice)
        Transaction.objects.bulk_create(transactions_bob)
        self.client.force_authenticate(user=user_alice)
        response = self.client.get('/api/transactions/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['counterparty'], 'Netflix')

    def test_duplicate_transaction_rejected_for_same_user(self):
        user_alice = User.objects.create_user(username='alice', password='testpass123')
        transactions_alice = Transaction(user=user_alice, amount=9.99, timestamp=datetime(2026,1,1,14,30, tzinfo=timezone.utc), counterparty='Netflix', money_out=True, description='NETFLIX.COM')
        transactions_alice.save()
        payload = {
            "amount": "9.99",
            "timestamp": "2026-01-01T14:30:00Z",
            "counterparty": "Netflix",
            "money_out": True,
            "description": "NETFLIX.COM"
            }
        self.client.force_authenticate(user=user_alice)
        response = self.client.post('/api/transactions/', payload)
        self.assertEqual(response.status_code, 400)

    def test_identical_transaction_allowed_for_different_user(self):
        user_alice = User.objects.create_user(username='alice', password='testpass123')
        user_bob = User.objects.create_user(username='bob', password='testpass123')
        transaction_alice = Transaction(user=user_alice, amount=9.99, timestamp=datetime(2026,1,1,14,30, tzinfo=timezone.utc), counterparty='Netflix', money_out=True, description='NETFLIX.COM')
        transaction_alice.save()
        payload = {
            "amount": "9.99",
            "timestamp": "2026-01-01T14:30:00Z",
            "counterparty": "Netflix",
            "money_out": True,
            "description": "NETFLIX.COM"
            }
        self.client.force_authenticate(user=user_bob)
        response = self.client.post('/api/transactions/', payload)
        self.assertEqual(response.status_code, 201)
