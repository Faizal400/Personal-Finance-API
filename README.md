# Personal Finance API

![CI](https://github.com/Faizal400/Personal-Finance-API/actions/workflows/ci.yml/badge.svg)

A REST API that reads a user's transaction history and works out which counterparties are quietly draining their account — separating real subscriptions from ordinary spending habits.

**Live:** https://personal-finance-api-87kr.onrender.com/api/docs/
**Demo login:** `demo` / `demopassword123`

Bank apps tell you what you spent. They rarely tell you what's *committed* — the forgotten £9.99 that leaves every month without a decision. That's the gap this fills.

---

## Try it in 60 seconds

Everything runs from the live Swagger page — no install, no client needed.

1. Open **[/api/docs/](https://personal-finance-api-87kr.onrender.com/api/docs/)** (free tier — first load takes up to a minute to wake)
2. `POST /api/token/` → **Try it out** → username `demo`, password `demopassword123` → **Execute**
3. Copy the `access` token from the response
4. Click **Authorize** (top right) → paste `Bearer <token>` → **Authorize**
5. `GET /api/transactions/classify-transactions/` → **Try it out** → **Execute**

The demo account is seeded with transactions covering every case the engine handles — a clean subscription, one with a price rise, a variable-amount weekly shop, a frequent habit, irregular noise, and a salary that gets ignored.

---

## What comes back

```json
{
  "Netflix": {
    "classification": "subscription",
    "subscription_strength": 1.0,
    "recurring_strength": 0.645
  },
  "Tesco": {
    "classification": "recurring",
    "subscription_strength": 0.317,
    "recurring_strength": 0.626
  },
  "Argos": {
    "classification": "neither",
    "subscription_strength": 0.186,
    "recurring_strength": 0.329
  }
}
```

Every counterparty gets a label and two confidence scores. Nothing is a black box — each score decomposes into features you can inspect.

---

## The interesting problem

A weekly Tesco shop and a Netflix subscription look **identical in timing**. Same merchant, regular gaps, repeated. Timing alone can't tell them apart.

The separator is price. Netflix charges £9.99 every time. Tesco charges £23, then £51, then £38. So the engine asks two independent questions rather than one:

1. **Does this recur at all?** — measured on the gaps between payments
2. **Does it behave like a subscription?** — measured on how many *distinct* prices exist

Getting that wrong in either direction is a real failure. Flag Tesco as a subscription and the output is noise. Miss a real subscription and the whole point of the app is gone.

**→ [Full engine writeup](docs/ENGINE.md)** — the feature weights, the trade-offs, why it isn't ML, the evaluation, and where it breaks. That's where the actual thinking is.

---

## Architecture

```
classifier_engine/          pure Python — no Django imports, no framework
    transaction_classifier.py
    test_transaction_classifier.py

transactions/               Django app — the web layer
    models.py               Transaction, Category
    serializers.py          model ↔ JSON
    views.py                viewset + the classify endpoint
    tests.py                API integration tests
    management/commands/    seed_demo.py

config/                     settings, urls, wsgi
```

**The engine imports nothing from Django.** It takes plain dicts in and returns plain dicts out. That's deliberate — it means the detection logic is unit-testable in isolation with zero framework setup, and the web layer is genuinely just plumbing on top. The classify endpoint pulls rows from Postgres, hands them to the engine as dicts, and returns whatever comes back.

**Request path:** `URL → JWT auth check → viewset → queryset filtered to request.user → engine → JSON`

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/token/` | Exchange credentials for an access + refresh token |
| POST | `/api/token/refresh/` | Get a fresh access token |
| GET, POST | `/api/transactions/` | List or create transactions (yours only) |
| GET, PUT, PATCH, DELETE | `/api/transactions/{id}/` | Single transaction |
| GET | `/api/transactions/classify-transactions/` | Run the engine over your history |
| — | `/api/docs/` | Interactive Swagger UI |
| — | `/admin/` | Django admin |

Every endpoint except the token ones requires a valid JWT. Every query is scoped to the authenticated user — there's a test that proves user A can't see user B's data.

---

## Stack

Python · Django 5.2 · Django REST Framework · SimpleJWT · PostgreSQL · Gunicorn · WhiteNoise · drf-spectacular · GitHub Actions · Render

---

## Run it locally

```bash
git clone https://github.com/Faizal400/Personal-Finance-API.git
cd Personal-Finance-API
python -m venv venv && venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

Create `.env` in the project root:

```
SECRET_KEY=any-random-string-for-local-dev
DEBUG=True
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/pfa
```

Needs a local PostgreSQL with a database called `pfa`. Then:

```bash
python manage.py migrate
python manage.py seed_demo        # demo user + sample transactions
python manage.py runserver
```

Open http://127.0.0.1:8000/ — it redirects to the docs.

---

## Tests

```bash
python manage.py test
```

Seven tests, two layers, and they cover different things on purpose:

**Engine (unit)** — statistics on known inputs, grouping and the income filter, classification of known cases, the tentative fallback. Pure functions, no database, milliseconds to run.

**API (integration)** — a request with no token gets 401, an authenticated user gets 200 and their own data, and one user cannot see another's transactions. These fire real requests through the full path: routing, auth, viewset, queryset, serializer, response.

The engine tests guard the logic. The API tests guard the wiring. CI runs both on every push against a throwaway PostgreSQL.

---

## Engineering decisions

The reasoning matters more than the choices, so each one is a link into the detail rather than a claim here.

**Rule-based, not ML.** No labelled dataset exists, and every classification needs to be explainable and tunable. A model would capture more and justify less. → [full reasoning](docs/ENGINE.md#design-decisions--trade-offs)

**Engine decoupled from Django.** Detection logic imports no framework, so it can be tested, reasoned about, and eventually reused without dragging a web stack along.

**JWT over sessions.** Sessions need a server-side lookup on every request and a shared store across instances. A signed token proves identity on its own — any instance verifies it with maths, not a database hit. The trade-off is revocation: a valid token stays valid until it expires, which is why access tokens live 5 minutes and a refresh token covers the gap.

**PostgreSQL over SQLite.** SQLite is a file your code opens — perfect locally, zero setup. But it locks the whole database per write, and it lives *with* the code, so a deploy overwrites it. Postgres is a separate process that owns its data: many concurrent writers, and it survives deploys because the code was never near it. So: SQLite while it's one developer, Postgres the moment it's a deployed app.

**Deploy early, iterate small.** The pipeline went live with the thinnest working version. Every feature since lands on a foundation already proven green — so when something breaks, the surface area is one change, not ten.

---

## Known limitations

Honest list. Each of these is a real gap, not a hypothetical.

**Product**
- **No registration endpoint.** Users can only be created via admin or the seed command. There's no public signup.
- **No bulk import.** Transactions go in one at a time via the API or admin. CSV/Statement import (and the per-bank format differences that come with it) is scoped out. 

**Engine**
- Thresholds and weights were tuned on the same 7 groups used to evaluate them. 100% accuracy on that set proves the logic runs, not that it generalises.
- Same-day transactions produce a 0-day gap, which spikes timing variance and pushes the group toward *neither*.
- Annual subscriptions need 2+ years of history before periodicity is detectable.
- → [the rest, in detail](docs/ENGINE.md#known-limitations)

**Infrastructure**
- Free-tier hosting spins down after 15 minutes idle; the first request takes ~1 minute to wake.
- The free PostgreSQL instance expires 30 days after creation.
- `amount` is stored as `DecimalField` but the engine does float arithmetic on it. Harmless for the current statistics, wrong in principle for currency.
- The classify endpoint hand-selects engine fields via `.values(...)` — a manual coupling point between the DB layer and the engine that a schema-driven approach would remove.

---

## What I'd do next

**Bulk import with a partial-overlap report.** Transactions currently go in one at a time, which is nothing like how people actually get their data — they export a statement. The interesting part isn't parsing the file, it's the response: an import of 200 rows where 15 already exist should return "185 imported, 15 skipped" rather than failing wholesale or silently double-counting. The per-transaction uniqueness rule is already in place, so this builds directly on top of it.

Then **price clustering** to replace the distinct-price ratio, so a subscription whose amount drifts by pennies stops being misread as a variable-amount habit.
