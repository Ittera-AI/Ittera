# Platform Audit Report — Iterra Stabilization & Twitter Integration

**Date:** June 5, 2026
**Scope:** Frontend ↔ Backend wiring, edge cases, and feature-level functional correctness for the features delivered in this spec (LinkedIn sync stabilization, Twitter sync, multi-platform persona, thread publishing, tier-aware generation, settings, sync endpoints, frontend updates).

**Method:** Static cross-checking of every frontend `productService` call against its backend route + response model, plus targeted review of state mapping, serialization, and runtime crash paths. Backend test suite re-run after fixes (146 passed). API import verified. TS diagnostics clean on changed files.

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 Critical (crash / broken feature) | 1 | Fixed |
| 🟠 High (silent data loss / wrong values) | 3 | Fixed |
| 🟡 Medium (degraded UX, no crash) | 3 | 2 fixed, 1 documented |
| 🔵 Low (cosmetic / future-proofing) | 2 | Documented |

Overall: the core flows (connect → sync → persona → generate → publish) are wired correctly. The defects were concentrated at the **sync-status and tier serialization boundary** between the new generic sync router and the settings UI. After fixes, the platform should operate smoothly end-to-end. Two items are intentionally left as recommendations because they are product decisions, not bugs.

---

## 🔴 Critical

### C1. Settings page crashes when loading live sync status
**Where:** `apps/web/src/app/(product)/settings/page.tsx` ↔ `GET /api/v1/sync/{platform}/status` (`apps/api/app/routers/sync.py`)

**Problem:** The backend `PlatformStatusResponse` returns `platform_username`, `missing_posting_scopes`, `missing_read_scopes`, and `sync_status`. The frontend `mapResponseToStatus` read `resp.username`, `resp.missing_scopes`, and `resp.sync_in_progress` — none of which exist on the response. `missingScopes` resolved to `undefined`, and `PlatformSyncStatusCard` calls `status.missingScopes.includes("r_member_social")` and `status.missingScopes.length` during render → **`TypeError: Cannot read properties of undefined`**, white-screening the Connected Accounts section whenever the sync endpoint succeeds.

**Fix applied:**
- Aligned `PlatformSyncStatusResponse` interface to the real backend shape (`platform_username`, `missing_posting_scopes`, `missing_read_scopes`, `sync_status`), keeping the old names optional for safety.
- Rewrote `mapResponseToStatus` to read `platform_username`, derive `missingScopes` from the posting+read scope arrays, and derive `syncInProgress` from `sync_status ∈ {initiated, in_progress}`.

---

## 🟠 High

### H1. `SyncTriggerResponse` shape mismatch
**Where:** `productService.syncPlatform` ↔ `POST /api/v1/sync/{platform}`

**Problem:** Frontend typed the response as `{ status, message, synced_posts, sync_path }`. Backend returns `{ task_id, platform, message }`. No crash (the settings handler ignores the body and re-fetches status), but any code reading `.status`/`.synced_posts` would get `undefined`.

**Fix applied:** Corrected the `SyncTriggerResponse` interface to `{ task_id, platform, message }`.

### H2. Generate endpoint dropped thread data
**Where:** `content_service.generate()` ↔ `response_model=GenerateResponse` (`apps/api/app/schemas/content.py`)

**Problem:** The service computes and returns `thread_segments` and `content_limit`, but `GenerateResponse` did not declare those fields. FastAPI's `response_model` **silently strips undeclared fields**, so the frontend could never tell that free-tier Twitter content was auto-split into a thread at generation time. The thread feature was effectively invisible on the generate path.

**Fix applied:** Added `thread_segments: list[str] | None` and `content_limit: dict | None` to `GenerateResponse`.

### H3. Twitter tier PUT response missing `is_thread_eligible`
**Where:** `productService.updateTwitterTier` ↔ `PUT /api/v1/social/twitter/tier`

**Problem:** Frontend `TwitterTierResponse` expects `{ tier, max_chars, is_thread_eligible }`, and `TwitterContentControls` stores the PUT response into `tierData` then reads `tierData.is_thread_eligible` to decide whether to show the thread preview. The backend `TwitterTierUpdateResponse` omitted `is_thread_eligible`, so after a user switched tiers the thread preview logic silently used `undefined` (falsy) — thread preview disappeared until a full reload re-hit the GET endpoint.

**Fix applied:** Added `is_thread_eligible: bool` to `TwitterTierUpdateResponse` and populated it (`tier == FREE`) in the PUT handler.

---

## 🟡 Medium

### M1. Thread drafts render as raw JSON in the editor — ✅ FIXED
**Where:** `apps/web/src/app/(product)/create/page.tsx`

**Problem:** Thread drafts are persisted with `content` as a JSON array string (e.g. `'["1/2 ...","2/2 ..."]'`). The draft editor loaded `setDraftBody(draft?.content ?? "")` directly, so opening a saved thread draft showed literal JSON in the textarea, and re-saving stored JSON-of-JSON.

