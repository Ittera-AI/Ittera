.PHONY: dev stop test migrate types lint seed help

# Default target
help:
	@echo "Iterra Development Commands"
	@echo "==========================="
	@echo "  make dev      Start all services (docker-compose up --build)"
	@echo "  make stop     Stop all services"
	@echo "  make test     Run all tests (pytest + vitest)"
	@echo "  make migrate  Run Alembic migrations"
	@echo "  make types    Regenerate TypeScript types from OpenAPI"
	@echo "  make lint     Lint Python (ruff) and TypeScript (eslint)"
	@echo "  make seed     Seed database with sample data"

dev:
	docker-compose up --build

stop:
	docker-compose down

test:
	@echo "🧪 Running API tests..."
	cd apps/api && pytest tests/ -v --tb=short
	@echo ""
	@echo "🧪 Running AI Engine tests..."
	cd packages/ai-engine && pytest tests/ -v --tb=short
	@echo ""
	@echo "🧪 Running Web tests..."
	cd apps/web && npm test

migrate:
	docker-compose run --rm api alembic upgrade head

types:
	bash scripts/gen_types.sh

lint:
	@echo "🔍 Linting Python (ruff)..."
	ruff check apps/api/
	ruff check packages/ai-engine/
	@echo ""
	@echo "🔍 Linting TypeScript (eslint)..."
	cd apps/web && npm run lint

seed:
	docker-compose run --rm api python /scripts/seed_db.py
