# Getting Started with Iterra

Welcome to the Iterra monorepo! This guide gets you from a fresh machine to a running development environment.

## Prerequisites

- Docker Desktop 4.x+
- Node.js 20+
- Python 3.11+
- Git

## Quick Start (Recommended)

```bash
git clone <repo-url> iterra
cd iterra
bash scripts/setup.sh
```

The setup script will:
1. Copy `.env.example` → `.env`
2. Start PostgreSQL and Redis in Docker
3. Install Python dependencies (including the `iterra_ai` package in editable mode)
4. Install Node dependencies
5. Run database migrations
6. Seed the database with sample data
7. Start all services

After the script completes:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Manual Setup

### 1. Environment Variables

```bash
cp .env.example .env
# Edit .env with your values (at minimum, set OPENAI_API_KEY)
```

### 2. Start Infrastructure

```bash
docker-compose up -d db redis
```

### 3. Install Python Dependencies

```bash
cd apps/api
pip install -r requirements-dev.txt
pip install -e ../../packages/ai-engine
```

### 4. Install Node Dependencies

```bash
cd apps/web
npm install
cd ../../packages/shared-types
npm install
```

### 5. Run Migrations

```bash
make migrate
```

### 6. Start Services

```bash
make dev
```

## Common Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start all services with Docker Compose |
| `make stop` | Stop all services |
| `make test` | Run all tests (Python + TypeScript) |
| `make migrate` | Run pending database migrations |
| `make types` | Regenerate TypeScript types from OpenAPI |
| `make lint` | Lint all Python and TypeScript code |
| `make seed` | Seed the database with sample data |

## Project Structure

```
iterra/
├── apps/web/          # Next.js 14 frontend
├── apps/api/          # FastAPI backend
├── packages/ai-engine/ # Python AI engines (iterra_ai)
├── packages/shared-types/ # Auto-generated TS types
├── workers/celery/    # Background task workers
├── infra/             # Docker, Nginx, K8s configs
└── docs/              # Documentation and ADRs
```

## Adding a New Feature

1. Update the AI engine in `packages/ai-engine/iterra_ai/<feature>/`
2. Add the FastAPI router in `apps/api/app/routers/<feature>.py`
3. Add the service in `apps/api/app/services/<feature>_service.py`
4. Run `make types` to regenerate TypeScript types
5. Add the frontend hook/store/service in `apps/web/`
6. Write tests at each layer
7. Open a PR using the PR template

## Troubleshooting

**Port conflicts:** Check if ports 3000, 8000, 5432, or 6379 are in use: `lsof -i :<port>`

**Database connection errors:** Ensure Docker is running and the `db` container is healthy: `docker-compose ps`

**Python import errors:** Ensure `iterra_ai` is installed: `pip install -e packages/ai-engine`

**Type errors after API change:** Run `make types` to regenerate `packages/shared-types/src/index.ts`