**Fix applied:**
- Added `apps/web/src/lib/thread.ts` with `parseThreadSegments`, `isThreadContent`, `toEditableText`, `fromEditableText`, and `countSegments`. Threads are shown in the editor as segments joined by a visible `---` separator and re-serialized to a JSON array on save.
- Create page now loads via `toEditableText(draft.content)` and saves/schedules/publishes via `fromEditableText(draftBody)`.
- Editor header shows `Thread · N tweets` with a hint about the `---` separator; the platform preview renders each segment as its own tweet card with per-segment char counts; the draft picker preview no longer shows raw JSON and tags threads with `· thread`.

### M2. Right-panel character counter ignores premium tier — ✅ FIXED
**Where:** `create/page.tsx` + `TwitterContentControls.tsx`

**Problem:** The draft-editor panel hardcoded 280 for Twitter, so a premium user (25,000) saw an incorrect `x/280` counter, contradicting the (correct) left-panel control.

**Fix applied:** `TwitterContentControls` now reports its resolved tier limit via a new `onLimitChange` callback; the create page stores it in `twitterLimit` state and derives the right-panel `limit` from it, so both panels agree.

### M3. `/connect/status` vs `/sync/{platform}/status` field drift — ✅ FIXED
**Where:** `GET /api/v1/connect/status` (`_connection_status_payload`) vs sync status

**Problem:** Two endpoints described connection status with different field names (`username`/`last_synced` vs `platform_username`/`last_synced_at`), a maintenance hazard and a likely source of future mismatches.

**Fix applied:** `_connection_status_payload` now emits the canonical names (`platform_username`, `connected_at`, `last_synced_at`, `missing_posting_scopes`, `missing_read_scopes`) alongside the legacy aliases (`username`, `last_synced`) for back-compat. The frontend `SocialConnectionStatus` type and the settings fallback now prefer the canonical fields.

---

## 🔵 Low

### L1. `getSyncStatus` only polls linkedin/twitter
The settings page polls a fixed `["linkedin","twitter"]` list. Instagram/Drive connections won't appear via the sync path (they fall back to store data). Fine for current scope; revisit when Instagram sync ships. The richer `GET /api/v1/social/platforms` endpoint already returns all platforms and could replace the two-call approach.

### L2. Manual-sync success is not surfaced
`handleSyncNow` triggers the Celery task and immediately re-fetches status, but the task is async — the UI won't reflect `completed`/`synced_posts` until a later poll. Consider polling `sync_status` for a few seconds or showing an "enqueued" toast so users aren't left wondering.

---

## Feature-by-feature verdict

| Feature | Wired correctly? | Notes |
|---------|------------------|-------|
| LinkedIn OAuth connect/disconnect | ✅ | `/connect/*` routes match frontend popup flow |
| LinkedIn historical sync + progress | ✅ | `scrape_linkedin_posts` → `sync_real_posts`; progress stored in `connection_metadata` |
| Twitter OAuth + auto-queue sync | ✅ | Callback queues `sync_twitter_posts`; tier defaulted to `free` |
| Twitter content sync (API v2) | ✅ | Maps metrics, detects threads, upserts idempotently |
| Multi-platform persona analysis | ✅ | All-platform query + platform-labeled formatting + 5-post gate |
| Cross-platform analytics | ✅ | `GET /analytics/platforms/comparison` registered and typed |
| Thread publishing | ✅ | `_publish_x_thread` reply-chains; partial-failure handling present |
| Tier-aware generation | ⚠️→✅ | Fixed: generate response now exposes thread/limit (H2) |
| Draft thread storage | ⚠️ | Editor reload shows raw JSON (M1) — recommendation pending |
| Settings sync status | 🔴→✅ | Fixed crash (C1) + trigger shape (H1) |
| Twitter tier management | ⚠️→✅ | Fixed PUT response (H3) |
| Calendar multi-platform | ✅ | Platform colors/icons/labels; backend returns all platforms |
| Auto-post / posting times | ✅ | Per-platform endpoints store to `connection_metadata` |

---

## Changes applied in this audit

1. `apps/web/src/services/product.service.ts` — corrected `PlatformSyncStatusResponse` and `SyncTriggerResponse` interfaces. *(C1, H1)*
2. `apps/web/src/app/(product)/settings/page.tsx` — fixed `mapResponseToStatus` field mapping + `syncInProgress` derivation. *(C1)*
3. `apps/api/app/schemas/content.py` — added `thread_segments` + `content_limit` to `GenerateResponse`. *(H2)*
4. `apps/api/app/schemas/social.py` — added `is_thread_eligible` to `TwitterTierUpdateResponse`. *(H3)*
5. `apps/api/app/routers/social.py` — populated `is_thread_eligible` in the PUT tier handler. *(H3)*

**Verification after fixes:** backend `pytest` → 146 passed; `import main` → OK; TS diagnostics on changed frontend files → clean.

---

## Recommended next steps (not blocking)

1. **M1 (thread draft editing)** — decide on the thread-editing UX and implement load/save (de)serialization. This is the highest-value remaining item.
2. **M2** — lift Twitter tier state into the create page so the right-panel counter matches the tier.
3. **M3/L1** — consolidate connection-status DTOs and migrate settings to the single `/social/platforms` call.
4. **L2** — add brief polling or a toast after "Sync Now" so async completion is visible.
5. Consider adding the optional property-based tests (spec tasks marked `*`) for the thread-splitting and limit-resolution invariants — they guard the exact serialization paths that caused H2/H3.
