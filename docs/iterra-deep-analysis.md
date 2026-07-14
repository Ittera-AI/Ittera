# Iterra (Ittera) — Deep Forensic Analysis

> Verified against source on 2026-06-24. Where docs and code disagree, **code is the source of truth**; drift is flagged inline.
> Legend: **[CONFIRMED]** = verified in code · **[DOCS-ONLY]** = stated in docs, not matched by code · **[UNVERIFIED]** = could not confirm.

---

## 1. System overview

Iterra is an AI content-strategy platform that runs a closed lifecycle: **trend detection → planning → creation → performance analysis → strategy improvement**. The newest feature (`self-learning-content-loop`) closes that loop: published posts are pulled back, analyzed, synthesized into durable per-creator memory, and proven facts are promoted into the context used for the next generation.

### Four core modules — current maturity

| Module | Engine | Real LLM path | Fallback | Maturity (code-verified) |
|--------|--------|---------------|----------|--------------------------|
| Smart Content Calendar | `CalendarEngine` | Yes (gated `USE_ITERRA_AI_CALENDAR`) | **None** — raises `EngineError`/`ParseError` | Demo: deterministic mock unless flag on |
| Content Repurposing | `RepurposeEngine` | Yes | Mock (`_mock_repurpose`) on no-key/parse-fail | Functional with mock fallback |
| AI Engagement Coach | `EngagementCoach` | Yes | Heuristic (`_heuristic_analyze`) | Strong — full heuristic parity |
| Trend Radar | `TrendRadar` | Yes | Synthetic (`_synthetic_scan`) | Functional; synthetic trends by default |
| (loop) Insight synthesis | `InsightSynthesisEngine` | Yes | Heuristic (`_heuristic_synthesize`) | Strong — deterministic fallback |

Citations: `packages/ai-engine/iterra_ai/{calendar,repurpose,coach,radar,insight}/engine.py`; flag at `apps/api/config.py:104`.

---

## 2. Architecture

### Monorepo layout [CONFIRMED]

```
apps/api/          FastAPI backend (settings at apps/api/config.py, re-exported via app/config.py)
apps/web/          Next.js 14 App Router, Zustand, Tailwind
packages/ai-engine/    `iterra_ai` package — imported directly, never via HTTP
packages/shared-types/ generated TS types from OpenAPI
workers/celery/    Celery + Redis jobs (app.py, beat_schedule.py, tasks/)
infra/, docker-compose.yml, Makefile, scripts/
supabase/          Supabase auth config
.kiro/specs/       3 specs (stabilization-and-twitter, x-integration-hardening, self-learning-content-loop)
```

### Service boundaries

- **AI-as-package, not service [CONFIRMED]:** backend imports engines directly, e.g. `from iterra_ai import ...` (`packages/ai-engine/iterra_ai/__init__.py:3-17`). No internal HTTP between `apps/api` and `packages/ai-engine` was found.
- **Routers → services → engine [CONFIRMED, mostly]:** routers delegate to `app/services/*`; services instantiate engines. Minor leakage noted in §10.

### Request lifecycle — post analysis (representative) [CONFIRMED]

```
POST /api/v1/analytics/analyze/{post_id}
  → analytics router (Depends get_current_user)
  → analytics_service.analyze_post(db, user, post_id)        # app/services/analytics_service.py:59
      → 30-day freshness short-circuit (no LLM, no event)    # :84-97
      → EngagementCoach.analyze(CoachInput)                  # iterra_ai/coach/engine.py:75
      → persists PostAnalysis (1:1 Post)
      → _emit_auto_analysis_complete (loop trigger)          # :220-251
  → response dict → frontend store/hook/component
```

### Frontend one-way data flow [DOCS-ONLY / PARTIAL]

`component → hook → store (stores/product.store.ts) → service → services/api.ts`. The rule is documented in `CLAUDE.md`; a full audit of `apps/web` was out of scope here. Note there are **two** API clients: `apps/web/src/services/api.ts` (apiFetch, same-origin proxy) and `apps/web/src/lib/api.ts` (typed `api.*` namespaces). This duplication is a drift risk.

