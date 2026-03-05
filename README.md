# E-Commerce Brain

An AI-powered operations intelligence platform that analyzes sales performance through demand, supply, marketing, and customer signals.

## Data Architecture

The system uses a three-layer PostgreSQL database structure designed for fast reasoning and root-cause analysis.

```
postgres_db
│
├── operational_data          ← Mocked source systems
│   ├── orders
│   ├── inventory_snapshots
│   ├── marketing_campaigns_daily
│   └── support_tickets
│
├── analytics_data            ← Derived KPIs (brain layer)
│   └── daily_metrics
│
└── intelligence_data         ← AI system memory & decisions
    ├── incidents
    ├── agent_outputs
    ├── actions
    └── hitl_decisions
```

---

## Layer 1: Operational Data

Simulates real-world business systems that generate raw operational signals.

### Orders (`orders`)
Primary demand and revenue signal used to answer "Why did sales drop?"

| Column | Description |
|--------|-------------|
| order_id | Unique order identifier |
| order_timestamp | When order was placed |
| customer_id | Buyer identifier |
| region | Geography |
| order_value | Total order amount |
| product_count | Items per order |
| created_date | Date for aggregation |

### Inventory Snapshots (`inventory_snapshots`)
Supply availability tracking — the most common root cause of sales drops.

| Column | Description |
|--------|-------------|
| product_id | SKU identifier |
| snapshot_timestamp | Stock check time |
| available_stock | Units available |
| stock_threshold | Reorder level |
| is_out_of_stock | Boolean flag |
| out_of_stock_since | Timestamp (nullable) |

### Marketing Campaigns (`marketing_campaigns_daily`)
Marketing demand generation signals.

| Column | Description |
|--------|-------------|
| campaign_id | Campaign identifier |
| channel | Google / Meta / Email |
| date | Aggregation date |
| impressions | Views |
| clicks | Engagement |
| spend | Cost |
| conversions | Orders attributed |
| campaign_status | active / paused |

### Support Tickets (`support_tickets`)
Customer pain and friction signals.

| Column | Description |
|--------|-------------|
| ticket_id | Unique ticket identifier |
| created_timestamp | When raised |
| issue_category | delivery / product / website |
| sentiment | positive / neutral / negative |
| product_id | Related SKU (nullable) |
| customer_id | Who complained |

---

## Layer 2: Analytics Data (Brain Layer)

Derived KPIs enabling fast, cross-domain reasoning.

### Daily Metrics (`daily_metrics`)
Primary input for Supervisor and Self-Reflection agents.

| Column | Description |
|--------|-------------|
| date | Metric date |
| total_revenue | Sum of order_value |
| total_orders | Count of orders |
| avg_order_value | Revenue / orders |
| stockout_sku_count | SKUs out of stock |
| total_complaints | Ticket count |
| marketing_spend | Total spend |
| marketing_conversions | Orders attributed |

**Sales drops are decomposed as:**
- Fewer orders?
- Lower average order value?
- Stockouts?
- Marketing decline?
- Complaint spike?

---

## Layer 3: Intelligence Data

AI system memory, decisions, and audit trail.

| Table | Purpose |
|-------|---------|
| `incidents` | Stores user questions, final root causes, confidence scores, and supporting agents |
| `agent_outputs` | Each agent's findings, evidence, and confidence — used by Supervisor, Self-Reflection, and observability |
| `actions` | Proposed actions, execution status, and outcomes |
| `hitl_decisions` | Human approvals, rejections, reasons, and decision owners |

---

## Agent → Data Mapping

| Agent | Data Sources |
|-------|--------------|
| Sales Agent | orders, daily_metrics |
| Inventory Agent | inventory_snapshots, daily_metrics |
| Marketing Agent | marketing_campaigns_daily, daily_metrics |
| Support Agent | support_tickets, daily_metrics |
| Supervisor Agent | daily_metrics, agent_outputs, incidents |
| Self-Reflection Agent | agent_outputs, daily_metrics |

