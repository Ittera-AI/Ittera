# Implementation Plan: Production-Readiness & Security Hardening

## Overview

This plan turns the design's Fix Plan (FX-1 … FX-21) and the 19 correctness properties into ordered, incremental coding steps for the Iterra platform. The implementation language is **Python** (FastAPI backend in `apps/api`, Celery workers in `workers/celery`, AI package in `packages/ai-engine`), with infrastructure changes to `infra/` and `docker-compose.yml`. Property-based tests use **Hypothesis** (already present in `apps/api/.hypothesis/`) and run at a minimum of 100 iterations each.

Each task builds on the previous ones and ends by wiring new components into the running app. Test sub-tasks are marked optional with `*`. Each property test references its design property number and the requirement clause it validates.

## Tasks

- [x] 1. Fail-closed configuration foundation (FX-1)
  - [x] 1.1 Extend `apps/api/config.py` startup validators
    - Add validators that, in staging/production (`ENVIRONMENT` in {staging, production}), fail startup with a descriptive error when `SECRET_KEY` is the insecure default, when `TOKEN_ENCRYPTION_KEY` is empty/unset, or when the `ALLOWED_ORIGINS` allowlist is empty
    - Keep the existing `secret_key_must_be_changed` behavior; do not weaken it
    - _Requirements: 3.1, 3.5, 6.1, 6.2, 6.3_
  - [ ]* 1.2 Write example tests for the startup validators
    - Assert startup raises on default `SECRET_KEY`, empty `TOKEN_ENCRYPTION_KEY`, and empty `ALLOWED_ORIGINS` in production; assert startup succeeds when all are set
    - _Requirements: 3.1, 3.5, 6.1, 6.2, 6.3_

- [x] 2. Authentication identity integrity (FX-2, FX-3)
  - [x] 2.1 Add the `email_verified` account-linking gate in `apps/api/app/dependencies/auth.py`
    - In `_get_or_create_user_from_supabase`, verify the local Supabase JWT decode requires `aud == "authenticated"`; link to an existing local account by email only when the token's `email_verified` claim is true
    - When an unverified Supabase email collides with an existing account, raise HTTP 401 and create no user record
    - _Requirements: 1.1, 1.3, 1.4_
  - [x] 2.2 Harden the Supabase REST fallback `_fetch_supabase_user`
    - Apply a bounded request timeout to the fallback call; re-check audience/verified status on the returned identity; return `None` (→ 401) on any non-verified or non-2xx result instead of swallowing errors silently
    - _Requirements: 1.2, 1.5_
  - [ ]* 2.3 Write property test for verified-email account linking
    - **Property 1: Verified-email account linking**
    - **Validates: Requirements 1.1**
    - Place in `apps/api/tests/test_auth_identity_properties.py`
  - [ ]* 2.4 Write property test for invalid-identity rejection
    - **Property 2: Invalid identity is always rejected without account creation**
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
    - Place in `apps/api/tests/test_auth_identity_properties.py`

- [x] 3. Authorization and route-scope coverage (FX-4)
  - [x] 3.1 Define the explicit public-route allowlist and route-scope source of truth
    - Create `apps/api/app/core/public_routes.py` enumerating documented public routes (`/health`, liveness, readiness, waitlist join/stats, auth register/login/logout, OAuth callbacks)
    - Produce the per-router scope mapping (public/user-scoped/admin-scoped) consumed by the Property 3 test and the audit deliverable
    - _Requirements: 2.1, 2.4_
  - [x] 3.2 Enforce owner-scoped resource access and admin gating
    - Ensure user-owned resource lookups filter by the authenticated user's id and return HTTP 404 when a resource does not belong to the user; confirm `require_admin` returns HTTP 403 when the email is not in `ADMIN_EMAILS`
    - Add/repair the per-service ownership filters where missing
    - _Requirements: 2.2, 2.3_
  - [ ]* 3.3 Write property test for non-public route authentication
    - **Property 3: Every non-public route requires authentication**
    - **Validates: Requirements 2.1**
    - Place in `apps/api/tests/test_authorization_properties.py`; enumerate `app.routes` against the allowlist
  - [ ]* 3.4 Write property test for owner-scoped resources
    - **Property 4: User-owned resources are owner-scoped**
    - **Validates: Requirements 2.2**
    - Place in `apps/api/tests/test_authorization_properties.py`
  - [ ]* 3.5 Write property test for admin authorization
    - **Property 5: Admin authorization matches the admin allowlist**
    - **Validates: Requirements 2.3**
    - Place in `apps/api/tests/test_authorization_properties.py`