---

## 3. Tech stack & LLM provider — drift RESOLVED

**The product actually runs on an OpenAI-compatible "AIML" gateway, not Anthropic.** [CONFIRMED]

- `BaseEngine._call_llm` lazy-builds an **OpenAI SDK** client pointed at AIML:
  ```34:40:packages/ai-engine/iterra_ai/core/base_engine.py
              if self._client is None:
                  from openai import OpenAI
                  self._client = OpenAI(
                      api_key=os.getenv("AIML_API_KEY"),
                      base_url=os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1"),
                  )
  ```
- Default model: `os.getenv("AIML_MODEL", "gpt-4o-mini")` (`base_engine.py:103-104`).
- `core/client.py` exposes only `get_anthropic_client()` and **no engine imports it — it is dead code** (`packages/ai-engine/iterra_ai/core/client.py:6-15`).
- `ANTHROPIC_MODEL` (config default `claude-sonnet-4-5`, `config.py:101`) is **never referenced** in the engine package.
- Competitive + all prediction engines construct their own `OpenAI(...)` against AIML (e.g. `competitive/engine.py:303-307`).

**Drift to fix:** docstrings claim Anthropic Claude (`coach/engine.py:7,42`; `brand_profile/engine.py:1`), `ContentDraft.generation_model` defaults to `"claude-sonnet-4-5"` (`apps/api/app/models/content_draft.py`), and README/architecture docs assert Anthropic. **Reality: AIML gateway + `gpt-4o-mini`.** The Anthropic branch in `BaseEngine` (`messages.create`, lines 58-68) is latent and only activates if a non-`.chat` client is injected — not done anywhere in-repo.

Stack (verified from imports/config): Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 / pydantic-settings; SQLite default / Postgres prod; Redis + Celery; Next.js 14 + TS + Tailwind + Zustand; Supabase auth.

---

## 4. Data model (authoritative, from `apps/api/app/models/`)

14 model modules; `organization.py` defines multiple tables. DateTime convention: `utc_now()` is **timezone-aware** (`app/db/datetime_helpers.py:8-9`), but most columns are declared as **naive** `DateTime` (no `timezone=True`).

| Table | Module | Notable columns / constraints |
|-------|--------|-------------------------------|
| `users` | user.py | email unique+indexed; `primary_platform` default `linkedin`; identity mirror fields `brand_name/bio/target_audience/content_mission`; naive timestamps |
| `posts` | post.py | `source` NOT NULL default `"imported"` indexed (`'imported'`/`'iterra_published'`) (`post.py:21`); `platform_post_id` indexed (no model-level unique); engagement ints/float |
| `post_analyses` | post_analysis.py | `post_id` **unique** (1:1 Post); `created_at` **naive** (`post_analysis.py:21`) |
| `content_drafts` | content_draft.py | `post_id` FK→posts SET NULL (`:35`); `generation_model` default `claude-sonnet-4-5` (drift); publishing fields |
| `content_draft_media` | content_draft.py | FK draft+user CASCADE |
| `learned_insights` | learned_insight.py | **UniqueConstraint(user_id, platform)** `uq_learned_insight_user_platform`; `confidence` float; `candidate_facts` JSON; `version` int; `is_mock` int; upserted in place |
| `user_contexts` | user_context.py | append-only versioned; `version`, `change_source`, `is_active` (indexed), `platform_facts` JSON |
| `brand_profiles` | brand_profile.py | `user_id` **unique** (1:1); `profile` JSON; `drive_analysis_file_id` |
| `content_plans` | content_plan.py | `niche` indexed; `platforms`/`slots` JSON |
| `social_connections` | social_connection.py | tokens (encrypted conditionally — see §10); `scopes` JSON; `connection_metadata` JSON |
| `trend_snapshots` | trend_snapshot.py | **UniqueConstraint(niche)** |
| `waitlist` | waitlist.py | email unique; `access_approved`/`approved_at`/`approved_by` |
| `daily_analytics_snapshots`, `analytics_events` | analytics_snapshot.py | `created_at` **timezone-aware**; unique `(user_id, snapshot_date)` lives in migration, not model |
| `persona_profiles/sources/documents/insights` | persona.py | scrape→analyze chain; naive timestamps |
| `organizations/workspaces/competitors/approvals/predictions` (+members) | organization.py | all **timezone-aware** DateTime |

