from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    user  = models.ForeignKey(User, on_delete=models.CASCADE)
    category_name = models.TextField()

class Transaction(models.Model):
    user  = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField()
    counterparty = models.CharField(max_length=200)
    money_out = models.BooleanField()
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    

