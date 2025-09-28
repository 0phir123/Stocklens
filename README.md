# StockLens 🧠📈  
> **Modular AI backend** for insights, metrics, and RAG—built to demonstrate production-style architecture, not just a demo script.

[![CI](https://img.shields.io/badge/CI-GitHub_Actions-informational)]()
[![API](https://img.shields.io/badge/API-FastAPI-009688)]()
[![Vector](https://img.shields.io/badge/Vector-FAISS-2962FF)]()
[![Cache](https://img.shields.io/badge/Cache-Redis-DC382D)]()

## ✨ Why this project matters (for reviewers)
- **Clear boundaries**: Ports & Adapters; pure domain in `core/`; infra in `adapters/`.
- **Swapability**: replace finance adapters (FRED/Yahoo) with a dummy without touching routes.
- **Operational realism**: caching, retries, validation, observability, CI/CD, containers.
- **LLM done right**: tool-routed agent, RAG with citations, JSON-schema outputs + validator fallback.

---
## ✨ Why this project matters
- **Clear boundaries**: Ports & Adapters; pure domain in `core/`; infra in `adapters/`.
- **Swapability**: replace finance adapters (FRED/Yahoo) with a dummy without touching routes.
- **Operational realism**: caching, retries, validation, observability, CI/CD, containers.
- **LLM done right**: tool-routed agent, RAG with citations, JSON-schema outputs + validator fallback.

## ✨ Why this project matters
- **Clear boundaries**: Ports & Adapters; pure domain in `core/`; infra in `adapters/`.
- **Swapability**: replace finance adapters (FRED/Yahoo) with a dummy without touching routes.
- **Operational realism**: caching, retries, validation, observability, CI/CD, containers.
- **LLM done right**: tool-routed agent, RAG with citations, JSON-schema outputs + validator fallback.

## 🟡 Project status (honest snapshot)
**Working now**
- Market & macro data fetching via adapters (e.g., Yahoo Finance, FRED) for core series.
- Basic RAG pipeline: chunk → embed → FAISS retrieve → synthesize (cited response).
- API skeleton with `/healthz`, `/v1/agent/ask`, `/v1/insights/metrics/*`.

**Not yet implemented / In progress**
- Oservability, Prometheus metrics, Redis cache strategy, screener stub..
- Integrate enhanced FE, regimes, backtests, optimizer; analytics endpoints.
- Smarter article ingestion (crawler/feeds, dedupe, metadata enrichment).
- LLM tool that makes **outbound requests** autonomously (safe router + budget caps).
- hardened Docker, CI/CD, K8s/Helm
- Security (JWT, rate limits), UX polish, SECURITY.md, demo script 

  
**Notes**
- Active development; public API may evolve.
- Adapters are swappable—infra can be replaced without touching domain routes.
  
## 🏗 Architecture (high level)

```
flowchart LR
  Client[(Client / UI)] -->|HTTP JSON| API[FastAPI Controllers / DTOs]
  subgraph Application Layer
    SVC[services/* Use-Cases]
  end
  subgraph Domain (Pure)
    CORE[core/* domain + agents + rag + metrics + errors]
  end
  subgraph Infrastructure (Adapters)
    VEC[adapters/vector/faiss]
    RED[adapters/cache/redis]
    FRED[adapters/providers/fred]
    YF[yfinance adapter]
    DB[(Postgres)]
  end

  API --> SVC --> CORE
  CORE <---> VEC
  CORE <---> RED
  CORE <---> FRED
  CORE <---> YF
  SVC --> DB


api/ → FastAPI controllers & request/response models
core/ → domain logic (agent router, RAG, metrics, errors)
services/ → orchestration, use-cases, transactions
adapters/ → infra impls (FRED, yfinance, FAISS, Redis, Postgres)
shared/ → config, logging, DI container, utils
tests/ → pytest (unit, snapshot, property-based)

```
## 🤖 Agent & Router Flow (RAG + Metrics)
Router chooses RAG or Metrics (or other tools) via policy.

- RAG: chunking → embeddings → FAISS → synthesis with citations.

- Metrics: provider port (FRED/Yahoo) → resample/interp strategies → typed DTO.

- Guardrails: token budgets, schema validation, prompt-injection mitigations.


## 🚀 Quick Start


**Requirements:** Docker + Docker Compose (recommended), or Python 3.11+

```bash
# Clone
git clone https://github.com/<your-user>/stocklens.git
cd stocklens

# Dev stack: API + Redis + Postgres (+ optional FAISS volume)
docker-compose up --build

# Open docs:
# http://localhost:8000/docs

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # or: poetry install
uvicorn api.main:app --reload
```

## 📡 Example Endpoints

## 📡 Example Endpoints

| Purpose        | Method & Path                                                | Notes                                       |
|----------------|---------------------------------------------------------------|---------------------------------------------|
| Health         | `GET /healthz`                                               | liveness                                    |
| Ask Agent      | `POST /v1/agent/ask`                                         | body: `{ "question": "US GDP growth 2020?" }` |
| Metrics        | `GET /v1/insights/metrics/{series_key}?start=...&end=...`    | e.g., `macro.gdp_real_q`                    |
| Retrieve (RAG) | `POST /v1/insights/retrieve`                                 | natural language query → cited snippets     |




## ✅ Quality & Ops

- **Code Quality**: ruff, black, mypy; pre-commit hooks.
- **Testing**: pytest (unit, snapshot, property-based); mark network tests.
- **Caching**: Redis (TTL + stampede control).
- **Resilience**: timeouts, retries/backoff, circuit breaker.
- **Security**: JWT/API keys, rate limits, CORS, input sanitization, PI mitigations.
- **Observability**: structured logs (correlation IDs), OpenTelemetry traces (API + nodes), Prometheus (p95, error rate, cache hits).
- **CI/CD**: GitHub Actions → lint → typecheck → tests → build → container scan.

## 🔌 Providers & Ports (Finance demo)

- `MarketDataPort` & `MacroDataPort` with **adapters**:
- **FREDProvider**: GDP (GDPC1), CPI (CPIAUCSL), BAA spreads (resample M/Q).
 - **YahooFinanceProvider**: SPY, ^GSPC, TLT, GLD, SLV (adj close; monthly).
- Swap to a **DummyProvider** for tests/offline—no API changes required.


## 👤 Author

**Ophir Ackerman** — AI-Backend / Python / Infra  
LinkedIn: https://www.linkedin.com/in/ophir-ackerman  
Email: ophirackerman@gmail.com
