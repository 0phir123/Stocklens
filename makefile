# Run all checks (lint + type + tests)
check: lint type test

# Ruff + Black in check mode (no auto-fix)
lint:
	ruff check .
	black --check .

# Black + Ruff auto-fix
format:
	black .
	ruff check . --fix

# Strict type checking
type:
	mypy .

# Run test suite
test:
	pytest -q

# Run dev server locally
run:
	uvicorn api.main:app --reload

# Build and run dev containers (API + Redis)
compose-up:
	docker compose -f docker/docker-compose.yml up --build

compose-down:
	docker compose -f docker/docker-compose.yml down
