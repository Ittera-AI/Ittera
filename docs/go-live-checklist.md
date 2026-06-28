# Go-Live Checklist — Production-Readiness & Security Hardening

> **Spec:** `production-readiness-security-hardening`
> **Deliverable:** 3 of 3 (Audit Report · Fix Plan · Go-Live Checklist)
> **Companion documents:** [`audit-report.md`](./audit-report.md), [`fix-plan.md`](./fix-plan.md)

## Purpose

This is the ordered checklist of everything required to deploy the Iterra platform safely. Items are presented **in execution order** (Stage 1 first). Each item is marked **[Required]** or **[Optional]** for the initial production release, names the concrete check, and cites the requirement(s) it verifies. Together the stages include a verification step for every hardening requirement defined in the spec.

This document satisfies Requirement 16 (Go-Live readiness checklist deliverable):

- **16.1** — prerequisites are presented in execution order.
- **16.2** — there is a verification step for each hardening requirement.
- **16.3** — environment-configuration, secrets, migration, TLS, observability, and rollback verification steps are included.
- **16.4** — each item is marked required or optional for the initial production release.

## Requirement coverage map (Requirement 16.2)

| Requirement area | Verified by checklist item(s) |
|------------------|-------------------------------|
| R1 Authentication identity | 6 |
| R2 Authorization & ownership | 9, 10, 11 |
| R3 Secrets & encryption | 2, 3, 5 |
| R4 OAuth hardening | 14, 15 |
| R5 Rate limiting | 12 |
| R6 CORS safety | 1, 4 |
| R7 Error handling & validation | 13 |
| R8 Background-job safety | 16, 17, 18 |
| R9 Datetime / data integrity | (covered by Property 17/18 in item 27) |
| R10 Migration reversibility | 8 |
| R11 Observability | 19, 20, 21 |
| R12 Infrastructure & TLS | 22, 23, 24, 25 |
| R13 Test-suite reliability | 26, 28 |
| Property suite (1–19) | 27 |

## Stage 1 — Environment configuration & secrets (do first)

