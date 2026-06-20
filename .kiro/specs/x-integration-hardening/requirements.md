# Requirements Document

## Introduction

This feature hardens the existing X (Twitter) integration in the Iterra codebase. The user is migrating X access to the official X API on a usage-based / pay-as-you-go plan. This is a billing change only: the same OAuth 2.0 + PKCE flow, the same endpoints (`GET /2/users/:id/tweets`, `POST /2/tweets`, media upload, token refresh), and the same environment variables remain in use. No new environment variables are introduced.

A diagnosis of the current integration surfaced concrete loose ends. This spec addresses them in priority order. Two items are critical (must-have) because they block reliable connect/refresh across the deployed multi-worker environment; the remainder are should-have correctness, security, and observability fixes.

Scope is strictly the X/Twitter integration plus the two shared social-OAuth security fixes (postMessage origin restriction and token-at-rest encryption) that live on code paths shared by all platforms. LinkedIn read-scope strategy is explicitly **out of scope** for this spec.

## Glossary

- **X_Integration**: The collection of backend components that connect to, sync from, and publish to X (Twitter), spanning `social_oauth.py`, `publisher_service.py`, and `twitter_service.py`.
- **OAuth_Connect_Flow**: The authorization-code exchange performed in `twitter_callback` that converts an authorization code into access and refresh tokens.
- **Token_Refresh_Flow**: The refresh-token exchange performed in `_refresh_x_token_if_needed` that obtains a new access token before expiry.
- **Confidential_Client**: An OAuth 2.0 client that holds a client secret and authenticates to the token endpoint using HTTP Basic authentication (`client_id:client_secret`).
- **PKCE_Verifier**: The `code_verifier` generated at the start of the OAuth flow and required to complete the authorization-code exchange.
- **Verifier_Store**: The shared, persistent store (Redis) used to hold a `PKCE_Verifier` between the `/twitter/start` and `/twitter/callback` requests, keyed by OAuth `state`.
- **Twitter_Sync_Service**: The `TwitterSyncService` component that fetches and persists a user's tweets and reports status via `get_status()`.
- **Sync_Progress**: The structured sync-status record (status, started-at, error) stored in `connection_metadata` and surfaced through `PlatformStatus`.
- **OAuth_Popup**: The HTML page returned by `_popup_response` that calls `window.opener.postMessage` to report connect success or failure to the frontend.
- **Token_Storage**: The persistence of `access_token` and `refresh_token` columns on the `social_connections` table.
- **Encryption_Helpers**: The `encrypt_value` / `decrypt_value` functions in `app/core/security.py`.
- **Frontend_Origin**: The web origin configured in `settings.FRONTEND_URL`.
- **Rate_Limit_Response**: An HTTP 429 response returned by the X API during tweet retrieval.

## Requirements

### Requirement 1: Consistent confidential-client authentication (CRITICAL)

**User Story:** As an Iterra operator migrating to the official X API, I want the initial code exchange and the token refresh to authenticate the client the same way, so that connecting and refreshing X both succeed reliably.

#### Acceptance Criteria

1. WHERE a client secret is configured in `settings.TWITTER_CLIENT_SECRET`, THE X_Integration SHALL treat the X application as a Confidential_Client for all token-endpoint requests.
2. WHILE the X application is treated as a Confidential_Client, WHEN the OAuth_Connect_Flow exchanges an authorization code, THE X_Integration SHALL authenticate to the token endpoint using HTTP Basic authentication with `client_id` and `client_secret`.
3. WHILE the X application is treated as a Confidential_Client, WHEN the Token_Refresh_Flow exchanges a refresh token, THE X_Integration SHALL authenticate to the token endpoint using HTTP Basic authentication with `client_id` and `client_secret`.
4. THE X_Integration SHALL use only HTTP Basic authentication as the client-authentication method for the OAuth_Connect_Flow and the Token_Refresh_Flow.
5. WHEN a user completes the OAuth_Connect_Flow with a configured client secret, THE X_Integration SHALL persist a valid access token and refresh token to the connection record.
6. WHEN the Token_Refresh_Flow runs for a connection that has a refresh token and a configured client secret, THE X_Integration SHALL obtain and persist a new access token.
7. IF any condition prevents successful connection establishment during the OAuth_Connect_Flow, including a token-endpoint authentication error, THEN THE X_Integration SHALL report a connect failure to the OAuth_Popup without persisting partial tokens.

### Requirement 2: Durable PKCE verifier persistence (CRITICAL)

**User Story:** As a user connecting X in a multi-worker deployment, I want my OAuth flow to complete regardless of which worker handles the callback, so that connecting X does not intermittently fail.

#### Acceptance Criteria

1. WHEN the OAuth_Connect_Flow starts at `/twitter/start`, THE X_Integration SHALL store the PKCE_Verifier in the Verifier_Store keyed by the OAuth `state` value.
2. WHEN the PKCE_Verifier is stored in the Verifier_Store, THE X_Integration SHALL set a time-to-live of 10 minutes on the stored entry.
3. WHEN `/twitter/callback` is invoked with a valid `state`, THE X_Integration SHALL retrieve the PKCE_Verifier from the Verifier_Store using that `state`.
4. WHEN the PKCE_Verifier is retrieved during `/twitter/callback`, THE X_Integration SHALL delete the stored entry from the Verifier_Store.
5. WHERE the deployment runs multiple worker processes or replicas, WHEN the worker handling `/twitter/callback` differs from the worker that handled `/twitter/start`, THE X_Integration SHALL retrieve the PKCE_Verifier successfully.
6. IF the PKCE_Verifier is absent or expired at `/twitter/callback`, THEN THE X_Integration SHALL report a connect failure to the OAuth_Popup with a message indicating the verifier is missing or expired.
7. IF retrieval of the PKCE_Verifier from the Verifier_Store fails due to a store or network error, THEN THE X_Integration SHALL report a connect failure to the OAuth_Popup with a message distinct from the missing-or-expired-verifier message.

