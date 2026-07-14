# Requirements Document

## Introduction

This spec defines a project-wide **production-readiness and security-hardening initiative** for the Iterra (Ittera) platform — a full-stack AI content-strategy system spanning a FastAPI backend (`apps/api`), a Next.js frontend (`apps/web`), an in-process AI package (`packages/ai-engine`), Celery background workers (`workers/celery`), Supabase auth/functions (`supabase/`), and infrastructure (`infra/` docker/nginx/k8s, `docker-compose.yml`).

The initiative was scoped from a line-by-line audit of the actual codebase and the existing operational docs. It deliberately **builds on, and does not duplicate**, three existing specs:
- `iterra-platform-stabilization-and-twitter` (general stabilization + Twitter publish path)
- `x-integration-hardening` (X/Twitter publish hardening, media limits, secret-safe logs)
- `self-learning-content-loop` (publish → analyze → synthesize → inject loop)

Where those specs already harden a concern (e.g. X publish-queue secret-safe logging, X token encryption, learning-loop idempotency), this spec references that work and extends the same guarantees **platform-wide** rather than re-stating it.

The deliverables of this spec are threefold and explicit:
1. **A verified audit report** of findings across security, edge-cases, and operational readiness.
2. **A prioritized patch-up / fix plan** mapping each finding to a remediation.
3. **An ordered go-live checklist** of everything required to deploy the project safely.

The requirements below define what "hardened and production-ready" means in precise, testable terms. Each requirement targets a concrete, code-verified gap.

## Glossary

- **API**: The FastAPI backend application defined under `apps/api`, entry point `apps/api/main.py`.
- **Web_App**: The Next.js frontend application under `apps/web`.
- **AI_Engine**: The in-process `iterra_ai` package under `packages/ai-engine`.
- **Worker**: The Celery worker/beat processes defined under `workers/celery`.
- **Auth_Resolver**: The authentication dependency `get_current_user` and its helpers in `apps/api/app/dependencies/auth.py`.
- **Supabase_Token**: A JWT issued by Supabase Auth, verified with `SUPABASE_JWT_SECRET` and audience `authenticated`.
- **Legacy_Token**: A JWT issued by the API's own `/auth` endpoints, signed with `SECRET_KEY`.
- **Admin_Guard**: The `require_admin` dependency that gates admin-only routes against `ADMIN_EMAILS`.
- **Rate_Limiter**: The middleware component responsible for limiting request volume per client.
- **Token_Store**: The encryption layer in `apps/api/app/core/security.py` that encrypts/decrypts OAuth credentials at rest.
- **OAuth_Connector**: The social-connection OAuth flow in `apps/api/app/routers/social_oauth.py` (Twitter/X, LinkedIn, Instagram, Google).
- **Connect_State**: The signed, time-bounded value passed through an OAuth authorization round-trip to prevent CSRF.
- **Publishing_Queue**: The Celery task `process_publishing_queue` in `workers/celery/tasks/publisher.py`.
- **Error_Envelope**: The standardized JSON error response returned by the API for handled and unhandled errors.
- **Correlation_Id**: A unique identifier attached to each request and propagated through logs.
- **Readiness_Probe**: An endpoint that reports whether the API can serve traffic (dependencies reachable).
- **Liveness_Probe**: An endpoint that reports whether the API process is running.
- **Reverse_Proxy**: The nginx service defined in `infra/nginx/nginx.conf`.
- **Naive_Datetime**: A Python `datetime` without timezone information.
- **Aware_Datetime**: A timezone-aware Python `datetime` (UTC), as produced by `utc_now()` in `apps/api/app/db/datetime_helpers.py`.
- **Audit_Report**: The deliverable document enumerating verified findings.
- **Fix_Plan**: The deliverable document mapping findings to remediations and priorities.
- **Go_Live_Checklist**: The deliverable ordered checklist of deployment prerequisites.
- **Production_Mode**: Runtime where the environment variable `ENVIRONMENT` equals `production`.

## Requirements

### Requirement 1: Authentication identity integrity

**User Story:** As a security owner, I want authentication to resolve a verified identity, so that one user cannot inherit another user's account through token or email collisions.

#### Acceptance Criteria