1. **[Required]** Set `ENVIRONMENT=production`. *Verify:* app reads production branches (CORS methods/headers explicit). (R6.2)
2. **[Required]** Set a strong `SECRET_KEY` (32-byte hex). *Verify:* startup does not raise the default-secret error; rotating it does not invalidate stored tokens (MultiFernet). (R3.1)
3. **[Required]** Set a dedicated `TOKEN_ENCRYPTION_KEY`. *Verify:* startup fails if unset in production (FX-1); a sample token round-trips. (R3.2, R3.5)
4. **[Required]** Set `ALLOWED_ORIGINS` to the real frontend origin(s), never `*`. *Verify:* startup fails on empty allowlist; credentialed cross-origin works only from listed origins. (R6.1, R6.3)
5. **[Required]** Provide DB URL, broker URL, and all API keys via the environment's secret store; confirm none are committed. *Verify:* static credential scan of tracked files and `docker-compose.yml` is clean; the local `iterra/iterra` Postgres creds are not used in prod. (R3.4, R12.6)
6. **[Required]** Configure Supabase (`SUPABASE_JWT_SECRET`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`). *Verify:* a verified Supabase login resolves; an unverified-email collision is rejected with 401. (R1.1, R1.3)

## Stage 2 — Database & migrations

7. **[Required]** Run `alembic upgrade head` against the production DB. *Verify:* schema current; app boots.
8. **[Required]** Test the downgrade path of recent migrations on a disposable copy. *Verify:* `upgrade head` then `downgrade -1` succeeds for reversible revisions; revision **009** is acknowledged as irreversible (no-op downgrade) and its rollback consequence accepted. (R10.1, R10.2, R10.4)

## Stage 3 — Application hardening verification

9. **[Required]** Confirm every non-public route requires auth. *Verify:* Property 3 test (route enumeration) passes; the route-scope table is published. (R2.1, R2.4)
10. **[Required]** Confirm ownership scoping. *Verify:* Property 4 test passes; cross-user access returns 404. (R2.2)
11. **[Required]** Confirm admin gating. *Verify:* `ADMIN_EMAILS` set; non-admin gets 403. (R2.3)
12. **[Required]** Confirm rate limiting is active and shared-store. *Verify:* exceeding the general/auth tiers returns 429 + `Retry-After`; limits hold across two API replicas. (R5.1–R5.5)
13. **[Required]** Confirm the global error envelope. *Verify:* a forced error returns the sanitized envelope with a correlation id and no stack trace; 422 on bad input. (R7.1–R7.4)
14. **[Required]** Confirm OAuth hardening. *Verify:* connect uses single-use `ct`; replayed/expired/unbound state rejected; no token appears in any URL or log; browser errors are category-level. (R4.1, R4.2, R4.4, R4.5)
15. **[Required]** Confirm token refresh/reconnect. *Verify:* an expired credential with a refresh token refreshes; without one, the connection is marked reconnect-required (see [`live_readiness_checklist.md`](./live_readiness_checklist.md) reconnect flow). (R4.3)

## Stage 4 — Background jobs

16. **[Required]** Confirm `process_publishing_queue` and all beat tasks are registered. *Verify:* `celery -A workers.celery.app inspect registered` lists every `BEAT_SCHEDULE` task. (R8.4)
17. **[Required]** Confirm exactly-once publishing. *Verify:* two identical due drafts publish at most once each under concurrent runs; a retry after partial success creates no duplicate. (R8.1, R8.5)
18. **[Required]** Confirm draft immutability and bounded failure. *Verify:* edits to publishing/published drafts are blocked; a forced failure ends in `failed` with a category error and no infinite retry. (R8.2, R8.3)

## Stage 5 — Observability

19. **[Required]** Confirm structured logging with correlation ids. *Verify:* request logs are JSON with `correlation_id`, severity, timestamp; secrets redacted. (R11.1, R11.4)
20. **[Required]** Wire orchestration probes. *Verify:* `/health/live` is 200 while up; `/health/ready` is 503 when DB or broker is down. (R11.2, R11.3)
21. **[Optional]** Confirm LLM cost attribution. *Verify:* `CostTracker` records token usage per engine call. (R11.5)

## Stage 6 — Infrastructure & TLS

22. **[Required]** Terminate TLS at nginx and redirect HTTP→HTTPS. *Verify:* `http://` redirects to `https://`; valid certificate served. (R12.1)
23. **[Required]** Emit security headers incl. HSTS. *Verify:* response headers include `Strict-Transport-Security` and the standard security set. (R12.2)
24. **[Required]** Define CPU/memory limits and healthchecks for api/worker/web. *Verify:* compose/k8s manifests show limits and healthchecks; orchestrator gates readiness on them. (R12.3, R12.4)
25. **[Required]** Confirm containers run as non-root. *Verify:* api/worker images run as `appuser` (already configured). (R12.5)

## Stage 7 — Test-suite & release gating

26. **[Required]** CI runs the full backend suite offline and deterministically. *Verify:* outbound network blocked; per-test timeout enforced; suite passes regardless of order. (R13.1–R13.3)
27. **[Required]** All Property 1–19 tests pass at ≥100 iterations each. *Verify:* property suite green. (covers R9 datetime properties 17/18 and the full correctness-property set)
28. **[Optional]** Transient artifacts excluded from VCS. *Verify:* `.coverage`, `.hypothesis/`, `iterra.db` gitignored and untracked. (R13.4)
29. **[Required]** Rollback plan rehearsed. *Verify:* a previous image can be redeployed and migrations downgraded one step (excluding 009) without data loss. (R10.4)

## Required vs optional summary (Requirement 16.4)

| Marker | Items |
|--------|-------|
| **[Required]** | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 27, 29 |
| **[Optional]** | 21 (LLM cost attribution), 28 (VCS artifact hygiene) |

---

*Each verification step above traces back to a remediation in the [Fix Plan](./fix-plan.md) and a finding in the [Audit Report](./audit-report.md).*
