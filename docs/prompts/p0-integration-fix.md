# P0 Integration Fix — Agent Prompt

Use this prompt in **Agent mode** as a single focused PR **before** Cofounders A and B split parallel work.

**Context doc:** [docs/vc-demo-mvp-plan.md](../vc-demo-mvp-plan.md)

---

## Task

Fix the **integration layer** of the Iterra monorepo so persona onboarding, social OAuth, and waitlist gating work end-to-end. Do **not** implement PermanentContext, the context assembler, or the full three-layer LLM generate pipeline — those are Phase 1 A/B work immediately after this PR merges.

Minimize scope. No unrelated refactors.

---

## Goals (all must pass)

1. API starts without import errors
2. `POST /api/v1/persona/onboarding/start` works with Supabase JWT
3. OAuth popup flow works for Twitter/X at minimum (`/api/v1/connect/twitter/start` or equivalent mounted path)
4. Persona scrape + analyze works for X-connected user when `OPENAI_API_KEY` is set
5. Waitlist `GET /me` returns `access_approved`; admin endpoints approve/revoke users
6. Frontend persona onboarding page completes without runtime/TypeScript errors
7. `make types` run; shared-types committed if changed
8. Existing `apps/api/tests/test_mock_mvp_flow.py` still passes

---

## Backend tasks

### 1. Mount routers in `apps/api/main.py`

- Include persona router at prefix `/api/v1/persona`
- Fix persona router internal prefix if it uses `/v1/persona` (see `apps/api/app/routers/persona.py` line 13)
- Include `social_oauth` router at prefix `/api/v1/connect`

### 2. Fix `social_oauth.py` auth

- Either implement `_fetch_supabase_user(token)` in `apps/api/app/dependencies/auth.py` (Supabase userinfo fallback when JWT secret decode fails)
- Or remove the import and use only `_decode_supabase_jwt` / `_decode_legacy_jwt`
- Add missing settings to `apps/api/config.py` and `.env.example`:
  - `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET`, `TWITTER_REDIRECT_URI`
  - LinkedIn/Instagram vars as empty defaults if referenced

### 3. Fix persona router

- Ensure all routes live under `/api/v1/persona/*`
- Register `PersonaProfile`, `PersonaSource`, `PersonaDocument`, `PersonaInsight` in `apps/api/app/models/__init__.py`
- In scrape path: accept `source_type` `"twitter"` and normalize to `"x"` before calling `ScraperService`

### 4. Fix waitlist approval

- Update `apps/api/app/models/waitlist.py` with `access_approved`, `approved_at`, `approved_by` (migration `003` already exists)
- Update `apps/api/app/schemas/waitlist.py` — `WaitlistMemberStatusResponse` includes `access_approved`, `approved_at`
- Update `GET /api/v1/waitlist/me` to return those fields
- Add admin routes (protect with admin email list from env `ADMIN_EMAILS` comma-separated):
  - `GET /api/v1/waitlist/admin/entries` → `{ entries: [...] }`
  - `POST /api/v1/waitlist/admin/approve` body `{ email }`
  - `POST /api/v1/waitlist/admin/revoke` body `{ email }`

### 5. Persona → user onboarding

- After successful persona analyze, populate user `niche`, `full_name`/`name`, `onboarding_complete=true`
- **Or** fix frontend to call `POST /api/v1/auth/onboarding` with required fields from persona result (`full_name`, `niche`, `primary_platform` per `OnboardingRequest`)

---

## Frontend tasks (minimal for integration)

### 6. Complete `apps/web/src/lib/api.ts`

Add namespaces:

```typescript
connect.status()
connect.startUrl(platform, token)
connect.disconnect(platform)

persona.startOnboarding()
persona.addSource(payload)
persona.listSources()
persona.scrape()
persona.analyze()
persona.get()
persona.update(payload)
persona.confirm()
```

Export types: `PersonaProfile`, `SocialConnectionStatus`

Use Supabase bearer token (same pattern as `apps/web/src/services/api.ts`). Prefer same-origin proxy in dev.

### 7. Fix `apps/web/src/context/AuthContext.tsx`

Add:

- `hasWorkspaceAccess`
- `workspaceAccessLoading`
- `workspaceAccessChecked`
- `waitlistPosition`
- `refreshWorkspaceAccess()`
- `isAdmin` (from `ADMIN_EMAILS` env or user email list)

Derive workspace access from `GET /api/v1/waitlist/me` (`access_approved`).

### 8. Wire `AuthShell` in `apps/web/src/app/layout.tsx`

Wrap children inside `AuthProvider`:

```tsx
<AuthProvider>
  <AuthShell>{children}</AuthShell>
</AuthProvider>
```

Import from `apps/web/src/components/auth/AuthShell.tsx`.

### 9. Export `hasStoredSupabaseSession()` from `apps/web/src/lib/supabase.ts`

Used by `SessionRouteGuard` — check for Supabase session in local storage / client.

### 10. Fix `apps/web/src/app/(auth)/onboarding/persona/page.tsx`

- Use `source_type: "x"` for Twitter **or** rely on backend normalization
- Call onboarding with `{ full_name, niche, primary_platform }` from persona result (not `primary_platform` alone)
- OAuth `startUrl` must match mounted backend path (`/api/v1/connect/twitter/start?token=...`)

### 11. Add onboarding route placeholder

- Create `/onboarding/context` route (minimal form or “Step 1 coming in Phase 1” stub)
- Document in PR description which approach was chosen

---

## Explicit non-goals (defer to Phase 1–2)

- `PermanentContext` model and API
- Context assembler / `ContextBundle`
- Drive write after persona/metrics analyze
- Metrics analysis service
- Fact promotion / `optimal_post_times` learning loop
- LLM upgrades for content, coach, calendar, radar
- Real LinkedIn/Instagram scraping
- Smart calendar UI
- Analytics score bar fix (`/10` not `/100`)
- Deprecating legacy brand profile system
- Celery scheduled publish worker

---

## Verification

```bash
cd apps/api && pytest tests/ -q
bash scripts/gen_types.sh
git diff --exit-code packages/shared-types/src/index.ts
cd apps/web && npm run build
```

### Manual smoke test

1. Sign in with Supabase → complete persona flow with X → land on dashboard
2. Admin: approve another waitlist email → user passes waitlist gate
3. Legacy flow: `pytest apps/api/tests/test_mock_mvp_flow.py` green

---

## Output

- Single PR: `fix: wire persona, social OAuth, and waitlist approval for demo`
- List new env vars in `.env.example`
- PR description notes remaining Phase 1 items for cofounder A/B split per [vc-demo-mvp-plan.md](../vc-demo-mvp-plan.md)
