# Audit Report — Production-Readiness & Security Hardening

> **Spec:** `production-readiness-security-hardening`
> **Deliverable:** 1 of 3 (Audit Report · Fix Plan · Go-Live Checklist)
> **Scope:** Platform-wide audit of the Iterra (Ittera) system — FastAPI backend (`apps/api`), Next.js frontend (`apps/web`), in-process AI package (`packages/ai-engine`), Celery workers (`workers/celery`), Supabase (`supabase/`), and infrastructure (`infra/`, `docker-compose.yml`).
> **Companion documents:** [`fix-plan.md`](./fix-plan.md), [`go-live-checklist.md`](./go-live-checklist.md)

## Purpose

This report enumerates verified findings across security, edge-cases, and operational readiness, derived from a line-by-line read of the repository. Each finding carries a severity, the exact file/location, a description, the impact, an area classification, and whether it is verified in code. Findings that overlap an existing spec reference that spec so work is not duplicated.

This document satisfies Requirement 14 (Audit Report deliverable):

- **14.1** — every finding has a severity, file/location, description, and impact.
- **14.2** — every finding is classified by area.
- **14.3** — findings verified in code are distinguished from those that could not be verified.
- **14.4** — findings already addressed by an existing spec reference that spec.

It also satisfies Requirement 2.4 (per-router authorization documentation) via the [Route-Scope Mapping](#route-scope-mapping-requirement-24) section and Requirement 10.2 (irreversible migration record) via finding **F-16**.

## Existing-spec context

This initiative deliberately **extends, and does not duplicate**, three existing specs. Where a concern is already hardened there, this report references it:

- **`iterra-platform-stabilization-and-twitter`** — general stabilization and the Twitter/X publish path (publish-queue immutability, bounded retries, `process_publishing_queue` registration).
- **`x-integration-hardening`** — X/Twitter publish hardening (media limits, secret-safe publish logs, X token encryption-at-rest, reconnect-required surfacing).
- **`self-learning-content-loop`** — publish → analyze → synthesize → inject loop (draft→post bridge, learning-loop idempotency).

## Severity scale

| Severity | Meaning |
|----------|---------|
| **Critical** | Exploitable now / data exposure. |
| **High** | Security or correctness gap likely to bite in production. |
| **Medium** | Hardening / operational gap. |
| **Low** | Hygiene. |

All findings below are **Verified in code** unless explicitly marked *Unverified*. The "Area" column uses the requirement areas (authentication, authorization, secrets, OAuth, rate limiting, CORS, error handling, background jobs, data integrity, migrations, observability, infrastructure, testing).

## Findings

| ID | Severity | Area | File / Location | Finding | Impact | Verified | Existing spec |
|----|----------|------|-----------------|---------|--------|----------|---------------|
| F-01 | Critical | Authentication | `apps/api/app/dependencies/auth.py` `_get_or_create_user_from_supabase` | User is looked up **by email** and returned with no check of the Supabase `email_verified` claim. | An attacker who registers a Supabase account with an unverified email equal to a legacy account's email inherits that account. | Yes | extends this spec (R1) |
| F-02 | High | Authentication | `apps/api/app/dependencies/auth.py` `_fetch_supabase_user` | REST fallback accepts the Supabase user response without re-checking audience/verified status; errors are swallowed (`except Exception: return None`). | Weakens identity guarantees when local JWT verify is bypassed. | Yes | — |
| F-03 | High | Rate limiting | `apps/api/main.py` (no `add_middleware` for rate limiting); `app/middleware/rate_limit.py` | `RateLimitMiddleware` exists but is **never registered**; it is also in-memory only, single-tier, and emits no `Retry-After`. | No active rate limiting in production; auth endpoints brute-forceable; limits would not hold across replicas. | Yes | — |
| F-04 | High | Authorization | `apps/api/app/middleware/auth.py` (`AuthMiddleware` is a no-op and unregistered) | Global auth is entirely per-route via `get_current_user`. A newly added router that forgets the dependency is silently public. | Risk of unprotected routes; needs an enumerated public allowlist + test. | Yes | — |
| F-05 | High | Error handling | `apps/api/main.py` (no exception handlers) | No global exception/validation handlers; no standardized `Error_Envelope`; no correlation id in errors. | Inconsistent error shapes; no client-to-log correlation; risk of detail leakage as routes grow. | Yes | — |
| F-06 | High | Observability | `apps/api/main.py` only `/health` | No readiness probe (DB/broker), no correlation-id middleware, no structured logging config. | Cannot gate orchestration on real readiness; hard to diagnose in production. | Yes | — |
| F-07 | High | OAuth | `apps/api/app/routers/social_oauth.py` `_make_connect_state` / `_decode_connect_state`, `linkedin_callback`, `instagram_callback` | Connect-state is a signed JWT with a 10-min `exp` but is **not bound to the browser session and not single-use** for LinkedIn/Instagram (only the Twitter PKCE verifier is single-use). | OAuth state replay/CSRF window for LinkedIn/Instagram connects. | Yes | `x-integration-hardening` (X path) |
| F-08 | Medium | OAuth | `apps/api/app/routers/social_oauth.py` `_resolve_start_user` still accepts `?token=` raw JWT; `_get_user_id_from_token` returns `f"...{payload}"` into popup error | Bearer JWT accepted in URL query (deprecated fallback) and fallback error embeds upstream payload in the browser message. | Token in URL/logs; minor upstream detail leak. R4.2/R4.5. | Yes | — |
| F-09 | High | Background jobs | `workers/celery/tasks/publisher.py` `process_publishing_queue` | Due drafts are selected then `db.refresh(draft)`'d — a re-read, **not a row-level lock**. No natural-key dedup before the platform call. | Concurrent beat runs could double-publish; a retry after partial success could create a duplicate post. R8.1/R8.5. | Yes | `iterra-platform-stabilization-and-twitter`, `self-learning-content-loop` |
| F-10 | Medium | Secrets | `apps/api/config.py` (`TOKEN_ENCRYPTION_KEY` default `""`); `app/core/security.py` `_multifernet` | Token encryption silently falls back to a `SECRET_KEY`-derived key when `TOKEN_ENCRYPTION_KEY` is unset; **no production validation** requires the dedicated key. | A single leaked `SECRET_KEY` compromises both JWT signing and token-at-rest. R3.2/R3.5. | Yes | `x-integration-hardening` |
| F-11 | Medium | Data integrity | `apps/api/app/routers/predictions.py` (`datetime.utcnow()`), `app/services/storage_service.py` (`google_datetime.utcnow()`), `app/services/reporting_service.py` (`datetime.now()`) | Naive/machine-local datetimes used where aware UTC values are compared/stored. | Offset-naive/aware subtraction errors and timezone-dependent behavior. R9.2/R9.4. | Yes | — |
| F-12 | Medium | Infrastructure | `infra/nginx/nginx.conf` | Listens on `:80` only; **no TLS, no HTTP→HTTPS redirect, no HSTS or security headers**. | Plaintext traffic; missing transport hardening. R12.1/R12.2. | Yes | — |
| F-13 | Medium | Infrastructure | `docker-compose.yml` | No CPU/memory limits; healthchecks only for `db`/`redis`, **not** api/worker/web; Postgres creds `iterra/iterra` inline. | No resource bounds; orchestration can't gate on app health; local creds pattern must not reach prod. R12.3/R12.4/R12.6. | Yes | — |
| F-14 | Medium | Testing | `apps/api/tests/conftest.py` | No outbound-network guard, no per-test timeout, single shared in-memory DB with manual cleanup (no per-test rollback isolation). | Tests can reach external services, hang, or leak state across order. R13.1–R13.3. | Yes | — |
| F-15 | Low | Testing | repo root / `apps/api` (`.coverage`, `.hypothesis/`, `iterra.db` present) | Transient test artifacts tracked/committed. | Repo noise; potential stale local DB. R13.4. | Yes | — |
| F-16 | Low | Migrations | `apps/api/app/db/migrations/versions/009_encrypt_social_tokens.py` | `downgrade()` is an intentional **no-op** (documented irreversible). | Cannot roll back past 009 without manual data handling; must be recorded. R10.1/R10.2. | Yes | `x-integration-hardening` |
| F-17 | Low | CORS | `apps/api/main.py` / `config.py` | Origins are a non-wildcard allowlist (good) and methods/headers are explicit in production (good), but there is **no startup guard** failing on an empty allowlist in production. | Silent misconfiguration could serve with no usable origins. R6.3. | Yes | — |
| F-18 | Medium | Authorization | `apps/api/app/routers/*` (28 routers in `main.py`) | No single source of truth documenting each route's scope (public/user/admin); ownership relies on per-service `filter(... user_id ...)` (present in `content_service.py`, `social_service.py`, etc.). | Coverage gaps are hard to detect; needs the route-scope table + Property 3 test. R2.4. | Yes | — |
| F-19 | Low | Observability | `packages/ai-engine/iterra_ai/core/cost_tracker.py` (`CostTracker`) *Unverified at call sites* | Cost tracking exists but per-call attribution to a request/correlation id was not confirmed across all engine call sites. | Cost may not be attributable per request. R11.5. | **Unverified** | `self-learning-content-loop` |

## Findings summary by severity

| Severity | Count | Finding IDs |
|----------|-------|-------------|
| Critical | 1 | F-01 |
| High | 6 | F-02, F-03, F-04, F-05, F-06, F-07, F-09 |
| Medium | 7 | F-08, F-10, F-11, F-12, F-13, F-14, F-18 |
| Low | 5 | F-15, F-16, F-17, F-19 *(unverified)* |

> One finding (**F-19**) is *Unverified*; all others are verified in code (Requirement 14.3).

## Positive findings (already hardened — do not re-do)

These concerns were checked and found already satisfied in the codebase. They are recorded so remediation effort is not wasted re-doing them.

- **Non-root containers** — `infra/docker/Dockerfile.api` and `Dockerfile.worker` both create and switch to `appuser` (R12.5 satisfied).
- **Production `SECRET_KEY` guard** — `config.py` `secret_key_must_be_changed` validator raises in production for the insecure default (R3.1 satisfied).
- **Token encryption-at-rest with rotation** — `core/security.py` `MultiFernet` decrypts legacy `SECRET_KEY`-derived ciphertext after rotating to `TOKEN_ENCRYPTION_KEY`; OAuth upsert encrypts tokens before persisting (R3.3 satisfied; key separation pending — see F-10).
- **Beat task registration** — `workers/celery/app.py` `include=[...]` registers all beat-referenced tasks, including previously-unregistered `compute_analytics`/`smart_scheduler` (R8.4 satisfied).
- **Draft immutability + bounded retries** — publishing-state transitions and the bounded HTTP retry/`failed` terminal state originate in `iterra-platform-stabilization-and-twitter` (R8.2/R8.3 largely satisfied; lock/dedup pending — see F-09).
- **Datetime helpers** — `db/datetime_helpers.py` provides `utc_now()`/`ensure_aware()` and most analytics services use duration arithmetic with aware UTC (R9.1 largely satisfied; stragglers in F-11).

## Route-Scope Mapping (Requirement 2.4)

The API enforces authentication per-route (via the `get_current_user` dependency) rather than through a global gate, so a newly added router that forgets the dependency would be silently public (finding **F-04**/**F-18**). The authoritative, code-backed source of truth is `apps/api/app/core/public_routes.py`. The table below documents, for each mounted router, the authorization scope that applies and any route that is public or admin-gated.

Scopes: **public** (reachable without an authenticated identity), **user-scoped** (requires an authenticated identity; data scoped to that user), **admin-scoped** (requires an authenticated identity whose email is in `ADMIN_EMAILS`).

### Documented public surface (Requirement 2.1)

| Method | Path | Why public |
|--------|------|-----------|
| GET | `/health` | Liveness alias. |
| GET | `/health/live` | Process liveness probe. |
| GET | `/health/ready` | Dependency-aware readiness probe. |
| GET | `/api/v1/waitlist` | Waitlist stats (anonymous). |
| POST | `/api/v1/waitlist` | Waitlist join (anonymous). |
| POST | `/api/v1/auth/register` | Credential-establishing. |
| POST | `/api/v1/auth/login` | Credential-establishing. |
| POST | `/api/v1/auth/logout` | Credential-establishing. |
| GET | `/api/v1/auth/google/start` · `/callback` | OAuth login flow (state-bound). |
| GET | `/api/v1/auth/linkedin/start` · `/callback` | OAuth login flow (state-bound). |
| GET | `/api/v1/connect/twitter/start` · `/callback` | Social connect (state/connect-token bound). |
| GET | `/api/v1/connect/linkedin/start` · `/callback` | Social connect (state/connect-token bound). |
| GET | `/api/v1/connect/instagram/start` · `/callback` | Social connect (state/connect-token bound). |

Framework routes (`/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc`) are public by design and treated as allowlisted.

### Per-router scope

| Router | Prefix | Default scope | Public routes | Admin routes | Notes |
|--------|--------|---------------|---------------|--------------|-------|
| `auth` | `/api/v1/auth` | user-scoped | register/login/logout + Google/LinkedIn OAuth start+callback | — | `/me`, `/onboarding` require `get_current_user`. |
| `waitlist` | `/api/v1/waitlist` | user-scoped | join, stats | `/admin/entries`, `/admin/approve`, `/admin/revoke` | `/admin/*` gated by `require_admin` against `ADMIN_EMAILS`. |
| `social_oauth` | `/api/v1/connect` | user-scoped | twitter/linkedin/instagram start+callback | — | `/status`, `/session`, `DELETE /{platform}` require `get_current_user`. |
| `onboarding` | `/api/v1/onboarding` | user-scoped | — | — | — |
| `context` | `/api/v1/context` | user-scoped | — | — | — |
| `linkedin` | `/api/v1/linkedin` | user-scoped | — | — | — |
| `brand_profile` | `/api/v1/brand-profile` | user-scoped | — | — | — |
| `trends` | `/api/v1/trends` | user-scoped | — | — | — |
| `content` | `/api/v1/content` | user-scoped | — | — | Ownership via `content_service` `user_id` filters. |
| `analytics` | `/api/v1/analytics` | user-scoped | — | — | — |
| `users` | `/api/v1/users` | user-scoped | — | — | — |
| `calendar` | `/api/v1/calendar` | user-scoped | — | — | — |
| `repurpose` | `/api/v1/repurpose` | user-scoped | — | — | — |
| `coach` | `/api/v1/coach` | user-scoped | — | — | — |
| `radar` | `/api/v1/radar` | user-scoped | — | — | — |
| `social` | `/api/v1/social` | user-scoped | — | — | Ownership via `social_service` `user_id` filters. |
| `sync` | `/api/v1/sync` | user-scoped | — | — | — |
| `persona` | `/api/v1/persona` | user-scoped | — | — | — |
| `storage` | `/api/v1/storage` | user-scoped | — | — | Exposes its own `/health` and `/status`, both user-scoped — not the public `/health`. |
| `organizations` | `/api/v1/organizations` | user-scoped | — | — | Membership/role checks via `permissions.py` enforce per-resource authorization. |
| `workspaces` | `/api/v1/workspaces` | user-scoped | — | — | Resource access mediated by `get_current_workspace` + `permissions.py`. |
| `predictions` | `/api/v1/predictions` | user-scoped | — | — | — |
| `competitors` | `/api/v1/competitors` | user-scoped | — | — | — |
| `reports` | `/api/v1/reports` | user-scoped | — | — | — |
| `approvals` | `/api/v1/approvals` | user-scoped | — | — | — |

**Routes lacking an ownership or authorization control (Requirement 2.4):** none identified beyond the documented public surface above. Every user-scoped router resolves identity through `get_current_user`; per-resource ownership is enforced by service-layer `user_id` filters and, for organizations/workspaces, by `permissions.py`. The structural gap is the *absence of an enforcing global gate* (F-04/F-18), which the route-scope source of truth plus the Property 3 enumeration test are designed to close.

## Migration reversibility record (Requirement 10.2)

| Revision | Reversible? | Operational consequence of rolling back past it |
|----------|-------------|--------------------------------------------------|
| `009_encrypt_social_tokens` | **No** (intentional no-op `downgrade()`) | Social-connection tokens were encrypted in place during upgrade. Rolling back past 009 does not restore plaintext columns; tokens would need manual decryption/migration. Roll back past 009 only with an explicit data-handling plan. (F-16) |
| Revisions `004`–`008`, `010`, and the additive idempotency/reconnect revision | Yes | `upgrade`/`downgrade` both implemented; safe one-step rollback. |

## Example user flows that expose the failure modes

These flows were used to derive and stress the findings above.

**Flow A — Email collision (exposes F-01).** A legitimate user signed up long ago via the legacy `/auth/register` flow with `dana@acme.com`. An attacker creates a Supabase account using `dana@acme.com` but never clicks the verification email. The attacker's Supabase JWT decodes locally (signature valid, `aud=authenticated`), and `_get_or_create_user_from_supabase` looks up by email, finds Dana's row, and returns it. The attacker is now authenticated as Dana. **Expected after remediation:** because `email_verified` is false and the email collides with an existing account, the resolver returns `401` and links nothing (Property 1).

**Flow B — OAuth connect round-trip (exposes F-07, F-08).** A user clicks "Connect LinkedIn." The frontend should call `POST /connect/session` to mint a single-use `ct`, then open `/connect/linkedin/start?ct=...`. Today a client can instead pass `?token=<raw JWT>` (F-08), and the returned `state` (a 10-min JWT) is not bound to the browser session — a captured authorization URL can be replayed within the window (F-07). **Expected after remediation:** start accepts only a single-use `ct`; the callback accepts state only when it is fresh, bound, and unused; replay is rejected (Property 7).

**Flow C — Scheduled publish retried after partial success (exposes F-09).** A draft is due at 12:00. The beat fires `process_publishing_queue`; `publish_draft` posts to X successfully, but the worker crashes before `db.commit()` sets `published`. Five minutes later the next beat run selects the same still-`scheduled` draft and publishes again — a duplicate tweet. Separately, two overlapping beat runs can both pass the `db.refresh` status re-check. **Expected after remediation:** the draft is selected under a row-level lock so only one run transitions it (Property 13), and a natural-key/`platform_post_id` guard detects the prior success and skips re-posting (Property 16).

**Flow D — Unhandled error in production (exposes F-05, F-06).** A service raises an unexpected `KeyError` while building an analytics summary. Today the client receives Starlette's default `500` with no correlation id, and the server log line cannot be tied to the client's report. **Expected after remediation:** the client gets the `Error_Envelope` (HTTP 500, category message, `correlation_id`) and the server log carries the same id, exception class, and stack trace — with no secrets (Properties 11, 19, 9).

**Flow E — First-of-month analytics window (exposes F-11).** On the 3rd of the month a user opens analytics. Any code that computed a window by replacing the day or month component (rather than subtracting a `timedelta`) would raise on invalid day-of-month; naive `datetime.utcnow()` in `predictions.py` compared to aware stored values raises offset-naive/aware errors. **Expected after remediation:** windows use duration arithmetic and all comparisons normalize via `ensure_aware` (Properties 17, 18).

---

*Each finding above is mapped to a remediation in the [Fix Plan](./fix-plan.md), and each remediation is verified by a step in the [Go-Live Checklist](./go-live-checklist.md).*