- [ ] 4. Correlation ID and structured logging (FX-5)
  - [x] 4.1 Create `CorrelationIdMiddleware`
    - Add `apps/api/app/middleware/correlation.py` that assigns/propagates `X-Correlation-ID`, binds it to a `contextvar`, and echoes it on every response
    - _Requirements: 11.1, 11.4, 7.4_
  - [x] 4.2 Create structured logging config with secret redaction
    - Add `apps/api/app/core/logging.py` with a JSON formatter (correlation id, severity, timestamp) and a `SecretRedactingFormatter` reusing the existing `AuditLogger._sanitize_details` redaction key set
    - _Requirements: 11.1, 4.4, 7.2_
  - [ ]* 4.3 Write property test for correlation-id propagation
    - **Property 19: Every request carries a propagated correlation id**
    - **Validates: Requirements 11.1, 11.4**
    - Place in `apps/api/tests/test_error_envelope_properties.py`

- [x] 5. Global error handling and Error_Envelope (FX-6)
  - [x] 5.1 Implement the Error_Envelope and exception handlers
    - Add `apps/api/app/core/errors.py` with handlers for unhandled `Exception` (HTTP 500, `code="internal_error"`, no stack trace/internal ids in body), `RequestValidationError` (HTTP 422, field-level `details` with no secret values), and `HTTPException` (wrap 401/403/404/429 in the same envelope, preserving status); include the correlation id matching the response header
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [ ]* 5.2 Write property test for unhandled-exception envelope
    - **Property 11: Unhandled exceptions yield a sanitized, correlated envelope**
    - **Validates: Requirements 7.1, 7.4**
    - Place in `apps/api/tests/test_error_envelope_properties.py`
  - [ ]* 5.3 Write property test for invalid input
    - **Property 12: Invalid input yields HTTP 422**
    - **Validates: Requirements 7.3**
    - Place in `apps/api/tests/test_error_envelope_properties.py`

- [x] 6. Rate limiting (FX-7)
  - [x] 6.1 Rework `RateLimitMiddleware` to a shared-store sliding window
    - In `apps/api/app/middleware/rate_limit.py`, implement a Redis-backed sliding-window limiter with per-tier limits (stricter limit for `/api/v1/auth/*` than general routes), returning HTTP 429 with a positive `Retry-After` header; make limits configurable
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - [ ]* 6.2 Write property test for rate-limit thresholds
    - **Property 10: Rate limiting enforces per-tier thresholds with Retry-After**
    - **Validates: Requirements 5.1, 5.2, 5.4, 5.5**
    - Place in `apps/api/tests/test_rate_limit_properties.py`
  - [ ]* 6.3 Write integration test for shared-store enforcement
    - Two limiter instances backed by one fake Redis enforce a single shared limit
    - _Requirements: 5.3_
    - Place in `apps/api/tests/test_rate_limit_integration.py`

- [x] 7. Wire middleware stack and health probes into the app (FX-8)
  - [x] 7.1 Register middleware and add readiness/liveness probes in `apps/api/main.py`
    - Register the ordered stack (CorrelationId → CORS → RateLimit) and the global exception/validation/HTTPException handlers; add `GET /health/live` (process only) and `GET /health/ready` (DB `SELECT 1` + broker ping, 503 with category-only failure detail); keep `GET /health` as a liveness alias
    - _Requirements: 11.2, 11.3, 7.1, 5.1, 6.2, 11.4_
  - [ ]* 7.2 Write example tests for the probes
    - Liveness returns 200 with DB down; readiness returns 200 when deps up and 503 when DB or broker is down
    - _Requirements: 11.2, 11.3_
    - Place in `apps/api/tests/test_health_probes.py`

- [x] 8. Checkpoint - middleware, auth, and error handling wired
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. OAuth and social-integration hardening (FX-9, FX-10, FX-12)
  - [x] 9.1 Bind connect-state to the session and make it single-use for all platforms
    - In `apps/api/app/routers/social_oauth.py`, extend the X PKCE single-use/binding pattern to LinkedIn and Instagram: bind `Connect_State` to the initiating session and reject callbacks whose state is missing, expired, reused, unbound, or for the wrong platform
    - _Requirements: 4.1_
  - [x] 9.2 Remove the URL-token fallback and sanitize OAuth error output
    - Remove the `?token=` raw-JWT acceptance in `_resolve_start_user` (require single-use `ct` server-side exchange); replace error strings that embed upstream payloads (e.g. `_get_user_id_from_token`, popup reasons) with category-level messages, and apply secret redaction to OAuth/external-platform error logs
    - _Requirements: 4.2, 4.4, 4.5, 7.2_
  - [x] 9.3 Implement refresh-or-reconnect for stored credentials
    - When a stored OAuth credential is expired, refresh it if a refresh token is available; otherwise set `SocialConnection.requires_reconnect` and surface a category error without crashing callers
    - _Requirements: 4.3_
  - [ ]* 9.4 Write property test for connect-state single-use binding
    - **Property 7: OAuth connect-state is single-use and bound**
    - **Validates: Requirements 4.1, 4.2**
    - Place in `apps/api/tests/test_oauth_hardening_properties.py`
  - [ ]* 9.5 Write property test for refresh-or-reconnect decision
    - **Property 8: Credential refresh-or-reconnect decision**
    - **Validates: Requirements 4.3**
    - Place in `apps/api/tests/test_oauth_hardening_properties.py`
  - [ ]* 9.6 Write property test for secret-safe logs and responses
    - **Property 9: No secret or raw upstream payload escapes to logs or responses**
    - **Validates: Requirements 4.4, 4.5, 7.2**
    - Place in `apps/api/tests/test_oauth_hardening_properties.py`