**ER essentials:** User 1—* Post 1—1 PostAnalysis; User 1—* ContentDraft *—1 Post (publish bridge); User 1—* LearnedInsight (one per platform); User 1—* UserContext (one active); User 1—1 BrandProfile.

Migration `010_self_learning_loop.py` [CONFIRMED] creates `learned_insights`, adds `content_drafts.post_id`, adds `posts.source`, with working `upgrade()` (`:21-68`) and `downgrade()` (`:71-85`).

---

## 5. API surface

**25 routers, all mounted** in `apps/api/main.py:48-72` [CONFIRMED] (corrects an earlier audit claiming 8 unmounted): auth, onboarding, context, linkedin, brand-profile, trends, content, analytics, waitlist, users, calendar, repurpose, coach, radar, social, sync, connect (social_oauth), persona, storage, organizations, workspaces, predictions, competitors, reports, approvals.

- Auth enforcement is **per-route** via `Depends(get_current_user)` (no global auth middleware — see §6).
- Public routes: `/health`, `GET/POST /api/v1/waitlist`, auth register/login/logout + OAuth callbacks, OAuth `connect/*/start|callback`.
- Admin gating only in waitlist router via `require_admin` against `ADMIN_EMAILS` (`apps/api/app/routers/waitlist.py:24-31`, endpoints `:130/:144/:162`).

---

## 6. Auth model [CONFIRMED]

Dual-JWT in `apps/api/app/dependencies/auth.py`:

1. **Supabase JWT** — HS256 with `SUPABASE_JWT_SECRET`, audience `"authenticated"` (`:29-43`); auto-creates a local `User` reusing the Supabase UUID (`_get_or_create_user_from_supabase`, `:54-94`).
2. **Legacy Iterra JWT** — HS256 with `SECRET_KEY`/`ALGORITHM` (`:46-51`); issued by `/auth/login|register`, also accepted via `ittera_token` cookie.
3. **Fallback** `_fetch_supabase_user` — calls Supabase `/auth/v1/user` when local decode fails (`:97-126`).

`get_current_user` order: Bearer-or-cookie → Supabase decode → Supabase REST → legacy decode → 401 (`:129-169`). `AuthMiddleware` exists but is a **no-op and not registered** (`app/middleware/auth.py:11-14`; only CORS is added in `main.py:39-45`).

---

## 7. Background jobs (Celery)

Registered in `workers/celery/app.py:11-20`: radar_scan, performance_sync, weekly_reports, scraper, twitter_sync, brand_profile, publisher, learning_loop.

**Beat schedule** (`workers/celery/beat_schedule.py`):

| Beat key | Task | Schedule | Gate | Default |
|----------|------|----------|------|---------|
| radar-scan-hourly | radar_scan.run_radar_scan | hourly | ENABLE_PLACEHOLDER_TASKS | off |
| performance-sync-daily | performance_sync.sync_performance_data | 02:00 | ENABLE_PLACEHOLDER_TASKS | off |
| weekly-reports-monday | weekly_reports.send_weekly_reports | Mon 08:00 | ENABLE_PLACEHOLDER_TASKS (+ requires ENABLE_LEARNING_LOOP at runtime) | off |
| linkedin-sync-all-users-daily | scraper.sync_all_linkedin_users | 03:00 | ENABLE_LINKEDIN_SYNC | off |
| analytics-snapshot-daily | compute_analytics.compute_all_users_snapshots | 01:00 | ENABLE_ANALYTICS_TASKS | **on** |
| analytics-cleanup-monthly | compute_analytics.delete_old_snapshots | 1st 04:00 | ENABLE_ANALYTICS_TASKS | on |
| schedule-optimization-daily | smart_scheduler.daily_schedule_optimization | 06:00 | ENABLE_SCHEDULER_TASKS | **on** |
| insight-cycle-daily | learning_loop.run_insight_cycle_all_users | 05:00 | ENABLE_LEARNING_LOOP | off |
| publishing-queue-every-five-minutes | publisher.process_publishing_queue | */5 min | **none (always on)** | — |

