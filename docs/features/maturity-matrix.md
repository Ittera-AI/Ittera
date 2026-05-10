# Feature maturity matrix

Snapshot of what is **stable enough for demo**, **in progress**, or **scaffolding only**. Refresh when shipping major slices.

| Area | Status | Notes |
|------|--------|--------|
| Auth (Supabase web + API JWT) | Demo-ready | Client session drives dashboard; API uses bearer tokens. |
| Brand profile CRUD + confirm | Demo-ready | Backend returns `drive_analysis_file_id` when set. |
| Content suggest / generate / drafts | Demo-ready | Mock-generation path; Drive-backed drafts optional in schema. |
| Calendar UI (scheduled/published) | Demo-ready | Derived from draft rows, not separate plan table. |
| Analytics + coach-on-post | Demo-ready | Heuristic / mock scoring depending on path. |
| Radar UI + API | Demo-ready | AI package radar engine still **experimental** (synthetic trends). |
| `/api/v1/calendar/generate` | Demo-ready | Deterministic mock by default; opt-in LLM via `USE_ITERRA_AI_CALENDAR` + Anthropic (`iterra_ai.CalendarEngine`). |
| `/api/v1/repurpose/` | Demo-ready | Uses **`iterra_ai.RepurposeEngine`** template path — not a production LLM stack yet (documented in OpenAPI). |
| LinkedIn mock connect/sync | Demo-ready | Mock posting path; not production LinkedIn API. |
| Social + Google Drive OAuth | In progress | Routers mounted; run staging checklist in `docs/runbooks/local-dev.md`. Drive token refresh enforced in `StorageService`. |
| Celery beat schedules | Off by default | Set `ENABLE_PLACEHOLDER_TASKS=true` only to run scheduled tasks during demos. |
| LinkedIn scrape worker | Demo-ready | `scrape_linkedin_posts` runs `linkedin_service.sync_mock_posts` against the API DB (real crawl TBD). |
| Product UI errors | Demo-ready | `ProductShell` surfaces `product.store` errors with dismiss. |
| CI / shared types | Maintained | API workflow runs offline OpenAPI export + `openapi-typescript` and fails on drift in `packages/shared-types/src/index.ts`. |

When in doubt, treat anything marked **experimental** in `packages/ai-engine` as non-production until evals and real data paths land.