- [ ] 10. Token encryption verification (FX-11)
  - [ ]* 10.1 Write property test for token encryption round-trip and key rotation
    - **Property 6: Token encryption round-trips and never stores plaintext**
    - **Validates: Requirements 3.2, 3.3**
    - Place in `apps/api/tests/test_token_encryption_properties.py`; cover legacy `SECRET_KEY`-derived ciphertext still decrypting after `TOKEN_ENCRYPTION_KEY` is configured (MultiFernet)

- [x] 11. Additive schema for idempotency and reconnect (FX-14, FX-9)
  - [x] 11.1 Add reversible Alembic revision and model fields
    - Add `ContentDraft.publish_idempotency_key` (nullable, unique per draft) and `SocialConnection.requires_reconnect` (boolean, default false) to the models, plus a new Alembic revision with both `upgrade` and `downgrade`
    - _Requirements: 8.5, 4.3, 10.1_

- [ ] 12. Background-job exactly-once publishing (FX-13, FX-14)
  - [x] 12.1 Select due drafts under a row-level lock
    - In `workers/celery/tasks/publisher.py` `process_publishing_queue`, replace the `db.refresh` re-read with a row-level lock (`SELECT ... FOR UPDATE SKIP LOCKED` on Postgres, reusing the `_lock_draft` pattern) before transitioning a draft to `publishing`
    - _Requirements: 8.1_
  - [x] 12.2 Add natural-key idempotency guard before the platform call
    - Before posting, set/check `publish_idempotency_key` and check for an existing `published` post by `(user_id, platform, platform_post_id)` (or an existing `platform_post_id` on the draft) so a retry after partial success does not republish
    - _Requirements: 8.5_
  - [x] 12.3 Enforce draft immutability and bounded failure
    - Reject content/media/schedule changes while a draft is in `publishing`/`published`; ensure a failed publish transitions to `failed` with a category-level error and does not retry indefinitely
    - _Requirements: 8.2, 8.3_
  - [ ]* 12.4 Write property test for exactly-once publishing under concurrency
    - **Property 13: Exactly-once publishing under concurrency**
    - **Validates: Requirements 8.1**
    - Place in `apps/api/tests/test_publishing_idempotency_properties.py`
  - [ ]* 12.5 Write property test for draft immutability
    - **Property 14: Published/publishing drafts are immutable**
    - **Validates: Requirements 8.2**
    - Place in `apps/api/tests/test_publishing_idempotency_properties.py`
  - [ ]* 12.6 Write property test for failed-state termination
    - **Property 15: Failed publish terminates in a failed state with a category error**
    - **Validates: Requirements 8.3**
    - Place in `apps/api/tests/test_publishing_idempotency_properties.py`
  - [ ]* 12.7 Write property test for natural-key idempotency
    - **Property 16: Publish is idempotent by natural key**
    - **Validates: Requirements 8.5**
    - Place in `apps/api/tests/test_publishing_idempotency_properties.py`
  - [ ]* 12.8 Write smoke test for beat-task registration
    - Assert every `BEAT_SCHEDULE` task is present in `celery_app.tasks`
    - _Requirements: 8.4_
    - Place in `apps/api/tests/test_beat_registration.py`

- [x] 13. Datetime and data-integrity consistency (FX-15)
  - [x] 13.1 Replace naive/machine-local datetimes with aware UTC handling
    - Update `apps/api/app/routers/predictions.py`, `app/services/storage_service.py`, and `app/services/reporting_service.py` to use `utc_now()`/`ensure_aware()`; ensure relative windows use `timedelta` arithmetic and all comparisons normalize to UTC
    - _Requirements: 9.1, 9.2, 9.3_
  - [ ]* 13.2 Write property test for relative date windows
    - **Property 17: Relative date windows succeed for every calendar date**
    - **Validates: Requirements 9.1**
    - Place in `apps/api/tests/test_datetime_properties.py`
  - [ ]* 13.3 Write property test for datetime normalization
    - **Property 18: Datetime normalization yields comparable aware UTC values**
    - **Validates: Requirements 9.2, 9.3**
    - Place in `apps/api/tests/test_datetime_properties.py`