**Registration gaps [CONFIRMED]:** `compute_analytics`, `smart_scheduler`, `data_cleanup`, `storage_sync` are **not in the Celery `include` list** yet are referenced by beat (`compute_analytics`, `smart_scheduler`) — these beat entries will fail to dispatch unless imported elsewhere. `smart_scheduler.daily_schedule_optimization` uses `@shared_task` rather than the app task decorator. `data_cleanup`/`storage_sync` have no beat entries despite docstrings.

---

## 8. The self-learning-content-loop — end-to-end

### Flow [CONFIRMED]
```
publish (content_service.publish_now OR publisher.process_publishing_queue)
  → post_bridge_service.bridge_draft_to_post   # idempotent on (platform, platform_post_id); sets source=iterra_published
  → learning_loop.on_post_published.delay      # gated ENABLE_LEARNING_LOOP
     → pull_and_analyze_post (delays 1h/24h/72h, LEARNING_LOOP_PULL_DELAYS)
        → performance_sync.sync_single_post  → analytics_service.analyze_post
        → synthesize_user_insights (debounced 60s)
           → learning_insight_service (version-bumped LearnedInsight per user,platform)
           → fact_promotion_service.promote_facts (confidence ≥ 0.7 → versioned UserContext)
  → context_service injects "## What We've Learned (apply this)" into next system prompt
```
Both publish paths use `_bridge_and_enqueue_learning_loop` with retry-and-retain (`content_service.py:445-515`, `publisher.py:36-91,182-186`).

### `compute_engagement_rate` [CONFIRMED] (`workers/celery/tasks/performance_sync.py:196-222`)
Clamps negative interactions to 0; zero/empty denominator → `0.0`; rounds to 4 dp; rejects NaN/±inf. **Finite & non-negative for any denominator** — verified. **Gap:** design P8 also asserts `≤ 1.0`; the code does **not** cap at 1.0 and the test does not assert it.

### Correctness properties P1–P8 → tests

| Prop | Statement (short) | Test (file::function) | Status |
|------|-------------------|------------------------|--------|
| P1 | Exactly one Post per published draft (idempotent) | `test_post_bridge_properties.py::test_property1_exactly_one_post_per_natural_key` | Covered |
| P2 | Published draft always linked to a learnable Post | `test_post_bridge_properties.py::test_property2_published_draft_always_linked_to_learnable_post` | Covered |
| P3 | Auto-analysis never double-charges | `test_analysis_idempotency_properties.py::test_property3_auto_analysis_never_double_charges` | Covered |
| P4 | Synthesis monotonic & non-destructive | `test_learning_insight_properties.py::test_property4_synthesis_monotonic_and_non_destructive` | Covered |
| P5 | Only confident facts promoted; versioned+append-only | `test_fact_promotion_properties.py::test_property5_only_confident_facts_promoted` (+ `_versioned_and_append_only`) | Covered |
| P6 | Learnings reach the next prompt | `test_learning_injection_properties.py::test_property6_learnings_reach_the_next_prompt` (+ converse) | Covered |
| P7 | Platform isolation | `test_learning_insight_properties.py::test_property7_platform_isolation` | Covered |
| P8 | Engagement rate well-defined on any denominator | `test_engagement_rate_property.py::test_engagement_rate_is_well_defined_on_any_denominator` | Covered (upper-bound ≤1.0 NOT asserted) |

