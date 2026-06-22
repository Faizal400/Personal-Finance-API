from datetime import datetime
import pprint
import statistics

# Known patterns baked in:
# Netflix: 6 monthly charges, stable amount (~£9.99, one price rise to £10.49)
# Tesco: 6 weekly charges, highly variable amounts (£23-£51)
# PureGym: 3 charges, monthly-ish but slightly irregular (borderline case)
# One-offs: Costa, Uber, Shell (noise)

# TODO: num_days currently receives len(day_gaps) which is transactions - 1.
# Should receive len(transactions) for accuracy. Same-day transactions also
# not handled. Revisit before Django integration.

test_transactions = [
    # Netflix - clear subscription (monthly, stable)
    {"amount": 9.99, "timestamp": datetime(2026, 1, 1, 14, 30), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},
    {"amount": 9.99, "timestamp": datetime(2025, 12, 2, 14, 28), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},
    {"amount": 9.99, "timestamp": datetime(2025, 11, 1, 14, 31), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},
    {"amount": 10.49, "timestamp": datetime(2025, 10, 3, 14, 29), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM PRICE INCREASE"},
    {"amount": 10.49, "timestamp": datetime(2025, 9, 2, 14, 30), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},
    {"amount": 10.49, "timestamp": datetime(2025, 8, 3, 14, 32), "counterparty": "Netflix", "money_out": True, "description": "NETFLIX.COM"},
    
    # Tesco - recurring but variable (weekly shop, not a subscription)
    {"amount": 42.30, "timestamp": datetime(2026, 1, 5, 18, 45), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 23.15, "timestamp": datetime(2025, 12, 29, 19, 10), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 51.20, "timestamp": datetime(2025, 12, 21, 18, 30), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 38.40, "timestamp": datetime(2025, 12, 14, 17, 55), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 27.80, "timestamp": datetime(2025, 12, 6, 19, 20), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    {"amount": 44.10, "timestamp": datetime(2025, 11, 30, 18, 15), "counterparty": "Tesco", "money_out": True, "description": "TESCO STORES"},
    
    # PureGym - borderline (3 charges, monthly-ish but slightly irregular gaps)
    {"amount": 24.99, "timestamp": datetime(2025, 12, 15, 6, 0), "counterparty": "PureGym", "money_out": True, "description": "PUREGYM LTD"},
    {"amount": 24.99, "timestamp": datetime(2025, 11, 10, 6, 1), "counterparty": "PureGym", "money_out": True, "description": "PUREGYM LTD"},
    {"amount": 24.99, "timestamp": datetime(2025, 10, 12, 6, 2), "counterparty": "PureGym", "money_out": True, "description": "PUREGYM LTD"},
    
    # One-offs (noise)
    {"amount": 3.50, "timestamp": datetime(2026, 1, 3, 9, 15), "counterparty": "Costa Coffee", "money_out": True, "description": "COSTA COFFEE"},
    {"amount": 18.40, "timestamp": datetime(2025, 12, 20, 22, 30), "counterparty": "Uber", "money_out": True, "description": "UBER TRIP"},
    {"amount": 45.00, "timestamp": datetime(2025, 11, 5, 15, 10), "counterparty": "Shell", "money_out": True, "description": "SHELL UK"},

    # Salary - should be completely ignored (money_out=False)
    {"amount": 2100.00, "timestamp": datetime(2026, 1, 1, 9, 0), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 12, 1, 9, 0), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 11, 1, 9, 0), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 10, 1, 9, 0), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 9, 1, 9, 0), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},
    {"amount": 2100.00, "timestamp": datetime(2025, 8, 1, 9, 0), "counterparty": "Employer Ltd", "money_out": False, "description": "SALARY"},

    # Adobe - subscription but price doubles halfway through
    {"amount": 9.99, "timestamp": datetime(2025, 8, 5, 10, 0), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},
    {"amount": 9.99, "timestamp": datetime(2025, 9, 5, 10, 0), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},
    {"amount": 9.99, "timestamp": datetime(2025, 10, 5, 10, 0), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},
    {"amount": 19.99, "timestamp": datetime(2025, 11, 5, 10, 0), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS NEW PLAN"},
    {"amount": 19.99, "timestamp": datetime(2025, 12, 5, 10, 0), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},
    {"amount": 19.99, "timestamp": datetime(2026, 1, 5, 10, 0), "counterparty": "Adobe", "money_out": True, "description": "ADOBE SYSTEMS"},

    # Deliveroo - irregular gaps (10, 45, 20 days) - should be neither
    {"amount": 15.50, "timestamp": datetime(2025, 10, 1, 19, 0), "counterparty": "Deliveroo", "money_out": True, "description": "DELIVEROO"},
    {"amount": 22.00, "timestamp": datetime(2025, 10, 11, 20, 0), "counterparty": "Deliveroo", "money_out": True, "description": "DELIVEROO"},
    {"amount": 18.75, "timestamp": datetime(2025, 11, 25, 19, 30), "counterparty": "Deliveroo", "money_out": True, "description": "DELIVEROO"},
    {"amount": 30.00, "timestamp": datetime(2025, 12, 15, 21, 0), "counterparty": "Deliveroo", "money_out": True, "description": "DELIVEROO"},

    # Pret A Manger - frequent habit, every 3-4 days, similar small amounts
    {"amount": 4.50, "timestamp": datetime(2025, 12, 1, 8, 30), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 3.80, "timestamp": datetime(2025, 12, 4, 8, 45), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 5.20, "timestamp": datetime(2025, 12, 7, 8, 30), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 4.10, "timestamp": datetime(2025, 12, 11, 8, 40), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 4.80, "timestamp": datetime(2025, 12, 14, 8, 30), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 3.60, "timestamp": datetime(2025, 12, 18, 8, 35), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 5.00, "timestamp": datetime(2025, 12, 21, 8, 30), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},
    {"amount": 4.30, "timestamp": datetime(2025, 12, 25, 8, 45), "counterparty": "Pret A Manger", "money_out": True, "description": "PRET A MANGER"},

    # Irregular clusters - looks like it could be recurring but genuinely isn't
    {"amount": 34.99, "timestamp": datetime(2025, 8, 1, 10, 0), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 12.50, "timestamp": datetime(2025, 8, 3, 14, 0), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 67.00, "timestamp": datetime(2025, 8, 5, 11, 0), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 23.00, "timestamp": datetime(2025, 9, 20, 10, 0), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 89.99, "timestamp": datetime(2026, 1, 15, 15, 0), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
    {"amount": 45.00, "timestamp": datetime(2026, 1, 17, 9, 0), "counterparty": "Argos", "money_out": True, "description": "ARGOS"},
]

def get_timestamp(txn) -> datetime:
    """
    Returns the value under timestamp key in a given transaction dict.
    """
    return txn["timestamp"]

def group_by_counterparty(transactions: list[dict]) -> dict[str, list[dict]]:
    """
    Sorts all transactions into groups, given the transaction from the same counterparty has more than 3 transactions.
    """
    grouped = {}
    for txn in transactions:
        if not txn["money_out"]:
            continue
        counterparty = txn["counterparty"]
        if counterparty not in grouped:
            grouped[counterparty] = [] #make a bucket, then add on the line below
        grouped[counterparty].append(txn)
    recurring_transactions = {}
    for k, v in grouped.items():
        if len(v) >= 3:
            recurring_transactions[k] = sorted(v, key=get_timestamp)
    return recurring_transactions


def get_gaps(txn_group: dict, gap_type:str) -> list[float]:
    """
    Returns a list of "gaps" between the given gap_type list.
    """
    # gap type is given in original dict. For example, amount or timestamp. What we're trying to get.
    previous_instance = 0
    instance_gaps = []
    for i in range(0, len(txn_group)):
        txn = txn_group[i]
        if previous_instance == 0:
            previous_instance = txn[gap_type]
        else:
            instance_gap = 0
            if gap_type == "timestamp":
                instance_gap = (txn["timestamp"] - previous_instance).days
            else:
                instance_gap = abs(txn[gap_type] - previous_instance)
            instance_gaps.append(instance_gap)
            previous_instance = txn[gap_type]
    return instance_gaps

def get_recurring_instances(txn_group: dict, instance_type:str) -> list: # not always int depends on instance_type's data type.
    """
    Creates a list of recurring instance_types in transactions, and returns that list. 
    """
    instances = []
    for txn in txn_group:
        instances.append(txn[instance_type])
    return instances

def calculate_txn_stats(instances_list: list[int]) -> tuple[float, float]:
    """
    Given a list of instances, it returns statistics such as average and standard deviation.
    """
    avg_instance_gap = statistics.mean(instances_list)
    instance_stdev = statistics.stdev(instances_list)
    return avg_instance_gap, instance_stdev

def get_recurring_metrics(day_gaps: list, price_history: list) -> tuple[float,float,float,float]:
    # [time_mean, time_stdev, amount_mean, amount_stdev]
    """
    Computes mean and standard deviation for both day gaps and price history, returning all four values

    time_mean = the average day gap between a transaction. E.g 29.6 time_mean would be "29.6 days roughly between each transaction"
    time_stdev = how much the day gaps differ (higher stdev = higher variance of day gaps between transactions)
    amount_mean = average price across the entire history
    amount_stdev = how much the price variates (higher stdev = generally higher fluctation / changes of the pricing)
    """
    time_mean, time_stdev = calculate_txn_stats(instances_list=day_gaps)
    amount_mean, amount_stdev = calculate_txn_stats(instances_list=price_history)
    return time_mean, time_stdev, amount_mean, amount_stdev
# =======================
# classifying actual groups
# Use DATE ("timestamp") (specifically date gaps as dates aren't consistent in their true 1:1 form) & PRICE ("amount")

def classify_tentative_groups(time_stdev: float, distinct_prices_percent: float, time_mean:float) -> str:
    """
    Groups with low sample sizes are considered "tentative [subscription/recurring]". 
    Not exactly a subscription/recurirng, but can be considered
    """
    picked_tentative_classification = "neither"
    if time_stdev < 5 and distinct_prices_percent <= 0.45 and time_mean >= 6.5:
        picked_tentative_classification = "tentative subscription"
    elif time_stdev < 5: 
        picked_tentative_classification = "tentative recurring"
    return picked_tentative_classification


def classify_group(time_mean: int, time_stdev:float, num_days: int, price_history: list[int]) -> tuple[str, float, float]:
    """
    Falls into one of 3 groups:
    subcription, recurring, neither
    
    Low time_stdev AND low amount_stdev → subscription
    Low time_stdev AND high amount_stdev → recurring
    Everything else → neither
    """
    unique_prices = len(set(price_history))
    distinct_prices_percent = unique_prices/ len(price_history)

    score_threshold = 0.6
    picked_classification = "neither"

    sample_size = min(1, num_days/7)
    regularity_score = (1/(time_stdev + 0.1)) # how consistent the gaps are. time_stdev. A payment that always comes exactly every 7 days is more regular than one that comes every 3-14 days unpredictably.
    frequency_score = 1/(time_mean + 1) # how often. time_mean. A payment every 3 days is more frequent than one every 10 days.
    price_uniformity = 1 - distinct_prices_percent
    frequency_penalty = min(1, time_mean / 13)
    recurring_strength = min(1, (0.35*frequency_score) + (0.3*sample_size) + (0.25*regularity_score) + (0.1*distinct_prices_percent))
    subscription_strength = min(1, ((0.4*regularity_score) + (0.35*price_uniformity) + (0.25*sample_size)) * frequency_penalty)

    if recurring_strength > score_threshold or subscription_strength > score_threshold:
        if subscription_strength >= recurring_strength:
             # In case of a tie, subscription takes priority.
             # A false subscription (user investigates a habit) is less harmful
             # than a missed subscription (user forgets a recurring charge).
             picked_classification = "subscription"
        else:
            picked_classification = "recurring"
    if num_days <= 4:
        picked_classification = classify_tentative_groups(time_stdev=time_stdev, distinct_prices_percent=distinct_prices_percent, time_mean=time_mean)
    

    return picked_classification, subscription_strength, recurring_strength

expected_labels = {
    "Netflix": "subscription",
    "Tesco": "recurring",
    "PureGym" : "subscription",
    "Adobe": "subscription",
    "Deliveroo" : "neither",
    "Pret A Manger" : "recurring",
    "Argos" : "neither"
}

def evaluate_classifications(predicted_outputs: dict[str, str]) -> tuple[dict, float]:
    """
    Evaluates the known examples and checks if they fall under their correct values, as stated in `expected_labels`
    """
    pred_acc_match = {}
    total = 0
    total_true = 0
    for k, v in predicted_outputs.items():
            total +=1
            accurate_output = expected_labels[k]
            normalised_predicted_output = v.replace("tentative ", "")
            matched = normalised_predicted_output == accurate_output
            pred_acc_match.update({k: matched})
            if matched:
                total_true +=1
    return pred_acc_match, (total_true / total)*100

recurring_groups = group_by_counterparty(transactions=test_transactions)

predicted_outputs = {}
for group in recurring_groups:
    group_list: list  = recurring_groups[group]
    day_gaps: list = get_gaps(group_list, "timestamp")
    price_history: list = get_recurring_instances(group_list, "amount")
    print(f"{group} day gaps: {day_gaps}")
    print(f"{group} price history: {price_history}")
    time_mean, time_stdev, amount_mean, amount_stdev = get_recurring_metrics(day_gaps=day_gaps, price_history=price_history)
    print(f"{group} time mean: {time_mean}, time_stdev: {time_stdev}, amount_mean: {amount_mean}, amount_stdev: {amount_stdev} distinct prices: {len(set(price_history)) / len(price_history)}")
    group_classification, subscription_strength, recurring_strength  = classify_group(time_mean=time_mean, time_stdev=time_stdev, num_days=len(day_gaps), price_history=price_history)
    print(f"Subscription strength: {subscription_strength}")
    print(f"Recurring strength: {recurring_strength}")
    print(f"{group_classification}")
    predicted_outputs.update({group: group_classification})
    print("-"*50)
evaluation, percentTrue = evaluate_classifications(predicted_outputs=predicted_outputs)
pprint.pprint(evaluation)
print(f"Evaluation % Score: {percentTrue}")