# Implementation Plan: X Integration Hardening

## Overview

This plan hardens the existing X (Twitter) integration in `apps/api` through incremental, code-focused steps. Work proceeds from shared building blocks (PKCE store, auth helper, encryption helpers, popup origin) toward the connect/callback wiring, the sync-progress and rate-limit changes, and finally the data migration and configuration guards. Each step builds on the previous ones and ends with the new code wired into the existing routers and services so nothing is left orphaned.

All implementation is in Python, matching the existing `pytest` + `Hypothesis` setup under `apps/api`. Property-based tests use Hypothesis (`@settings(max_examples=100)`), and Redis-backed tests use `fakeredis`.

## Tasks

- [x] 1. Create the durable PKCE verifier store
  - [x] 1.1 Implement the Redis-backed verifier store module
    - Create `apps/api/app/services/pkce_store.py` with `put_verifier(state, verifier)`, `take_verifier(state)`, a `VerifierStoreError`, and a 600-second TTL constant
    - `put_verifier` sets `pkce:verifier:{state}` with `ex=600`; `take_verifier` atomically gets-and-deletes via a Redis pipeline and returns `None` when absent
    - Reuse the existing `settings.REDIS_URL`; raise `VerifierStoreError` on `redis.RedisError`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 7.2_

  - [ ]* 1.2 Write property test for verifier store round-trip
    - **Property 3: PKCE verifier store round-trip**
    - **Validates: Requirements 2.1, 2.3**
    - Use `fakeredis` and `st.text(min_size=1)` for state and verifier

  - [ ]* 1.3 Write property test for single-consumption of the verifier
    - **Property 4: PKCE verifier is consumed once**
    - **Validates: Requirements 2.4**

  - [ ]* 1.4 Write property test for cross-worker retrieval
    - **Property 5: PKCE verifier is retrievable across workers**
    - **Validates: Requirements 2.5**
    - Use two independent client handles against the same fake store

  - [ ]* 1.5 Write unit tests for verifier store error and TTL behavior
    - Assert TTL ≈ 600s after `put_verifier`; assert `VerifierStoreError` is raised on store failure (distinct from a `None` miss)
    - _Requirements: 2.2, 2.6, 2.7_

- [x] 2. Add confidential-client authentication helper
  - [x] 2.1 Implement the shared client-auth selection helper
    - Add `_x_token_auth()` to `apps/api/app/routers/social_oauth.py` returning `(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)` when the secret is set, else `None`
    - _Requirements: 1.1, 1.4_

  - [ ]* 2.2 Write property test for confidential-client auth selection
    - **Property 1: Confidential-client auth selection**
    - **Validates: Requirements 1.1, 1.4**
    - Use `st.text()` for secret values including the empty string

- [x] 3. Encrypt OAuth tokens at rest
  - [x] 3.1 Add token decryption that signals undecryptable values
    - Add `TokenDecryptionError` and `decrypt_token(encrypted)` to `apps/api/app/core/security.py`, raising when a non-empty value decrypts to `""`
    - _Requirements: 5.3, 5.6_

  - [ ]* 3.2 Write property test for token encryption round-trip
    - **Property 9: Token encryption round-trip**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    - Use `st.text()` for tokens and `st.none() | st.text()` for the refresh token

  - [ ]* 3.3 Write unit test for undecryptable token handling
    - Corrupted ciphertext raises `TokenDecryptionError`
    - _Requirements: 5.6_