### Requirement 3: Twitter sync-progress visibility

**User Story:** As a user on the settings page, I want to see when an X sync is in progress or has failed, so that I can tell whether my X content is being fetched.

#### Acceptance Criteria

1. WHEN the Twitter_Sync_Service begins a sync, THE Twitter_Sync_Service SHALL record Sync_Progress with status "initiated" or "in_progress" and a sync-start timestamp in `connection_metadata`.
2. WHEN the Twitter_Sync_Service completes a sync successfully, THE Twitter_Sync_Service SHALL record Sync_Progress with status "completed".
3. WHEN the Twitter_Sync_Service fails a sync, THE Twitter_Sync_Service SHALL record Sync_Progress with status "failed" and a descriptive error message.
4. IF recording Sync_Progress fails, THEN THE Twitter_Sync_Service SHALL leave the previously recorded Sync_Progress unchanged.
5. WHEN `get_status()` is called for the Twitter connection, THE Twitter_Sync_Service SHALL read the recorded Sync_Progress and populate `sync_status`, `sync_error`, and `sync_started_at` on the returned `PlatformStatus`.
6. THE Twitter_Sync_Service SHALL structure Sync_Progress using the same `connection_metadata` layout that the LinkedIn sync service uses.
7. WHEN the `/sync/all`, `/sync/{platform}/status`, or `/platforms` endpoint reports Twitter status, THE X_Integration SHALL return the Twitter `sync_status`, `sync_error`, and `sync_started_at` values that reflect the most recent sync.

### Requirement 4: Restrict OAuth popup postMessage origin

**User Story:** As a security-conscious operator, I want the OAuth popup to send its result only to the application frontend, so that connection results and usernames are not leaked to arbitrary opener origins.

#### Acceptance Criteria

1. WHEN the OAuth_Popup posts a result to its opener, THE OAuth_Popup SHALL set the `postMessage` target origin to the Frontend_Origin.
2. THE OAuth_Popup SHALL NOT use a wildcard (`"*"`) target origin when posting the result in any environment, requiring the Frontend_Origin to be configured per environment.
3. THE OAuth_Popup SHALL apply the Frontend_Origin restriction for every platform that uses the shared popup response, including X, LinkedIn, and Instagram.

### Requirement 5: Encrypt OAuth tokens at rest

**User Story:** As a security-conscious operator, I want stored OAuth access and refresh tokens to be encrypted at rest, so that a database disclosure does not expose usable platform credentials.

#### Acceptance Criteria

1. WHEN a social connection's `access_token` is written to Token_Storage, THE X_Integration SHALL encrypt the value using the Encryption_Helpers before persistence.
2. WHEN a social connection's `refresh_token` is written to Token_Storage and a refresh token is present, THE X_Integration SHALL encrypt the value using the Encryption_Helpers before persistence.
3. WHEN a stored `access_token` or `refresh_token` is read for use in an API call, THE X_Integration SHALL decrypt the value using the Encryption_Helpers before use.
4. FOR ALL social connections, writing a token then reading it back SHALL yield the original plaintext token value (round-trip property).
5. THE X_Integration SHALL provide a migration path that encrypts existing plaintext `access_token` and `refresh_token` rows in `social_connections`.
6. IF a stored token value cannot be decrypted, THEN THE X_Integration SHALL treat the connection as requiring reconnection rather than using an unusable token.

### Requirement 6: Graceful rate-limit handling during tweet sync

**User Story:** As a user syncing my X content, I want rate-limit conditions to be surfaced clearly while keeping the tweets already fetched, so that a partial sync does not look like an empty or silent failure.

#### Acceptance Criteria

1. WHEN the X API returns a Rate_Limit_Response during tweet retrieval after one or more tweets have been fetched, THE Twitter_Sync_Service SHALL retain the tweets that were already fetched in the current sync.
2. WHEN a Rate_Limit_Response interrupts tweet retrieval, THE Twitter_Sync_Service SHALL record Sync_Progress with a status and error message indicating that X rate limiting occurred.
3. WHEN a sync is interrupted by a Rate_Limit_Response, THE Twitter_Sync_Service SHALL persist any retained tweets that were successfully fetched.
4. WHEN `get_status()` is called after a rate-limited sync, THE Twitter_Sync_Service SHALL surface the rate-limit message through the `PlatformStatus` error field.
5. THE Twitter_Sync_Service SHALL report a rate-limited sync as a distinct, non-silent outcome rather than reporting an unqualified success with zero synced tweets.

### Requirement 7: No new environment variables for the official X API

**User Story:** As an operator deploying the pay-as-you-go X API change, I want to reuse the existing configuration, so that the billing migration requires no new secrets or deployment changes.

#### Acceptance Criteria

1. THE X_Integration SHALL operate against the official X API using only the existing `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET`, and `TWITTER_REDIRECT_URI` settings.
2. THE X_Integration SHALL NOT require any new environment variable to complete connect, sync, refresh, or publish on the pay-as-you-go plan, and SHALL source all X credentials from the existing `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET`, and `TWITTER_REDIRECT_URI` settings rather than hardcoded values or other configuration sources.
3. THE X_Integration SHALL treat an app-only `TWITTER_BEARER_TOKEN` as out of scope unless reading non-connected public accounts is later required.