1. WHEN the Auth_Resolver receives a Supabase_Token whose email matches an existing Legacy_Token account, THE API SHALL link the accounts only IF the Supabase_Token email claim is marked verified, and otherwise SHALL reject the request with HTTP 401.
2. WHEN the Auth_Resolver decodes any token, THE API SHALL reject the request with HTTP 401 IF the token is expired, malformed, or fails signature verification.
3. WHEN the Auth_Resolver validates a Supabase_Token locally, THE API SHALL verify the audience claim equals `authenticated`.
4. IF the Auth_Resolver cannot resolve a valid identity through any configured method, THEN THE API SHALL respond with HTTP 401 and SHALL NOT create a new user record.
5. WHERE the Supabase REST fallback validation path is enabled, THE API SHALL apply a bounded request timeout to the fallback call and SHALL respond with HTTP 401 IF the fallback does not return a verified identity.

### Requirement 2: Authorization and resource ownership

**User Story:** As a platform operator, I want every protected resource access scoped to its owner, so that authenticated users cannot read or modify other users' data.

#### Acceptance Criteria

1. THE API SHALL require an authenticated identity via the Auth_Resolver for every route except the documented public routes (`/health`, readiness, liveness, waitlist join/stats, auth register/login/logout, OAuth callbacks).
2. WHEN a request targets a user-owned resource by identifier, THE API SHALL filter the resource by the authenticated user's identifier and SHALL respond with HTTP 404 IF the resource does not belong to that user.
3. WHEN a request targets an admin-only route, THE Admin_Guard SHALL authorize the request only IF the authenticated user's email is present in `ADMIN_EMAILS`, and otherwise SHALL respond with HTTP 403.
4. THE API SHALL document, for each mounted router, whether each route is public, user-scoped, or admin-scoped, and THE Audit_Report SHALL list any route lacking an ownership or authorization control.

### Requirement 3: Secret and encryption key management

**User Story:** As a security owner, I want secrets and encryption keys to be strong, separated, and environment-validated, so that a single leaked value cannot compromise multiple security domains.

#### Acceptance Criteria

1. IF the API starts in Production_Mode with `SECRET_KEY` set to the insecure default, THEN THE API SHALL fail startup with a descriptive error.
2. THE Token_Store SHALL encrypt OAuth credentials using a dedicated `TOKEN_ENCRYPTION_KEY` when configured, and SHALL record in the Audit_Report any environment where token encryption falls back to a `SECRET_KEY`-derived key.
3. WHEN OAuth credentials are persisted, THE API SHALL store the access token and refresh token as ciphertext, never as plaintext.
4. THE Go_Live_Checklist SHALL require that database credentials, broker URLs, and API keys are supplied through environment-specific secrets and SHALL require that no production credential is committed to the repository or to `docker-compose.yml`.
5. WHERE a deployment environment is staging or production, THE API SHALL validate that `SECRET_KEY` and `TOKEN_ENCRYPTION_KEY` are non-default before serving authenticated traffic.

### Requirement 4: OAuth and social-integration hardening

**User Story:** As a user connecting a social account, I want the connection flow to resist CSRF and credential leakage, so that my social accounts and tokens stay protected.

#### Acceptance Criteria

1. WHEN an OAuth authorization flow is initiated, THE OAuth_Connector SHALL bind the Connect_State to the initiating browser session and SHALL reject a callback whose state is missing, expired, reused, or unbound.
2. THE OAuth_Connector SHALL accept the initiating user identity only through a single-use server-side token exchange and SHALL NOT accept a bearer JWT supplied as a URL query parameter.
3. IF a stored OAuth credential is expired and a refresh token is available, THEN THE API SHALL refresh the credential before performing a platform action; IF no refresh is possible, THEN THE API SHALL mark the connection as requiring reconnection.
4. WHEN the API logs an OAuth or external-platform error, THE API SHALL exclude access tokens, refresh tokens, and raw external response bodies from the log output.
5. WHEN an OAuth flow returns an error to the browser, THE API SHALL return a category-level message and SHALL NOT embed raw external API payloads in the response.

### Requirement 5: Request rate limiting

**User Story:** As a platform operator, I want active rate limiting on the API, so that abusive or runaway clients cannot exhaust resources or brute-force authentication.

