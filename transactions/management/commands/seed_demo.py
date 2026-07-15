from datetime import datetime, timezone

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from transactions.models import Transaction

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demopassword123"

# Sample transaction data covering each classification case the engine handles:
# clear subscription, subscription with a price tier change, variable-amount
# recurring, frequent habit, irregular clusters, one-offs, and income (ignored).
DEMO_TRANSACTIONS = [
    # Netflix - clear subscription (monthly, stable amount, one price rise)
    {"amount": 9.99, "timestamp": datetime(2026, 1, 1, 14, 30, tzinfo=timezone.utc), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},
    {"amount": 9.99, "timestamp": datetime(2025, 12, 2, 14, 28, tzinfo=timezone.utc), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},
    {"amount": 9.99, "timestamp": datetime(2025, 11, 1, 14, 31, tzinfo=timezone.utc), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},
    {"amount": 10.49, "timestamp": datetime(2025, 10, 3, 14, 29, tzinfo=timezone.utc), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM PRICE INCREASE"},
    {"amount": 10.49, "timestamp": datetime(2025, 9, 2, 14, 30, tzinfo=timezone.utc), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},
    {"amount": 10.49, "timestamp": datetime(2025, 8, 3, 14, 32, tzinfo=timezone.utc), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},

    # Tesco - recurring but variable amounts (weekly shop, not a subscription)
    {"amount": 42.30, "timestamp": datetime(2026, 1, 5, 18, 45, tzinfo=timezone.utc), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 23.15, "timestamp": datetime(2025, 12, 29, 19, 10, tzinfo=timezone.utc), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 51.20, "timestamp": datetime(2025, 12, 21, 18, 30, tzinfo=timezone.utc), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 38.40, "timestamp": datetime(2025, 12, 14, 17, 55, tzinfo=timezone.utc), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 27.80, "timestamp": datetime(2025, 12, 6, 19, 20, tzinfo=timezone.utc), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 44.10, "timestamp": datetime(2025, 11, 30, 18, 15, tzinfo=timezone.utc), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},

    # PureGym - borderline: only 3 charges, monthly-ish, stable amount
    {"amount": 24.99, "timestamp": datetime(2025, 12, 15, 6, 0, tzinfo=timezone.utc), "counterparty": "PureGym", "money_out": True, "description": "PUREGYM LTD"},
    {"amount": 24.99, "timestamp": datetime(2025, 11, 10, 6, 1, tzinfo=timezone.utc), "counterparty": "PureGym", "money_out": True, "description": "PUREGYM LTD"},
    {"amount": 24.99, "timestamp": datetime(2025, 10, 12, 6, 2, tzinfo=timezone.utc), "counterparty": "PureGym", "money_out": True, "description": "PUREGYM LTD"},

    # Adobe - subscription with a price tier change partway through
    {"amount": 9.99, "timestamp": datetime(2025, 8, 5, 10, 0, tzinfo=timezone.utc), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},
    {"amount": 9.99, "timestamp": datetime(2025, 9, 5, 10, 0, tzinfo=timezone.utc), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},
    {"amount": 9.99, "timestamp": datetime(2025, 10, 5, 10, 0, tzinfo=timezone.utc), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},
    {"amount": 19.99, "timestamp": datetime(2025, 11, 5, 10, 0, tzinfo=timezone.utc), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS NEW PLAN"},
    {"amount": 19.99, "timestamp": datetime(2025, 12, 5, 10, 0, tzinfo=timezone.utc), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},
    {"amount": 19.99, "timestamp": datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},

    # Pret A Manger - frequent habit, small similar amounts
    {"amount": 4.50, "timestamp": datetime(2025, 12, 1, 8, 30, tzinfo=timezone.utc), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 3.80, "timestamp": datetime(2025, 12, 4, 8, 45, tzinfo=timezone.utc), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 5.20, "timestamp": datetime(2025, 12, 7, 8, 30, tzinfo=timezone.utc), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 4.10, "timestamp": datetime(2025, 12, 11, 8, 40, tzinfo=timezone.utc), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 4.80, "timestamp": datetime(2025, 12, 14, 8, 30, tzinfo=timezone.utc), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 3.60, "timestamp": datetime(2025, 12, 18, 8, 35, tzinfo=timezone.utc), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 5.00, "timestamp": datetime(2025, 12, 21, 8, 30, tzinfo=timezone.utc), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 4.30, "timestamp": datetime(2025, 12, 25, 8, 45, tzinfo=timezone.utc), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},

    # Deliveroo - irregular gaps, should classify as neither
    {"amount": 15.50, "timestamp": datetime(2025, 10, 1, 19, 0, tzinfo=timezone.utc), "counterparty": "Deliveroo", "money_out": True, "description": "DELIVEROO"},
    {"amount": 22.00, "timestamp": datetime(2025, 10, 11, 20, 0, tzinfo=timezone.utc), "counterparty": "Deliveroo", "money_out": True, "description": "DELIVEROO"},
    {"amount": 18.75, "timestamp": datetime(2025, 11, 25, 19, 30, tzinfo=timezone.utc), "counterparty": "Deliveroo", "money_out": True, "description": "DELIVEROO"},
    {"amount": 30.00, "timestamp": datetime(2025, 12, 15, 21, 0, tzinfo=timezone.utc), "counterparty": "Deliveroo", "money_out": True, "description": "DELIVEROO"},

    # Argos - irregular clusters, should classify as neither
    {"amount": 34.99, "timestamp": datetime(2025, 8, 1, 10, 0, tzinfo=timezone.utc), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 12.50, "timestamp": datetime(2025, 8, 3, 14, 0, tzinfo=timezone.utc), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 67.00, "timestamp": datetime(2025, 8, 5, 11, 0, tzinfo=timezone.utc), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 23.00, "timestamp": datetime(2025, 9, 20, 10, 0, tzinfo=timezone.utc), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 89.99, "timestamp": datetime(2026, 1, 15, 15, 0, tzinfo=timezone.utc), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 45.00, "timestamp": datetime(2026, 1, 17, 9, 0, tzinfo=timezone.utc), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},

    # One-offs - not enough occurrences to form a group
    {"amount": 3.50, "timestamp": datetime(2026, 1, 3, 9, 15, tzinfo=timezone.utc), "counterparty": "Costa Coffee", "money_out": True, "description": "COSTA COFFEE"},
    {"amount": 18.40, "timestamp": datetime(2025, 12, 20, 22, 30, tzinfo=timezone.utc), "counterparty": "Uber", "money_out": True, "description": "UBER TRIP"},
    {"amount": 45.00, "timestamp": datetime(2025, 11, 5, 15, 10, tzinfo=timezone.utc), "counterparty": "Shell", "money_out": True, "description": "SHELL UK"},

    # Salary - income, excluded from classification by the money_out filter
    {"amount": 2100.00, "timestamp": datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 12, 1, 9, 0, tzinfo=timezone.utc), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 11, 1, 9, 0, tzinfo=timezone.utc), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 10, 1, 9, 0, tzinfo=timezone.utc), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 9, 1, 9, 0, tzinfo=timezone.utc), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 8, 1, 9, 0, tzinfo=timezone.utc), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
]


def build_transactions(user: User, transaction_data: list[dict]) -> list[Transaction]:
    """Builds unsaved Transaction instances for the given user from raw dicts."""
    return [Transaction(user=user, **txn) for txn in transaction_data]


class Command(BaseCommand):
    help = "Creates a demo user with sample transactions for the public demo."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username=DEMO_USERNAME)

        if not created:
            self.stdout.write("Demo user already exists, skipping seed.")
            return

        user.set_password(DEMO_PASSWORD)
        user.save()

        transactions = build_transactions(user, DEMO_TRANSACTIONS)
        Transaction.objects.bulk_create(transactions)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created demo user '{DEMO_USERNAME}' with {len(transactions)} transactions."
            )
        )