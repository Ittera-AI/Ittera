# Local development runbook

## Prerequisites

- Docker Desktop
- Python 3.11+ (for offline OpenAPI export and host-side pytest)
- Node.js 20+ (for web and `openapi-typescript`)

## Fast path (Docker)

From the repo root:

1. Copy env: `cp .env.example .env` and fill Supabase, DB, and keys as needed.
2. `docker-compose up -d db redis` then bring up `api`, `web`, `worker`, `beat` as you prefer, or use `docker-compose up --build`.

The **API** container mounts `./apps/api`, `./packages/ai-engine`, and `./scripts` so:

- Migrations: `docker-compose exec api alembic upgrade head`
- Seed: `docker-compose exec api python /scripts/seed_db.py`

## Type generation (no running API required)

```bash
python scripts/export_openapi.py
cd packages/shared-types && npx openapi-typescript openapi.json --output src/index.ts
```

On Unix-like shells you can use `bash scripts/gen_types.sh` (falls back to `curl` if offline export fails).

The web app imports generated types via path alias `@iterra/shared-types` (see `apps/web/tsconfig.json`).

## Celery / beat

- Worker image includes `workers/` under `/app/workers`.
- `PYTHONPATH` in the worker image includes `/app/apps/api` so tasks can `import app.*` (required for LinkedIn scrape → DB ingestion).
- Beat and worker read `ENABLE_PLACEHOLDER_TASKS` (default **false**). Leave it false unless you intentionally want scheduled no-op tasks during demos.

## Drive pipeline (staging check)

Use this checklist after configuring Google OAuth client + redirect URIs for your staging hostname.

1. **Connect** — Signed-in user visits `/api/v1/social/connect/google-drive`, completes OAuth with `prompt=consent` so Google returns a **refresh_token** on first consent.
2. **Folder IDs** — Confirm `SocialConnection.connection_metadata` has `iterra_folder_id` and `drafts_folder_id` (`GET /api/v1/storage/status` should show these when connected).
3. **Stale access token** — `StorageService` refreshes OAuth access tokens when `Credentials.expired` is true before listing, reading, writing, or deleting Drive files.
4. **Export** — Call `GET /api/v1/storage/export` after creating at least one Iterra-managed file under the folder; failures usually mean wrong folder metadata or revoked consent.
5. **Worker + DB URL** — The Celery worker must use the same `DATABASE_URL` as the API so `scrape_linkedin_posts` ingests rows the API can see.

If you run the worker directly on the host (not Docker), export `PYTHONPATH` to include `apps/api` at the repo root (same as Docker image).

## Common issues

- **Disk full / WSL swap errors** — free space; remove large `.next` caches under `apps/web` if needed.
- **Windows without `make`** — invoke `docker-compose`, `pytest`, and the Python/NPX commands above directly.
- **Dashboard redirect loops** — ensure `apps/web/src/proxy.ts` does not gate on legacy cookies; Supabase session is client-side.

See also the known-issue notes in `docs/onboarding/getting-started.md`.