---



# AI Ops Brain — Day 1 MVP Backbone

## What’s implemented

- Canonical schemas for all agent outputs, root cause, action proposal, HITL decision, and memory record.
- LangGraph backbone: user input → supervisor → domain agents (parallel) → synthesis → self-reflection → HITL → final response.
- All nodes are class-based, modular, and ready for logic.
- Retry/fallback stubs are ready for extension.
- `.env.example` for environment variables.
- `settings.py` for global config
.

## How to run

This project can be run locally (dev), using Docker, or in a containerized environment. The repo contains a backend FastAPI service, a CLI tester (`backend/app.py`), a small React frontend (Vite), helper scripts, and a set of integration tests.

Recommended platform versions
- Python: 3.11 (matches Dockerfile)
- Node.js: 20.x (matches frontend Dockerfile)

Quick start — development (Python + frontend)
1. Copy `.env.example` to `.env` and fill in real values (do NOT commit secrets).
   - If a password contains special characters (e.g. `@`) URL-encode them when used in `DATABASE_URL` (e.g. `@` -> `%40`).
2. Create a virtual environment and install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.\\.venv\\Scripts\\activate  # Windows (PowerShell)
pip install --upgrade pip
pip install -r requirements.txt
```

3. Run the backend API locally (development):

```bash
# Runs uvicorn with the FastAPI app and honors settings in env
python backend/run_api.py
```

4. (Optional) Run the CLI graph test to exercise agents locally:

```bash
python backend/app.py
```

Frontend (local dev)
```bash
cd frontend
npm ci
npm run dev
# Open http://localhost:5173 (Vite default)
```

Docker / docker-compose
1. Build and start all services (Postgres, backend, frontend):

```bash
docker-compose up --build
# or: docker compose up --build
```

2. Services and ports (default)
- PostgreSQL: 5432
- Backend API: 8000 (docs at http://localhost:8000/docs)
- Frontend (served by nginx in container): 3000 -> port 80 inside container

3. Run in background and stop:

```bash
docker-compose up -d --build
docker-compose down
```

Database seeding
- A helper `scripts/seed_postgres.py` exists to create tables and seed example data. Edit its connection parameters at the top to point to your DB (or modify it to read DB connection from environment variables) and then run it:

```bash
python scripts/seed_postgres.py
```

Alternatively, when using `docker-compose`, you can connect to the `postgres` container and run SQL or copy/run the script inside a container.

MCP server
- Start the local MCP server (used for Model Context Protocol integrations):

```bash
python scripts/start_mcp_server.py
```

Testing

```bash
pytest
```

Logging
- Backend logs go to `logs/api.log` and `logs/api_errors.log` (created by `backend/run_api.py`). Create a `logs` directory if it doesn't exist:

```bash
mkdir -p logs    # Linux / macOS
md logs          # Windows (PowerShell)
```

Notes & troubleshooting
- Use `.env.example` as a template; never commit real secrets to git.
- If your `DB_PASSWORD` contains special characters, URL-encode them when used in `DATABASE_URL` (e.g. `password@123` -> `password%40123`).
- The `Dockerfile.backend` runs `uvicorn backend.api.app:app` — use `python backend/run_api.py` locally to match container behavior.

Contributing
- Please open issues or PRs for changes. Follow the existing code style and add tests for significant changes.

More details on architecture, data models, and agents are in the top sections of this README and in the repository's `backend/` modules.

## Next steps

- Implement Supervisor logic and routing (Day 2).
- Add agent reasoning and mock data (Day 3).


## Day 2 — Supervisor Agent (LLM Intent Classification)

- SupervisorAgent now uses an LLM to classify intent from the user question.
- Routing logic is dynamic: intent labels from the LLM determine which agents are called.
- Supervisor passes context and collects outputs from all called agents.
- All agent outputs are structured and stored in the state.
- Added tests for routing logic.