#### Acceptance Criteria

1. THE API SHALL enforce a configurable per-client request limit on incoming requests.
2. WHEN a client exceeds the configured request limit within the configured time window, THE API SHALL respond with HTTP 429.
3. WHERE the API runs with more than one process or replica, THE Rate_Limiter SHALL enforce limits using a shared backing store so that limits hold across all processes.
4. THE API SHALL apply a stricter request limit to authentication routes than to general routes.
5. WHEN a request is rejected for exceeding the limit, THE API SHALL include a `Retry-After` indication in the response.

### Requirement 6: CORS configuration safety

**User Story:** As a security owner, I want CORS configured per environment, so that credentialed cross-origin requests are only accepted from approved origins.

#### Acceptance Criteria

1. THE API SHALL set allowed origins from an explicit configured allowlist and SHALL NOT use a wildcard origin while credentials are allowed.
2. WHERE the API runs in Production_Mode, THE API SHALL restrict allowed methods and headers to an explicit list rather than a wildcard.
3. IF the allowed-origins allowlist is empty or unset in Production_Mode, THEN THE API SHALL fail startup with a descriptive error.

### Requirement 7: Global error handling and input validation

**User Story:** As an operator and as a user, I want consistent, sanitized error responses and validated inputs, so that internal details never leak and clients receive predictable errors.

#### Acceptance Criteria

1. WHEN an unhandled exception occurs during request processing, THE API SHALL return a standardized Error_Envelope with HTTP 500 and SHALL NOT include stack traces or internal identifiers in the response body.
2. WHEN the API handles any error, THE API SHALL log the error with its Correlation_Id and exception class while excluding secrets and raw external payloads.
3. THE API SHALL validate every request body, path parameter, and query parameter against a typed schema and SHALL respond with HTTP 422 for inputs that fail validation.
4. WHEN the API returns an Error_Envelope, THE API SHALL include the Correlation_Id so that a client report can be matched to server logs.

### Requirement 8: Background job safety and idempotency

**User Story:** As a content creator, I want scheduled posts published exactly once, so that background-job retries or overlapping runs never produce duplicate posts.

#### Acceptance Criteria

1. WHEN the Publishing_Queue selects a due draft, THE Worker SHALL acquire a row-level lock on that draft before transitioning it to a publishing state so that concurrent runs cannot select the same draft.
2. WHILE a draft is in a publishing or published state, THE API SHALL reject changes to that draft's content, media, and schedule.
3. WHEN a publish attempt fails, THE Worker SHALL transition the draft to a failed state with a category-level error and SHALL NOT retry the draft indefinitely.
4. THE Worker SHALL register every task that is referenced by the beat schedule so that scheduled tasks dispatch successfully.
5. IF a publish operation is retried after a partial success, THEN THE Worker SHALL detect the prior success by natural key and SHALL NOT create a duplicate published post.

### Requirement 9: Datetime and data-integrity consistency

**User Story:** As a developer, I want consistent timezone-aware datetime handling, so that date arithmetic never crashes and timestamps are comparable across the system.

#### Acceptance Criteria

1. WHEN the API computes a relative date window, THE API SHALL use duration-based arithmetic so that the computation succeeds for every calendar date including the first seven days of a month.
2. THE API SHALL produce Aware_Datetime values in UTC for stored timestamps and for any datetime used in comparison or subtraction.
3. IF a stored Naive_Datetime is compared against an Aware_Datetime, THEN THE API SHALL normalize both to UTC before comparison so that no offset-naive/offset-aware error occurs.
4. THE Audit_Report SHALL list every code site that uses machine-local time or naive datetime arithmetic against aware values.

### Requirement 10: Database migration reversibility

**User Story:** As an operator, I want migrations to be reversible and non-destructive, so that I can roll back a deployment safely.

#### Acceptance Criteria

1. THE API SHALL provide both an upgrade and a downgrade path for every migration revision, except revisions explicitly documented as irreversible.
2. WHERE a migration is documented as irreversible, THE Audit_Report SHALL record the revision and the operational consequence of rolling back past it.
3. WHEN a migration performs a data transformation, THE migration SHALL avoid destructive deletion of data that cannot be reconstructed, or SHALL document the data loss explicitly.
4. THE Go_Live_Checklist SHALL require that the downgrade path of every recent migration is tested before release.

