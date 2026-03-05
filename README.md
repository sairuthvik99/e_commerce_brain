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



# MVP Backbone

## What’s implemented

- Canonical schemas for agent outputs, root cause, action proposals, HITL decisions, and memory records.
- LangGraph-based pipeline: user input → supervisor → domain agents (parallel) → synthesis → self-reflection → HITL → final response.
- Modular, class-based nodes and agent interfaces ready for implementing reasoning logic.
- Retry/fallback stubs and observability hooks are scaffolded for production readiness.
- `.env.example` is included as a template for environment configuration.

## How to run (developer guide)

This section is written for developers and covers local development, Docker-based runs, database setup and seeding, the MCP server, testing, and common troubleshooting.

Prerequisites
- Python 3.11
- Node.js 20.x (for frontend dev/build)
- Docker & Docker Compose (optional but recommended for full stack)
- PostgreSQL (if not using Docker Compose)

1) Environment configuration

- Copy the template and fill secrets (do NOT commit real secrets):

```bash
cp .env.example .env
```

- Important notes:
    - If a DB password contains special characters (e.g. `@`) URL-encode them when used in `DATABASE_URL` (e.g. `password@123` -> `password%40123`).
    - `DIAL_API_KEY` and provider keys are required for agent LLM access in most flows. For local testing you can stub these values, but some modules may raise on missing keys.

2) Backend — local development

- Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.\\.venv\\Scripts\\activate  # Windows (PowerShell)
pip install --upgrade pip
pip install -r requirements.txt
```

- Create a `logs` directory used by the backend logger (if not present):

```bash
mkdir -p logs        # macOS / Linux
md logs              # Windows (PowerShell)
```

- Ensure your database is available (local Postgres or via Docker). If using a local Postgres instance, set `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` in `.env`.

- Start the FastAPI backend (development):

```bash
python backend/run_api.py
```

Notes:
- `backend/run_api.py` configures loggers and runs `uvicorn` for the application defined at `backend.api.app:app`.
- The app exposes OpenAPI docs at `/docs` and a health endpoint at `${API_PREFIX:-/api/v1}/health`.

3) CLI smoke test

- A CLI tester that runs the LangGraph pipeline is available at `backend/app.py`:

```bash
python backend/app.py
```

4) Frontend — local development

```bash
cd frontend
npm ci
npm run dev
# Open http://localhost:5173
```

To build a production bundle:

```bash
npm run build
```

5) Docker / docker-compose (recommended for full-stack)

- Build and bring up the full stack (Postgres, backend, frontend):

```bash
docker-compose up --build
# or: docker compose up --build
```

- Common lifecycle commands:

```bash
docker-compose up -d --build   # start in background
docker-compose logs -f         # follow logs
docker-compose down            # stop and remove containers
```

- Default ports (docker-compose):
    - PostgreSQL: `5432`
    - Backend API: `8000` (docs: `http://localhost:8000/docs`)
    - Frontend (nginx): `3000` → container port `80`

6) Database seeding

- A seed helper exists at `scripts/seed_postgres.py`. It creates tables and inserts sample data. By default the script contains connection placeholders — update those values to point to your DB or modify the script to read from environment variables.

- Example: run the script against a DB container started by docker-compose:

```bash
docker-compose up -d postgres
docker-compose exec -T postgres bash -c "psql -U user -d ecommerce_db -c 'SELECT 1'"
# Or copy/run the seed script from a container that has python and psycopg2 available
```

7) MCP server

- Start the Model Context Protocol (MCP) server used by some integrations:

```bash
python scripts/start_mcp_server.py
```

8) Testing

- Run unit and integration tests with `pytest` from the repo root:

```bash
pytest
```

- Tests live under `tests/` and `tests/agent_tests/`.

9) Logging & observability

- The backend uses `loguru`. Runtime logs are written to `logs/api.log` and `logs/api_errors.log`. Configure environment logging variables or the logger setup in `backend/run_api.py` as needed.

10) Health checks and diagnostics

- API health endpoint: `${API_PREFIX:-/api/v1}/health`
- OpenAPI docs: `/docs`

## Project layout (key files)

- `backend/` — Python backend, LangGraph orchestration, agents, API routes and services.
- `backend/api/app.py` — FastAPI application factory.
- `backend/run_api.py` — Development entrypoint which configures logging and runs Uvicorn.
- `backend/app.py` — CLI test runner that executes the LangGraph pipeline for quick verification.
- `backend/settings.py` — Global settings loaded from environment variables.
- `frontend/` — React (Vite) application and static assets.
- `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml` — container definitions for building and running the stack.
- `scripts/seed_postgres.py` — DB seeding script (edit to fit your environment).
- `scripts/start_mcp_server.py` — starts the MCP server for context protocol integration.
- `requirements.txt` — Python dependencies.
- `tests/` — test suites and integration checks.

## Configuration & important environment variables

- The repository includes `.env.example` — use it as the authoritative reference. Key variables include:
    - `DIAL_API_KEY` — LLM provider key used by agents.
    - `AZURE_ENDPOINT`, `API_VERSION`, `AZURE_EMBEDDING_DEPLOYMENT`, `AZURE_OPENAI_DEPLOYMENT` — Azure / LLM settings.
    - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DATABASE_URL` — database connection settings.
    - `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`, `PINECONE_INDEX` — vector DB configuration (optional).
    - `LANGFUSE_*` — telemetry integration (optional).

## Common issues & troubleshooting

- Runtime error: `DIAL_API_KEY not found` — some modules call `Settings.validate()` and expect this key. Add a placeholder in `.env` if you are running only structural tests.
- DB connection failures — verify `DATABASE_URL` is correct and that special characters in the password are URL-encoded.
- If dependency installation on Linux inside Docker fails due to Windows-only packages, the `Dockerfile.backend` filters them out before `pip install`.

## Roadmap / planned improvements

- Add upstream supervisor decision logic and richer agent reasoning implementations.
- Improve automated CI for tests and container builds.
- Add example deployment manifests for k8s and CI/CD.

## Contributing

- Fork, create a feature branch, add tests, and open a PR. Include a clear description of changes and any migration or environment changes required.

If you'd like, I can also:
- Convert `scripts/seed_postgres.py` to read DB connection from environment variables and make it runnable out-of-the-box.
- Add a `Makefile` or shell scripts for common developer flows (dev, build, seed, test).
