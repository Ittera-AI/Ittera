# ADR-001: Monorepo Structure

## Status

Accepted

## Context

Iterra is an AI Content Strategy Platform composed of a Next.js frontend, a FastAPI backend, an internal AI engine Python package, and Celery background workers. Each component has different runtime requirements and deployment targets, but they share types, contracts, and business logic.

We needed to decide how to organize the codebase: separate repositories per service, or a monorepo.

## Decision

We will use a **monorepo** with the following top-level layout:

- `apps/web` — Next.js frontend
- `apps/api` — FastAPI REST API
- `packages/ai-engine` — Internal pip package (`iterra_ai`) installed via `pip install -e`
- `packages/shared-types` — Auto-generated TypeScript types from the FastAPI OpenAPI spec
- `workers/celery` — Celery background task workers
- `infra/` — Docker, Nginx, and Kubernetes configs
- `docs/` — Architecture Decision Records, API docs, onboarding guides

The AI engine is a standalone installable package (`pyproject.toml`) rather than a module within `apps/api` so it can be versioned, tested, and evaluated independently without coupling to the HTTP layer.

## Consequences

**Positive:**
- Single source of truth for all code, contracts, and CI
- Atomic cross-service changes (e.g., schema change in Python reflected in TypeScript types in one PR)
- Shared CI configuration and tooling
- Easy local development with `docker-compose`

**Negative:**
- CI must be scoped by path to avoid running all pipelines on every commit
- Monorepo tooling (Turborepo, Nx) may be needed as the project scales
- All developers need to understand the full structure even if working on one area

## Alternatives Considered

1. **Polyrepo (separate repos per service):** Better isolation but requires coordinated releases, cross-repo PRs for shared changes, and duplicated CI setup.

2. **Nx/Turborepo monorepo:** More powerful tooling with build caching, but adds significant complexity for a small team at this stage. Can be adopted later if build times become a bottleneck.

3. **AI engine embedded in `apps/api`:** Simpler initially, but prevents independent versioning, evaluation, and reuse across future services (e.g., a mobile API).