### Requirement 11: Observability and operational readiness

**User Story:** As an operator, I want structured logging, correlation, and dependency-aware health checks, so that I can monitor and diagnose the system in production.

#### Acceptance Criteria

1. THE API SHALL emit logs in a structured format that includes the Correlation_Id, severity, and timestamp for each request-scoped log entry.
2. THE API SHALL expose a Liveness_Probe that reports process health without checking external dependencies.
3. THE API SHALL expose a Readiness_Probe that reports not-ready IF the database or the broker is unreachable.
4. WHEN a request is received, THE API SHALL assign or propagate a Correlation_Id and SHALL include it on the response.
5. THE API SHALL record outbound LLM token usage for every AI_Engine call so that cost can be attributed per request.

### Requirement 12: Infrastructure and deployment hardening

**User Story:** As an operator, I want the deployment infrastructure to enforce TLS, resource limits, and least privilege, so that the platform is safe to expose to the internet.

#### Acceptance Criteria

1. THE Reverse_Proxy SHALL terminate HTTPS and SHALL redirect plaintext HTTP requests to HTTPS.
2. THE Reverse_Proxy SHALL set security response headers including HTTP Strict Transport Security.
3. THE deployment configuration SHALL define CPU and memory limits for the API, Worker, and Web_App services.
4. THE deployment configuration SHALL define health checks for the API, Worker, and Web_App services so that orchestration can gate readiness on application health.
5. THE container images for the API and Worker SHALL run as a non-root user.
6. THE deployment configuration SHALL source secrets from environment-specific secret stores and SHALL NOT contain hardcoded production credentials.

### Requirement 13: Test-suite reliability

**User Story:** As a developer, I want the test suite to run deterministically and offline, so that CI is reliable and tests never reach external services.

#### Acceptance Criteria

1. WHEN the backend test suite runs, THE test harness SHALL block or mock all outbound network calls so that no test depends on an external service.
2. WHEN the full backend test suite runs, THE test harness SHALL complete without hanging by enforcing a per-test timeout.
3. WHILE the test suite runs, THE test harness SHALL isolate database state between tests so that test outcomes do not depend on execution order.
4. THE repository SHALL exclude transient test artifacts (local databases, coverage files, scratch scripts) from version control.

### Requirement 14: Audit report deliverable

**User Story:** As a stakeholder, I want a verified audit report, so that I understand the security and readiness posture of the platform with evidence.

#### Acceptance Criteria

1. THE Audit_Report SHALL enumerate each finding with a severity, the file and location, a description, and the impact.
2. THE Audit_Report SHALL classify each finding by area (authentication, authorization, secrets, OAuth, rate limiting, CORS, error handling, background jobs, data integrity, migrations, observability, infrastructure, testing).
3. THE Audit_Report SHALL distinguish findings verified in code from findings that could not be verified.
4. THE Audit_Report SHALL reference existing specs where a finding is already addressed so that work is not duplicated.

### Requirement 15: Fix plan deliverable

**User Story:** As an engineering lead, I want a prioritized fix plan, so that remediation can be sequenced and tracked.

#### Acceptance Criteria

1. THE Fix_Plan SHALL map every Audit_Report finding to one or more remediation actions.
2. THE Fix_Plan SHALL assign each remediation a priority derived from the finding's severity.
3. THE Fix_Plan SHALL identify dependencies between remediations so that ordering is explicit.
4. WHERE a remediation overlaps an existing spec, THE Fix_Plan SHALL reference that spec rather than duplicate the work.

### Requirement 16: Go-live readiness checklist deliverable

**User Story:** As a release manager, I want an ordered go-live checklist, so that nothing required for a safe deployment is missed.

#### Acceptance Criteria

1. THE Go_Live_Checklist SHALL present deployment prerequisites in execution order.
2. THE Go_Live_Checklist SHALL include a verification step for each hardening requirement defined in this spec.
3. THE Go_Live_Checklist SHALL include environment-configuration, secrets, migration, TLS, observability, and rollback verification steps.
4. THE Go_Live_Checklist SHALL mark each item as required or optional for the initial production release.
