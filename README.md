# Transaction Classifier Engine

## What It Does

Not all banking apps provide an easy-to-read breakdown of which places, apps, or counterparties are repeatedly eating away at a user's bank account. This engine provides a scored breakdown of which counterparties are repeatedly reducing a user's balance across their transaction history — flagging subscriptions and recurring payment habits so they can be surfaced, ranked, and acted on.

---

## The Core Distinction

The engine classifies each counterparty's transaction history into one of three groups: **subscription**, **recurring**, or **neither**.

A **subscription** is a uniform, cyclical scheduled payment — consistent time between payments and consistent pricing. A **recurring payment** is a frequent pattern of payments with low gap variance, but without the pricing uniformity of a subscription. Unlike subscriptions, recurring payments don't follow fixed pricing or fixed intervals.

The distinction is not trivial. A weekly Tesco shop and a Netflix subscription can look identical in timing — the engine uses price uniformity as the primary separator. The line between the two classes is genuinely blurry in some cases, and the engine makes a best-effort probabilistic classification rather than a definitive one.

The engine produces two scores — `subscription_strength` and `recurring_strength` — both scaled 0–1. If either score clears the threshold, the higher score determines the label. If neither clears it, the group is classified as **neither**.

Transaction groups with fewer than 4 distinct payment days are passed through a separate tentative classifier and labelled as **tentative subscription** or **tentative recurring**, reflecting lower confidence due to insufficient data.

---

## How It Works

1. **Input:** A flat list of transaction dictionaries, each containing `amount`, `timestamp`, `counterparty`, `money_out`, and `description`.

2. **Filter & group:** Income transactions (`money_out=False`) are excluded. Remaining transactions are grouped by counterparty. Groups with fewer than 3 transactions are dropped — insufficient data to detect any pattern.

3. **Sort:** Each group is sorted by timestamp, oldest to newest, so gap calculations are sequential.

4. **Compute statistics:** For each group, the engine computes:
   - `time_mean` — average number of days between consecutive payments
   - `time_stdev` — standard deviation of those gaps (how consistent the timing is)
   - `amount_mean` — average payment amount
   - `distinct_prices_percent` — ratio of distinct price values to total transactions

5. **Compute features:** Each feature is clamped to [0, 1]:
   - `sample_size` — how well the group fills a 7-transaction quota (`min(1, n/7)`)
   - `regularity_score` — how consistent the time gaps are (`1 / (time_stdev + 0.1)`)
   - `frequency_score` — how frequently payments occur (`1 / (time_mean + 1)`)
   - `price_uniformity` — how uniform pricing is (`1 - distinct_prices_percent`)
   - `frequency_penalty` — penalises subscriptions with average gaps under 13 days (`min(1, time_mean / 13)`)

6. **Compute recurring strength** (weighted linear sum):

   | Feature | Weight |
   |---|---|
   | frequency_score | 0.35 |
   | sample_size | 0.30 |
   | regularity_score | 0.25 |
   | distinct_prices_percent | 0.10 |

7. **Compute subscription strength** (weighted linear sum, then multiplied by frequency penalty):

   | Feature | Weight |
   |---|---|
   | regularity_score | 0.40 |
   | price_uniformity | 0.35 |
   | sample_size | 0.25 |

8. **Classify:** If either score exceeds the threshold (0.6), the higher score wins. On a tie, subscription takes priority (see design decisions). If neither score clears the threshold, the group is classified as neither.

9. **Tentative fallback:** Groups with fewer than 4 gap measurements are passed through a hard-threshold tentative classifier using `time_stdev`, `distinct_prices_percent`, and `time_mean` directly. These are labelled `tentative subscription` or `tentative recurring` to signal lower confidence.

10. **Evaluate:** Results are compared against a hand-labelled ground truth set to verify correctness and catch regressions when thresholds or weights change.

---

## Design Decisions & Trade-offs

**Rule-based over ML**

ML would generally be the stronger approach for this problem — it can capture subtle patterns, edge cases, and implicit rules that a hand-crafted system cannot. However, ML requires a large, truth-labelled dataset of transaction groups, which does not currently exist. At this foundation stage, explainability and tunability matter more than performance ceiling: every threshold and weight can be inspected and adjusted, and every classification decision can be traced. A black box would capture more, but couldn't be explained or corrected. Rule-based is the correct choice for this stage, not a consolation prize.