- [ ] 14. Infrastructure and deployment hardening (FX-16, FX-17, FX-18)
  - [x] 14.1 Harden nginx for TLS and security headers
    - Add a 443 server with HTTP→HTTPS redirect and HSTS plus the standard security headers to `infra/nginx/nginx.conf`
    - _Requirements: 12.1, 12.2_
  - [x] 14.2 Add resource limits and healthchecks to orchestration
    - Define CPU/memory limits and healthchecks for the api, worker, and web services in `docker-compose.yml` (and k8s manifests); source secrets from environment-specific stores with no hardcoded production credentials
    - _Requirements: 12.3, 12.4, 12.6_
  - [ ]* 14.3 Write config/snapshot tests for infrastructure
    - Assert nginx has a 443 server, HTTP→HTTPS redirect, and HSTS/security headers; assert compose/k8s define CPU/memory limits and healthchecks for api/worker/web; assert recent additive migrations expose a non-trivial downgrade and revision 009 is recorded irreversible
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 10.1, 10.2_
    - Place in `apps/api/tests/test_infra_config.py`
  - [ ]* 14.4 Write static credential-scan test
    - Scan tracked files and `docker-compose.yml` for committed production credentials; assert none are present
    - _Requirements: 3.4, 12.6_
    - Place in `apps/api/tests/test_credential_scan.py`

- [ ] 15. Test-suite reliability and hygiene (FX-19, FX-20)
  - [x] 15.1 Harden the test harness in `apps/api/tests/conftest.py`
    - Add an autouse `block_network` fixture that patches socket/httpx transport to raise on real connections; configure `pytest-timeout` with a conservative per-test default; add a per-test transaction/savepoint that rolls back after each test for state isolation
    - _Requirements: 13.1, 13.2, 13.3_
  - [x] 15.2 Exclude and untrack transient test artifacts
    - Gitignore and untrack `.coverage`, `.hypothesis/`, and `iterra.db`
    - _Requirements: 13.4_

- [x] 16. LLM cost attribution (FX-21)
  - [x] 16.1 Instrument per-call cost attribution
    - Ensure `packages/ai-engine/iterra_ai/core/cost_tracker.py` records outbound LLM token usage for every engine call site, attributed to the request/correlation id
    - _Requirements: 11.5_
  - [ ]* 16.2 Write integration test for cost tracking
    - Assert `CostTracker` records token usage per engine call
    - _Requirements: 11.5_
    - Place in `apps/api/tests/test_cost_tracking.py`

- [x] 17. Produce the spec deliverable documents
  - [x] 17.1 Write the Audit Report, Fix Plan, and Go-Live Checklist documents
    - Materialize the three deliverables as repository documents under `docs/`: the Audit Report (findings with severity, file/location, description, impact, area classification, verified/unverified, existing-spec references), the Fix Plan (each finding mapped to remediation with priority and dependencies), and the ordered Go-Live Checklist (execution order, a verification step per hardening requirement, required/optional markers)
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 15.1, 15.2, 15.3, 15.4, 16.1, 16.2, 16.3, 16.4, 2.4, 10.2_

- [x] 18. Final checkpoint - full suite green
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core implementation tasks are never optional.
- Property tests (Properties 1–19) each run at a minimum of 100 Hypothesis iterations and are tagged with a comment referencing the design property, e.g. `# Feature: production-readiness-security-hardening, Property 13: ...`.
- Each task references specific requirement clauses for traceability; checkpoints provide incremental validation points.
- Positive findings already satisfied in code (non-root containers R12.5, production `SECRET_KEY` guard R3.1, MultiFernet rotation R3.3, beat-task registration R8.4) are verified rather than rebuilt.
- Where work overlaps the `iterra-platform-stabilization-and-twitter`, `x-integration-hardening`, and `self-learning-content-loop` specs, this plan extends those guarantees platform-wide rather than duplicating them.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1", "4.1", "4.2", "5.1", "6.1", "9.1", "11.1", "13.1", "14.1", "14.2", "15.1", "15.2", "16.1"] },
    { "id": 1, "tasks": ["1.2", "2.2", "3.2", "7.1", "9.2", "9.3", "12.1", "12.3", "13.2", "14.3", "14.4", "16.2", "17.1"] },
    { "id": 2, "tasks": ["2.3", "3.3", "4.3", "6.2", "6.3", "7.2", "9.4", "10.1", "12.2", "12.8", "13.3"] },
    { "id": 3, "tasks": ["2.4", "3.4", "5.2", "9.5", "12.4"] },
    { "id": 4, "tasks": ["3.5", "5.3", "9.6", "12.5"] },
    { "id": 5, "tasks": ["12.6"] },
    { "id": 6, "tasks": ["12.7"] }
  ]
}
```
