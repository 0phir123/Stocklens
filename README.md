# StockLens — AI Backend (Agents + RAG + Insights API)

Production-style FastAPI backend with clean architecture (Ports/Adapters/Services), ready for agents, RAG, metrics, and finance analytics.

## Why
- Ship **maintainable** backends (SOLID, DI, tests, lint, type).
- Add domain logic via **adapters** without touching the core.
- Ready for **observability**, **caching**, and **CI/CD**.

## Architecture
api/ # FastAPI (controllers/routers only)
core/ # pure domain: ports (Protocols), entities, errors
services/ # application use-cases (compose ports)
adapters/ # infrastructure: providers, clients, storage
shared/ # config, logging, DI
tests/ # pytest: api, services, adapters

shell
Copy code

## Quickstart (local venv)
```bash
python -m venv .venv
# mac/linux: source .venv/bin/activate
# windows:   .\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -e ".[dev]"

# run tests
pytest -q

# run api (dev)
uvicorn api.main:app --reload
# -> http://localhost:8000/healthz
Pre-commit (format/lint/type on every commit)
bash
Copy code
pip install pre-commit
pre-commit install
pre-commit run --all-files
Dev via Docker & Compose (hot reload)
bash
Copy code
docker compose up --build
# -> http://localhost:8000/healthz
API (early skeleton)
GET /healthz → {"status":"ok"}

GET /v1/agent/ask?q=... → stub echo

(Week 2 adds /v1/insights/metrics/* with OOP ports/services/adapters.)

Workflow (Git)
Branches: main (green), feature/*

Commits: Conventional (feat, fix, chore, test, …)

CI: ruff + black + mypy + pytest (GitHub Actions)

Roadmap (high level)
Week 1: repo, tests, pre-commit, Docker dev

Week 2: OOP metrics port/service + finance adapters

Week 3: observability + caching

Week 4: CI/CD + hardened Docker + K8s

Week 5: analytics/backtests endpoints (integrate your scripts)

Week 6: security + UX + write-up

License
TBD

bash
Copy code

---

# Step 7 — Dev Docker & Compose (reposted, concise)

## `Dockerfile.dev`
```dockerfile
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip uv && uv pip install -e ".[dev]"

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
docker-compose.yml
yaml
Copy code
version: "3.9"
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
Run
bash
Copy code
docker compose up --build
# open http://localhost:8000/healthz
