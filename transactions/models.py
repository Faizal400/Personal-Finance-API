from django.db import models
from django.contrib.auth.models import User
from django.db.models import UniqueConstraint

class Category(models.Model):
    user  = models.ForeignKey(User, on_delete=models.CASCADE)
    category_name = models.CharField(max_length=200)
    def __str__(self):
        return self.category_name

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
    def __str__(self):
        return self.counterparty
    class Meta:
        constraints = [ UniqueConstraint(
            name="unique_transaction",
            fields=["user", "amount", "timestamp", "counterparty", "money_out"],
            )
        ]