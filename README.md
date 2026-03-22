# Iterra — AI Content Strategy Platform

Iterra helps creators and marketers plan, repurpose, and optimize their content using AI.

## Features

| Feature | Description |
|---------|-------------|
| **Content Calendar** | AI-generated content plans tailored to your niche and platforms |
| **Repurpose Engine** | Adapt content across Twitter, LinkedIn, Instagram, and more |
| **Engagement Coach** | Score and improve your content before posting |
| **Trend Radar** | Real-time trending topic detection for your niche |

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand |
| Backend | FastAPI, Python 3.11, SQLAlchemy, Alembic, PostgreSQL |
| AI Engine | `iterra_ai` (internal pip package), OpenAI SDK, LangChain |
| Workers | Celery + Redis |
| Infra | Docker, docker-compose, Nginx |

## Quick Start

```bash
git clone <repo-url> iterra && cd iterra
bash scripts/setup.sh
```

See [docs/onboarding/getting-started.md](docs/onboarding/getting-started.md) for the full guide.

## Development Commands

```bash
make dev       # Start all services
make stop      # Stop all services
make test      # Run all tests
make migrate   # Run database migrations
make types     # Regenerate TypeScript types from OpenAPI
make lint      # Lint all code
make seed      # Seed the database
```

## Project Structure

```
iterra/
├── apps/
│   ├── web/              # Next.js 14 frontend
│   └── api/              # FastAPI REST API
├── packages/
│   ├── ai-engine/        # iterra_ai Python package
│   └── shared-types/     # Auto-generated TS types
├── workers/celery/       # Background task workers
├── infra/                # Docker, Nginx, K8s
├── docs/                 # ADRs, onboarding, API docs
├── scripts/              # Setup, seed, type-gen scripts
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Architecture

See [docs/adr/001-monorepo-structure.md](docs/adr/001-monorepo-structure.md) for the monorepo architecture decision record.

## Contributing

1. Read [docs/onboarding/getting-started.md](docs/onboarding/getting-started.md)
2. Create a feature branch from `main`
3. Follow the PR checklist in [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)
4. Ensure CI passes before requesting review

## License

Private — All rights reserved.
