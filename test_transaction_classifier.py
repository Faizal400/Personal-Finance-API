from datetime import datetime
from transaction_classifier import group_by_counterparty, calculate_txn_stats, classify_group, classify_tentative_groups

def test_calculate_txn_stats_uniform():
    mean, stdev = calculate_txn_stats([30, 30, 30])
    assert mean == 30
    assert stdev == 0

def test_group_by_counterparty():
    groups = group_by_counterparty([
        {"amount": 2100.00, "timestamp": datetime(2026, 1, 1, 9, 0), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
        {"amount": 15.50, "timestamp": datetime(2025, 10, 1, 19, 0), "counterparty": "Deliveroo", "money_out": True, "description": "DELIVEROO"}
        ])
    assert len(groups) == 0


def test_classify_group():
    # fairly useless, this is what evaluation does.
    subscription_txn, p, a = classify_group(time_mean=29.6, time_stdev= 0.5477225575051661, num_days=5, price_history=[10.49, 10.49, 10.49, 9.99, 9.99, 9.99])
    recurring_txn, p , a = classify_group(time_mean=3, time_stdev=1.0, num_days=7, price_history=[4.5, 3.8, 5.2, 4.1, 4.8, 3.6, 5.0, 4.3])
    neither_txn, p , a = classify_group(time_mean=33.2, time_stdev=50.51930324143436, num_days=5, price_history=[34.99, 12.5, 67.0, 23.0, 89.99, 45.0])
    assert subscription_txn == "subscription"
    assert recurring_txn == "recurring"
    assert neither_txn == "neither"

def test_classify_tentative_groups():
    sub = classify_tentative_groups(4.242640687119285, 0.3333333333333333, 31)
    assert sub == "tentative subscription"
