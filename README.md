# Iterra — AI Content Strategy Engine

> Stop guessing. Start strategizing.

Iterra is an AI-powered content strategy platform that guides the full content
lifecycle — from trend detection and planning through creation, performance
analysis, and iterative improvement. It is not another AI writing tool. It is
an intelligent system that acts as a content strategist.

---

## The Problem

AI tools have made content *generation* easy. Content *strategy* remains
entirely unsolved. Creators regularly struggle with the same questions:

- What should I post next?
- When should I post, and on which platform?
- Why did that post perform well — or poorly?
- How do I spot a trend before it's saturated?

The result is inconsistent growth, wasted creative effort, and burnout. Iterra
closes this gap.

---

## The Core Idea: Closed Content Intelligence Loop

```
Trend Signals  →  Content Strategy  →  Content Creation
                                                ↓
                              Strategy Improvement  ←  Performance Analysis
```

Most tools are one-way. Iterra builds a self-improving feedback loop that learns
which content patterns work best for each individual creator over time.

---

## The Four Modules

### Smart Content Calendar
A strategic planning engine that generates data-informed content plans based on
a creator's niche, audience, platform behavior, and historical engagement. Tells
you what to post, where to post it, when, and why.

### Content Repurposing Engine
Converts one core idea into multiple platform-optimised versions — LinkedIn
thought leadership, Twitter threads, Instagram carousel outlines, short-form
video scripts — without manual rewriting.

### AI Engagement Coach
Analyzes posts at a deeper level than metrics: hook strength, emotional tone,
readability, storytelling structure, and call-to-action presence. Tells you
exactly what worked, what weakened the post, and how to improve it.

### Trend Radar
Detects emerging topics before they become saturated by monitoring Reddit,
YouTube, and Google Trends. Surfaces timely content angles so creators can
engage with trends early.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand |
| Backend | FastAPI, Python 3.11+, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| AI Engine | Internal pip package (`iterra_ai`), OpenAI SDK |
| Background Jobs | Celery + Redis |
| Infra | Docker, docker-compose, Nginx |
| CI/CD | GitHub Actions |

---

## Repository Structure

This is a **monorepo** — all services live in one repository, separated by
top-level folder. One `git clone`, one `docker-compose up`, one PR queue.

```
iterra/
│
├── apps/
│   ├── web/                  # Next.js 14 frontend
│   └── api/                  # FastAPI backend
│
├── packages/
│   ├── ai-engine/            # Core AI modules — importable as iterra_ai
│   └── shared-types/         # Auto-generated TypeScript types from OpenAPI
│
├── workers/
│   └── celery/               # Async background jobs (Trend Radar scans, etc.)
│
├── infra/
│   ├── docker/               # Per-service Dockerfiles
│   ├── nginx/                # Reverse proxy config
│   └── k8s/                  # Kubernetes manifests (future scaling)
│
├── docs/
│   ├── adr/                  # Architecture Decision Records
│   ├── api/                  # Auto-generated OpenAPI reference
│   ├── onboarding/           # Getting started guide
│   └── research/             # Market research and competitor notes
│
├── .github/
│   ├── workflows/            # CI per service (web.yml, api.yml, ai-engine.yml)
│   ├── CODEOWNERS            # Auto-assign reviewers by folder
│   └── PULL_REQUEST_TEMPLATE.md
│
├── scripts/
│   ├── setup.sh              # One-command local setup
│   ├── seed_db.py            # Dev database seeding
│   └── gen_types.sh          # Regenerate shared-types from OpenAPI
│
├── .env.example              # Environment variable template
├── docker-compose.yml        # Local dev — all services together
├── Makefile                  # Common commands
└── CLAUDE.md                 # AI coding assistant context and agent personas
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.11+
- Git

### First-time Setup

Clone the repository and run the setup script. It handles everything:

```bash
git clone https://github.com/your-org/iterra.git
cd iterra
bash scripts/setup.sh
```

The setup script will:
1. Copy `.env.example` to `.env`
2. Start the database and Redis containers
3. Install all Python dependencies including the `iterra_ai` package
4. Install all Node dependencies
5. Run database migrations
6. Seed the development database with sample data
7. Start all services

The full setup should complete in under 15 minutes on a fresh machine.

### Manual Setup (step by step)

If you prefer to set up manually:

```bash
# 1. Copy environment variables
cp .env.example .env
# Edit .env and fill in your API keys

# 2. Start infrastructure
docker-compose up -d db redis

# 3. Install Python deps (backend + ai-engine)
cd apps/api && pip install -r requirements.txt
pip install -e ../../packages/ai-engine

# 4. Run database migrations
make migrate

# 5. Install frontend deps
cd apps/web && npm install

# 6. Generate TypeScript types from API
make types

# 7. Seed dev database
make seed