Plus `test_full_loop_integration.py` (happy-path closure + failing-stage isolation). **Untested:** Celery scheduling/debounce/beat fan-out, enqueue-retry, `send_weekly_reports`.

**Spec-vs-code drift:** `MIN_POSTS_FOR_SYNTHESIS = 5` (`learning_insight_service.py:46`) vs design example “e.g. 3”.

---

## 9. Configuration & feature flags (from `apps/api/config.py`)

| Flag | Default | Effect |
|------|---------|--------|
| `USE_ITERRA_AI_CALENDAR` | `False` | LLM calendar vs deterministic mock (`:104`) |
| `ENABLE_LEARNING_LOOP` | `False` | Gates loop orchestrator + weekly digest (`:110`) |
| `LEARNING_LOOP_PULL_DELAYS` | `[3600, 86400, 259200]` | Post-publish metric pull windows (`:111`) |
| `ENABLE_LINKEDIN_SYNC` | `False` | LinkedIn scrape beat (`:60`) |
| `ENABLE_PLACEHOLDER_TASKS` | (in beat_schedule) | radar/performance/weekly beats |
| `ENABLE_ANALYTICS_TASKS` | **on** (beat_schedule) | analytics snapshot/cleanup |
| `ENABLE_SCHEDULER_TASKS` | **on** (beat_schedule) | smart scheduler |

Other notable env: `DATABASE_URL` (default `sqlite:///./iterra.db`), `SECRET_KEY` (validator blocks insecure default **only in production**, `:38-47`), `SUPABASE_JWT_SECRET`/`SUPABASE_URL`/anon keys, `AIML_API_KEY`/`AIML_BASE_URL`/`AIML_MODEL`, OAuth creds (Twitter/LinkedIn/Instagram/Google), `ADMIN_EMAILS`, `ALLOWED_ORIGINS`. Env files loaded by absolute path from repo root + apps/api (`config.py:11-19`). Local: SQLite, flags mostly off. Prod: Postgres, SECRET_KEY enforced, loop/sync flags enabled via env.

---

## 10. Risks, tech debt & drift