- [x] 4. Restrict the OAuth popup target origin
  - [x] 4.1 Derive and apply the frontend origin in the popup response
    - Add `_frontend_origin()` (scheme://netloc from `settings.FRONTEND_URL`) and change `_popup_response` to post to that origin, never `"*"`
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 4.2 Write property test for popup target origin
    - **Property 8: Popup target origin is the frontend origin and never a wildcard**
    - **Validates: Requirements 4.1, 4.2, 4.3**
    - Generate across platforms (`twitter`, `linkedin`, `instagram`) and arbitrary status/username/error inputs

- [x] 5. Checkpoint - shared building blocks
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Wire confidential-client connect and refresh through the token endpoint
  - [x] 6.1 Route the connect code exchange through Basic auth and the verifier store
    - In `twitter_callback`, replace `_pkce_store` access with `take_verifier(state)`; distinguish `VerifierStoreError` (store-unreachable popup) from a `None` miss (missing/expired popup)
    - Pass `auth=_x_token_auth()` to the code-exchange POST and drop `client_id` from the form body when Basic auth is used
    - In `/twitter/start`, call `put_verifier(state, verifier)` and remove the module-level `_pkce_store`
    - On any token-endpoint error, return `_popup_response("twitter", "error", ...)` without calling `_upsert_connection`
    - _Requirements: 1.2, 1.5, 1.7, 2.1, 2.3, 2.5, 2.6, 2.7_

  - [x] 6.2 Refactor the refresh flow to share the auth helper
    - Change `_refresh_x_token_if_needed` to obtain client auth from `_x_token_auth()` so connect and refresh share one source of truth
    - _Requirements: 1.3, 1.4, 1.6_

  - [ ]* 6.3 Write property test for no partial token persistence on connect failure
    - **Property 2: No partial token persistence on connect failure**
    - **Validates: Requirements 1.7**
    - Sample failure modes (status 400/401/403/429/500, transport error)

  - [ ]* 6.4 Write unit tests for connect/refresh Basic-auth requests
    - Assert both flows build Basic-auth requests against a mocked token endpoint and route through the shared helper; assert missing/expired vs store-error popup messages differ
    - _Requirements: 1.2, 1.3, 1.5, 1.6, 2.6, 2.7_

- [x] 7. Encrypt tokens on the connection write and read paths
  - [x] 7.1 Encrypt tokens on persistence and decrypt before use
    - In `_upsert_connection` and `_refresh_x_token_if_needed`, write `encrypt_value(access_token)` and `encrypt_value(refresh_token)` only when a refresh token is present
    - At the point of use (sync/publish/refresh), call `decrypt_token`; on `TokenDecryptionError`, flag the connection as `reconnect_required` and do not use the value
    - _Requirements: 5.1, 5.2, 5.3, 5.6_

- [x] 8. Bring Twitter sync-progress to parity with LinkedIn
  - [x] 8.1 Implement structured sync-progress helpers
    - In `apps/api/app/services/twitter_service.py`, add status constants (including `rate_limited`) and `_update_sync_progress` / `_get_sync_progress` writing under `connection_metadata["sync_progress"]`, mirroring the LinkedIn layout
    - On commit failure, roll back so the previously recorded progress is left unchanged
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_

  - [x] 8.2 Populate PlatformStatus from recorded sync-progress in get_status
    - Update `get_status` to read `_get_sync_progress` and populate `sync_status`, `sync_error`, and `sync_started_at` (parsing the ISO start timestamp)
    - _Requirements: 3.5, 3.7_

  - [ ]* 8.3 Write property test for failed progress write preserving prior progress
    - **Property 6: Failed progress write preserves prior progress**
    - **Validates: Requirements 3.4**

  - [ ]* 8.4 Write property test for status reflecting recorded sync progress
    - **Property 7: Status reflects recorded sync progress**
    - **Validates: Requirements 3.5**
    - Build `sync_progress` records with `st.fixed_dictionaries` over sampled statuses/errors/timestamps

  - [ ]* 8.5 Write unit tests for sync-progress transitions and layout
    - Assert `initiated`/`in_progress` + start timestamp, `completed`, and `failed` + message; assert Twitter keys match the LinkedIn layout
    - _Requirements: 3.1, 3.2, 3.3, 3.6_

- [x] 9. Handle rate limits during tweet sync
  - [x] 9.1 Signal rate-limit interruptions while retaining fetched tweets
    - Add `RateLimitInterruption(partial_tweets)`; in `_fetch_tweets`, raise it on HTTP 429 carrying `all_tweets[:MAX_RESULTS]`
    - In `sync_posts`, catch it, upsert the retained tweets, record `rate_limited` progress with a message, and return a non-silent `SyncResult`
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

  - [ ]* 9.2 Write property test for rate-limited sync retaining and persisting tweets
    - **Property 11: Rate-limited sync retains and persists fetched tweets**
    - **Validates: Requirements 6.1, 6.3**
    - Split `st.lists(tweet_dicts)` into pages with a 429 injected at a generated index

  - [ ]* 9.3 Write property test for rate-limited sync being distinct and non-silent
    - **Property 12: Rate-limited sync is a distinct, non-silent outcome**
    - **Validates: Requirements 6.5**

  - [ ]* 9.4 Write unit test for rate-limit status surfaced through get_status
    - Rate-limited sync records the rate-limit status/message and `get_status().sync_error` surfaces it
    - _Requirements: 6.2, 6.4_

- [x] 10. Checkpoint - connect, sync, and security paths
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Migrate existing plaintext tokens to ciphertext
  - [x] 11.1 Add an idempotent Alembic data migration
    - Create a revision under `apps/api/app/db/migrations` that probes each `social_connections` token with `_looks_like_plaintext` (decrypt returns `""` for non-empty raw values) and encrypts only plaintext rows in place
    - _Requirements: 5.5_

  - [ ]* 11.2 Write property test for migration idempotence
    - **Property 10: Token migration is idempotent**
    - **Validates: Requirements 5.5**
    - Generate rows mixing plaintext and `encrypt_value`-wrapped values; run the transform twice and assert no double-encryption

  - [ ]* 11.3 Write integration test for migration end-to-end
    - Apply the migration against a seeded table with mixed plaintext/encrypted rows, then re-apply to confirm idempotence
    - _Requirements: 5.5_

- [ ] 12. Guard the configuration boundary
  - [ ]* 12.1 Write configuration smoke tests
    - Assert the X code paths use only `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET`, and `TWITTER_REDIRECT_URI`, and that `Settings` exposes no new X-specific fields; assert `TWITTER_BEARER_TOKEN` remains unused
    - _Requirements: 7.1, 7.2, 7.3_

- [ ] 13. Integration and endpoint wiring
  - [ ]* 13.1 Write integration tests for status endpoints
    - Assert `/sync/all`, `/sync/{platform}/status`, and `/platforms` return the latest Twitter `sync_status`/`sync_error`/`sync_started_at` after a sync (1–3 representative cases)
    - _Requirements: 3.7_

- [x] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP, though they validate the universal correctness properties and key edge cases.
- Each task references specific requirements (granular acceptance-criteria clauses) for traceability.
- Checkpoints ensure incremental validation at natural boundaries.
- Property-based tests (Hypothesis, `max_examples=100`) validate Properties 1–12; `fakeredis` backs the verifier-store properties.
- No new environment variables are introduced; the Redis verifier store reuses the existing `settings.REDIS_URL`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1", "4.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "1.5", "2.2", "3.2", "3.3", "4.2", "8.1"] },
    { "id": 2, "tasks": ["6.1", "6.2", "8.2", "9.1"] },
    { "id": 3, "tasks": ["6.3", "6.4", "7.1", "8.3", "8.4", "8.5", "9.2", "9.3", "9.4", "11.1"] },
    { "id": 4, "tasks": ["11.2", "11.3", "12.1", "13.1"] }
  ]
}
```