**Distinct-price-ratio over amount standard deviation**

Standard deviation measures variance in pricing, but low variance can occur in recurring habits too — a user who always spends around £4 at the same coffee shop will have low amount stdev, which would incorrectly push that group toward subscription. Distinct-price-ratio measures how many *different* price points exist relative to total transactions. It captures whether pricing is truly fixed (subscription-like) or just coincidentally similar (habit). A future improvement would cluster near-identical prices rather than requiring exact matches, but distinct-price-ratio is the correct signal for the current scale.

**Subscription wins on tied scores**

When `subscription_strength` and `recurring_strength` are equal, the engine labels the group as a subscription. Recurring payments are habits — the user makes them actively and consciously each time. Subscriptions are more automatic; users can forget they exist. A false subscription label (flagging a habit as a subscription) means the user investigates unnecessarily. A missed subscription label means a forgotten charge goes unnoticed. The latter is more harmful, so recall is biased toward subscription on ties.

**Frequency penalty on subscriptions**

Subscriptions are not frequent by nature — a subscription billing more than once every 13 days is unusual. The frequency penalty (`min(1, time_mean / 13)`) scales down subscription strength for high-frequency groups, preventing frequent habits from scoring highly as subscriptions purely through timing regularity.

**Tentative classifier for low-data groups**

With fewer than 4 gap measurements, strength scores are unreliable — small sample sizes produce volatile stdev values. Rather than defaulting these groups to neither, a separate hard-threshold classifier labels them as tentative, preserving the signal while communicating uncertainty to the caller.

**Income exclusion**

Transactions with `money_out=False` are excluded before any classification. A regular salary is uniform in timing and amount — without this filter, it would score as a subscription. These are not outgoing payments and carry no actionable information for the user.

---

## Evaluation

After completing the first iteration of the engine, a hand-labelled ground truth dataset was assembled covering seven counterparty groups across a range of cases: a clear subscription (Netflix), a subscription with a mid-period price change (Adobe), a borderline low-data case (PureGym), a regular but variable-amount recurring payment (Tesco), a frequent small-amount habit (Pret A Manger), an irregular cluster (Deliveroo), and a noise case (Argos).

The evaluation function compares engine output against these expected labels, normalising tentative labels before comparison. The current engine scores **7/7 — 100%**.

What this does not prove:

- **Thresholds may be overfitted.** The score threshold (0.6) and classifier thresholds were tuned against the same 7 groups used in evaluation. A larger, unseen dataset could expose failures.
- **The test set is small and deliberate.** Real transaction data will contain unanticipated cases not represented here.
- **Weights are not optimised.** The weighted sums were derived by reasoning, not mathematical optimisation. A different weighting might classify these 7 correctly but generalise differently.

---

## Known Limitations

- **Off-by-one on transaction count:** `num_days` receives the gap count (transactions − 1) rather than the actual transaction count, which slightly affects sample size scoring. To be corrected before Django integration.
- **Same-day transactions unhandled:** Multiple transactions on the same day produce a 0-day gap, spiking `time_stdev` and pushing the group toward neither. Not a practical issue for subscriptions but can affect frequent-habit detection.
- **Thresholds tuned on 7 groups only:** Both the score threshold and classifier thresholds were derived from the evaluation set, likely introducing overfitting. A larger unseen dataset may expose threshold failures.
- **Distinct-price-ratio is binary:** Subscriptions where every payment differs slightly (e.g. currency-converted charges) receive a ratio of 1.0 and may misclassify as recurring. A price-clustering approach is the correct fix and is parked for v2.
- **Annual subscriptions need 2+ years of data:** With only one or two data points the engine cannot detect periodicity. Annual charges with insufficient history fall through to neither.
- **Weights are reasoned, not derived:** The weighted sums were chosen by judgement. A different weighting may generalise better to unseen data.
- **Rule-based performance ceiling:** A machine learning approach trained on a large labelled dataset would handle most of these edge cases more robustly. The rule-based system is correct for this stage but has a lower ceiling.