| # | Issue | Where | Impact | Recommended fix |
|---|-------|-------|--------|-----------------|
| R1 | **Test isolation** — 16/16 loop tests pass per-module but fail together with `no such table: users` | `apps/api/tests/conftest.py:23-36` (session-scoped `create_all` on shared on-disk `test.db`, function-scoped sessions, no per-test transaction) | Full suite unreliable; CI flakiness | Use in-memory SQLite + `StaticPool` (shared conn) **or** wrap each test in a transaction with rollback **or** scope table create/drop per-module; delete stray `test.db` |
| R2 | **Full suite hangs** (>5 min, no output) | network-touching tests lacking mocks: `test_mock_mvp_flow.py`, `test_publishing_hardening.py`, `test_platform_preferences.py` (httpx/requests refs) | `pytest tests/` never finishes locally | Add `pytest-timeout` (e.g. `--timeout=30`), block sockets in tests (`pytest-socket`), mock all outbound HTTP |
| R3 | **LLM provider drift** — docs/docstrings say Anthropic Claude; code uses AIML + `gpt-4o-mini`; `get_anthropic_client` dead | `core/client.py`, `coach/engine.py:7,42`, `content_draft.generation_model` default, README/ARCHITECTURE | Misleading ops/cost assumptions | Update docs + docstrings; remove dead Anthropic client or wire it behind `LLM_PROVIDER` |
| R4 | **Naive datetime class-of-bug** | `PostAnalysis.created_at` and most naive `DateTime` columns; fix applied only in `analytics_service.analyze_post` (`:88-95`) | TypeError on aware−naive subtraction wherever else these are compared | Standardize on `DateTime(timezone=True)` + a migration, or centralize normalization helper used at all comparison sites |
| R5 | **Plaintext OAuth tokens** for refresh-tokenless flows | `social_oauth._upsert_connection:128-139` (LinkedIn/Instagram stored unencrypted) | Tokens readable if DB leaks | Encrypt all tokens; make read sites decrypt uniformly |
| R6 | **Supabase JWT passed as URL query param** to `connect/*/start?token=` | `social_oauth.py:188-238` | Access token leaks to server logs/referrer/history | Use short-lived one-time `state` exchange or POST; never put bearer tokens in query strings |
| R7 | **Fernet key derived from `SECRET_KEY`** via SHA-256 | `app/core/security.py:21-24` | Weak/rotating SECRET_KEY breaks decryptability; default key in non-prod weak | Dedicated `TOKEN_ENCRYPTION_KEY`; key rotation strategy |
| R8 | **Celery registration gaps** | `workers/celery/app.py:11-20` missing compute_analytics/smart_scheduler (beat-referenced) | Beat tasks silently fail to dispatch | Add to `include`; convert `@shared_task` to app task |
| R9 | **Prompt-versioning rule violations** | inlined prompts in `competitive/engine.py:47-299`, `radar/engine.py:25-28`, content uses caller prompt; non-`_Vn` constants in calendar/content/repurpose/radar | Breaks "prompts versioned in prompts/" convention; eval regressions | Move prompts to `iterra_ai/prompts/`, version constants |
| R10 | **Cost tracking not universal** | competitive + prediction engines bypass `CostTracker` (`competitive/engine.py`, `predictions/*`) | Untracked LLM spend | Route all engines through `BaseEngine._call_llm` or call `CostTracker.log` |
| R11 | **No retries/timeouts in BaseEngine** despite docstring claiming "retry logic in base engine" (`coach/engine.py:118`) | `core/base_engine.py:26-76` | Transient LLM failures fall straight to fallback; no request timeout | Add timeout + bounded retry/backoff |
| R12 | **Dual frontend API clients** | `apps/web/src/services/api.ts` vs `src/lib/api.ts` | Divergent auth/transport behavior | Consolidate to one client |
| R13 | **CORS `allow_methods/headers=["*"]` with credentials** | `main.py:39-45` | Broad surface; fine for dev, tighten for prod | Restrict methods/headers in prod |

---

## 11. Fast start for a new engineer

**Run (Docker):** `make dev` (web, api, worker, db, redis); `make stop`. **Manual API:** from `apps/api`, set `.env` (root or apps/api), `uvicorn main:app --reload` (defaults to SQLite, all flags off → safe demo mode).

**Test:**
- AI engine (fast, hermetic): `cd packages/ai-engine && python -m pytest -q` → **17 pass**.
- Backend per-module (reliable): `cd apps/api && python -m pytest tests/test_<module>.py -q`.
- Do **not** run the whole `apps/api` suite until R1/R2 are fixed (cross-module DB failures + network hang). 169 tests collected.

**Add a migration:** `make migrate` runs `alembic upgrade head`; author revisions with **both** `upgrade()` and `downgrade()` (pattern: `apps/api/app/db/migrations/versions/010_self_learning_loop.py`).

**Regenerate shared types:** after any schema change run `make types` (`scripts/gen_types.sh` → OpenAPI → `openapi-typescript`). Never hand-edit `packages/shared-types/src/index.ts`.

**Golden rules (from CLAUDE.md, enforced in review):** contracts before code; no business logic in routers; AI engine imported never HTTP-called; prompts versioned in `iterra_ai/prompts/`; no API calls from React components; migrations reversible; token usage logged.

---

## Verification status summary

- **Confirmed by running:** ai-engine 17/17 pass; learning-loop modules 16/16 pass individually; combined run fails with `no such table: users`; full `apps/api` suite collects 169 tests and hangs when run whole.
- **Confirmed by reading:** LLM=AIML/`gpt-4o-mini`; dual-JWT auth; 25 mounted routers; data model; loop wiring; flags/defaults; migration 010 up/down; analytics timezone fix.
- **Could not verify:** exact runtime LLM behavior against a live AIML key; full `apps/web` data-flow compliance; whether any deployment injects an Anthropic client at runtime.
