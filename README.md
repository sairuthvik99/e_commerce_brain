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

1. Copy `.env.example` to `.env` and add your DIAL API key.
2. Install dependencies:
    ```
    pip install pydantic langchain langgraph python-dotenv
    ```
3. Run the app:
    ```
    python backend/app.py
    ```

## Next steps

- Implement Supervisor logic and routing (Day 2).
- Add agent reasoning and mock data (Day 3).


## Day 2 — Supervisor Agent (LLM Intent Classification)

- SupervisorAgent now uses an LLM to classify intent from the user question.
- Routing logic is dynamic: intent labels from the LLM determine which agents are called.
- Supervisor passes context and collects outputs from all called agents.
- All agent outputs are structured and stored in the state.
- Added tests for routing logic.