# 8. Start everything
make dev
```

---

## Daily Development

```bash
make dev      # Start all services (web :3000, api :8000, worker, db, redis)
make stop     # Stop all services
make test     # Run all tests (pytest + vitest)
make lint     # Run ruff (Python) + eslint (TypeScript)
```

### After changing the API schema

Any time you modify a Pydantic schema in `apps/api/app/schemas/`, regenerate
the shared TypeScript types so the frontend stays in sync:

```bash
make types
```

This runs `gen_types.sh` which exports the OpenAPI spec from FastAPI and
generates `packages/shared-types/src/index.ts`. Never edit that file manually.

### After changing a database model

Any time you modify a SQLAlchemy model in `apps/api/app/models/`, create and
run a migration:

```bash
# Inside apps/api/
alembic revision --autogenerate -m "describe your change"
# Review the generated migration file carefully before running it
make migrate
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values. All variables are
documented in `.env.example` with comments.

Key variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing secret — generate a strong random string |
| `OPENAI_API_KEY` | OpenAI API key for all AI modules |
| `ENVIRONMENT` | `development`, `staging`, or `production` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins |

Never commit `.env`. The `.gitignore` already excludes it. Only `.env.example`
is committed.

---

## Architecture Decisions

### Why a monorepo?

With a small founding team, a monorepo eliminates version mismatch problems
between services, makes cross-service changes atomic, and gives everyone full
visibility into the entire codebase. See `docs/adr/001-monorepo-structure.md`.

### Why is the AI engine a pip package, not a microservice?

The `packages/ai-engine/` directory is an installable Python package, not a
separate HTTP service. The backend imports it directly:

```python
from iterra_ai.calendar import CalendarEngine
```

This means zero network overhead between the API and the AI layer during
development, no second service to manage, and a clean module interface enforced
by Python imports rather than HTTP contracts. When usage grows and the AI
workload needs dedicated infrastructure, it can be extracted into a standalone
service — but that is a scaling problem for later.

### Why `shared-types/`?

The backend's Pydantic schemas are the single source of truth for the API
contract. Running `make types` exports the FastAPI OpenAPI spec and generates
TypeScript types into `packages/shared-types/`. The frontend imports all API
types from there. This eliminates the entire class of type drift bugs — where
the backend returns one shape and the frontend expects another.

---

## Code Architecture Rules

These are the conventions the entire codebase follows. They are enforced in
code review and by the agent personas in `CLAUDE.md`.

### Frontend (`apps/web/`)

Data flow is strictly one-directional:

```
API  →  services/  →  stores/  →  hooks/  →  components/
```

- **Components** render UI and call hooks. Nothing else.
- **Hooks** manage local loading/error state and call stores.
- **Stores** (Zustand) hold shared state and call services.
- **Services** make all API calls using the typed client in `services/api.ts`.

### Backend (`apps/api/`)

```
Router  →  Service  →  AI Engine / Database
```

- **Routers** handle HTTP only: validation, auth, response shaping.
- **Services** contain all business logic and call the AI engine.
- **Models** define the database schema. Never used directly in routers.
- **Schemas** define request and response shapes. Defined before implementation.

### AI Engine (`packages/ai-engine/`)

- Each module exposes one primary class with a typed `generate()` or `analyze()` method.
- All LLM prompts live in `iterra_ai/prompts/` as versioned constants. Never inline.
- All inputs and outputs are Pydantic models. No raw strings in or out.
- Token usage is logged on every call.

---

## Git Workflow

### Branches

| Branch | Purpose |
|---|---|
| `main` | Production. Protected. Merges here trigger production deploy. |
| `develop` | Integration. Protected. All features land here first. Auto-deploys to staging. |
| `feature/[initials]-[task]` | Day-to-day work. e.g. `feature/rs-calendar-ui` |
| `fix/[initials]-[what]` | Bug fixes. Branch from `develop`, merge back to `develop`. |
| `hotfix/[what]` | Critical production fixes. Branch from `main`, merge to `main` AND `develop`. |

### PR Rules

- Every PR must reference a GitHub Issue.
- CI must be green before merge — no exceptions.
- Keep PRs under 400 lines changed where possible.
- All merges to `develop` are squash merges for a clean linear history.
- `CODEOWNERS` automatically assigns the right reviewer for each folder.

---

## Running Tests

```bash
# All tests
make test

# Backend only
cd apps/api && pytest --cov=app tests/

# AI engine only
cd packages/ai-engine && pytest tests/

# Frontend only
cd apps/web && npm run test
```

---

## Services at a Glance

| Service | Local URL | Description |
|---|---|---|
| Web | http://localhost:3000 | Next.js frontend |
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI (dev only) |
| API Health | http://localhost:8000/health | Health check endpoint |
| Redis | localhost:6379 | Message broker for Celery |
| PostgreSQL | localhost:5432 | Primary database |

---

## Contributing

1. Check the open Issues and pick one (or create one before starting work).
2. Branch from `develop`: `git checkout -b feature/your-initials-task-name`
3. Write the code. Write the tests. Run `make lint` and `make test`.
4. If you changed the API schema, run `make types` and commit the result.
5. Open a PR against `develop`. Fill out the PR template completely.
6. Address review comments. Merge once CI is green and you have one approval.

For architectural changes or decisions that affect the whole team, write an
ADR in `docs/adr/` before writing code, and get agreement from the team first.

---

## License

Private — all rights reserved. Not open source.
