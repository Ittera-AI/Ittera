# Implementation Plan: Iterra Platform Stabilization & Twitter Integration

## Overview

This plan implements six interconnected goals: stabilizing LinkedIn historical content sync, implementing Twitter/X content retrieval, enabling multi-platform persona analysis, adding Twitter thread publishing, formalizing a provider pattern, and enforcing platform-aware content generation limits. Implementation proceeds from foundational interfaces through platform services, then wires everything together with frontend updates.

## Tasks

- [x] 1. Define ContentSyncProvider protocol and shared data structures
  - [x] 1.1 Create `app/services/content_sync_provider.py` with the `ContentSyncProvider` Protocol class, `SyncResult` dataclass, and `PlatformStatus` dataclass
    - Define the Protocol with `sync_posts`, `get_status`, and `map_post` methods
    - Define `SyncResult` with fields: synced_posts, total_posts, last_synced_at, message, ready_for_analysis, sync_path
    - Define `PlatformStatus` with fields: connected, platform_username, last_synced_at, synced_posts, scopes, posting_ready, read_sync_ready, missing_posting_scopes, missing_read_scopes, reconnect_required, message
    - _Requirements: 7.1, 7.2, 7.4_

  - [x] 1.2 Create `app/services/platform_limits.py` with `TwitterTier` enum, `ContentLimit` dataclass, `resolve_content_limit`, `_get_twitter_tier`, `update_twitter_tier`, `split_into_thread`, `_word_boundary_split`, and `is_thread` functions
    - Implement `PLATFORM_CHAR_LIMITS` dict with LinkedIn (3000), Instagram (2200), Twitter (free: 280, premium: 25000)
    - Implement `resolve_content_limit` to resolve tier-aware limits from `connection_metadata`
    - Implement `split_into_thread` algorithm using sentence-boundary splitting with thread numbering
    - Implement `is_thread` helper for detecting thread content (JSON array)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.8_

  - [ ]* 1.3 Write property test for platform limit resolution (Property 9)
    - **Property 9: Platform-aware character limit enforcement**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.8**
    - Test file: `tests/test_content_limits_props.py`
    - Generator: random strings × all platform+tier combos

  - [ ]* 1.4 Write property test for thread splitting (Property 10)
    - **Property 10: Thread splitting preserves content within limits at sentence boundaries**
    - **Validates: Requirements 8.5, 8.6**
    - Test file: `tests/test_thread_split_props.py`
    - Generator: random multi-sentence strings (281-10000 chars) with varied sentence lengths

  - [ ]* 1.5 Write property test for content length validation flag (Property 11)
    - **Property 11: Content length validation flag correctness**
    - **Validates: Requirements 8.7**
    - Test file: `tests/test_content_limits_props.py`
    - Generator: random content strings × random positive limit values

- [x] 2. Stabilize LinkedIn historical content sync
  - [x] 2.1 Refactor `linkedin_service.py` to implement the `ContentSyncProvider` protocol
    - Add `platform = "linkedin"` attribute
    - Ensure `sync_posts` method returns `SyncResult` matching the protocol
    - Implement `get_status` method returning `PlatformStatus` with scope-awareness (detect missing `r_member_social`)
    - Implement `map_post` (rename/wrap existing `map_ugc_post`) to conform to protocol
    - Store raw API responses for debugging (requirement 1.3)
    - _Requirements: 1.1, 1.3, 1.4, 7.1, 7.4_

  - [ ]* 2.2 Write property test for LinkedIn post mapping (Property 1)
    - **Property 1: LinkedIn post mapping preserves required fields**
    - **Validates: Requirements 1.1**
    - Test file: `tests/test_linkedin_mapping_props.py`
    - Generator: random UGC post dicts with optional fields

  - [x] 2.3 Add sync progress tracking to LinkedIn service
    - Implement real-time sync status updates: initiated, in-progress, completed, failed
    - Store sync state per connection in `connection_metadata` or a status field
    - On completion, update last_synced_at and post count
    - Handle token expiry during retrieval gracefully (prompt reconnect without losing fetched data)
    - _Requirements: 1.2, 1.5, 1.8, 1.9_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Twitter/X content sync service
  - [x] 4.1 Create `app/services/twitter_service.py` implementing `ContentSyncProvider`
    - Implement `TwitterSyncService` class with `platform = "twitter"`
    - Implement `sync_posts`: fetch up to 100 tweets via Twitter API v2 `/2/users/:id/tweets` with fields `created_at,public_metrics,conversation_id,in_reply_to_user_id,referenced_tweets`
    - Implement token refresh reusing existing `_refresh_x_token_if_needed`
    - Implement pagination handling
    - Implement `map_tweet`: map Twitter v2 response to Post model dict (content, platform_post_id, published_at, content_type, engagement metrics)
    - Implement `detect_threads`: group tweets by `conversation_id` where author replied to self
    - Implement `get_status`: return Twitter connection/sync status
    - Implement upsert logic with deduplication on `platform_post_id`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.9_

  - [ ]* 4.2 Write property test for tweet mapping (Property 2)
    - **Property 2: Tweet mapping preserves required fields**
    - **Validates: Requirements 2.1, 2.2**
    - Test file: `tests/test_twitter_mapping_props.py`
    - Generator: random Twitter v2 tweet objects

  - [ ]* 4.3 Write property test for upsert idempotence (Property 3)
    - **Property 3: Post upsert is idempotent**
    - **Validates: Requirements 2.4**
    - Test file: `tests/test_upsert_props.py`
    - Generator: random lists of post dicts with repeated IDs

  - [x] 4.4 Create Celery task for Twitter content sync
    - Add `sync_twitter_posts` task in `app/tasks/` that calls `TwitterSyncService.sync_posts`
    - Wire Twitter OAuth callback to automatically queue the sync task on successful connection
    - Support manual re-sync trigger from settings
    - Chain brand profile analysis after sync if post threshold met
    - _Requirements: 2.7, 2.8_

- [x] 5. Implement multi-platform brand profile analysis
  - [x] 5.1 Update `BrandProfileService.generate_profile()` to pull posts from all platforms
    - Remove platform filter from post query (currently LinkedIn-only)
    - Update `_format_posts_for_engine()` to annotate each post with platform label (e.g., `TWITTER`, `LINKEDIN`)
    - Add platform-specific style variation notes in the prompt sent to the AI engine
    - Enforce minimum 5 posts threshold across all platforms before triggering generation
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

  - [ ]* 5.2 Write property test for multi-platform post inclusion (Property 4)
    - **Property 4: Multi-platform posts included in brand profile input**
    - **Validates: Requirements 3.1**
    - Test file: `tests/test_brand_profile_props.py`
    - Generator: random posts across 2-3 platforms

  - [ ]* 5.3 Write property test for minimum post threshold (Property 5)
    - **Property 5: Minimum post threshold gates analysis**
    - **Validates: Requirements 3.3**
    - Test file: `tests/test_brand_profile_props.py`
    - Generator: random post counts (0-20) across platforms

  - [x] 5.4 Add cross-platform engagement comparison to performance analysis
    - Extend analytics queries to compare engagement patterns across platforms
    - _Requirements: 3.4_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Twitter thread publishing
  - [x] 7.1 Extend `publisher_service.py` with `_publish_x_thread` function
    - Implement sequential tweet publishing with reply chaining (each tweet replies to previous)
    - Validate each segment is within character limit before publishing
    - Handle partial failures: store IDs of successfully published tweets, mark draft as "failed" with partial data
    - Return `platform_post_id` as first tweet ID, plus `thread_ids` array
    - _Requirements: 4.3, 4.4_

  - [x] 7.2 Update `_publish_x` to be tier-aware and handle thread detection
    - Use `resolve_content_limit` for dynamic character limits instead of hard-coded `[:280]`
    - Detect thread content via `is_thread()` and route to `_publish_x_thread`
    - Implement automatic token refresh before publishing; prompt reconnect if refresh fails
    - _Requirements: 4.7, 4.8, 8.2, 8.3_

  - [ ]* 7.3 Write property test for thread reply chaining (Property 6)
    - **Property 6: Thread publishing chains replies correctly**
    - **Validates: Requirements 4.2**
    - Test file: `tests/test_thread_publish_props.py`
    - Generator: random threads (2-25 segments, varied content)

  - [x] 7.4 Update `POST /drafts` endpoint to accept thread content as JSON array
    - Validate thread segments on creation (each within character limit)
    - Store thread as JSON array string in `content_drafts.content`
    - _Requirements: 4.4_

- [x] 8. Integrate tier-aware content generation
  - [x] 8.1 Update `content_service.py` `generate()` to resolve tier-aware limits
    - Call `resolve_content_limit(db, user.id, platform)` before generating content
    - Override `platform_rules` `max_chars` with the resolved limit
    - After generation, validate output length and set `within_platform_limit` flag
    - If free-tier Twitter content exceeds 280 chars, auto-split into thread via `split_into_thread`
    - Store draft as thread JSON if split, plain text otherwise
    - Return `content_limit` metadata in response (platform, max_chars, tier)
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 8.7_

  - [x] 8.2 Add Twitter tier management to settings/connection flow
    - Store `subscription_tier` in `connection_metadata` on the Twitter `social_connections` row
    - Default to `"free"` when tier is unknown or missing
    - Implement `update_twitter_tier` endpoint callable from settings
    - When tier changes, apply new limits to subsequent generations
    - _Requirements: 8.4, 8.8, 8.9_

  - [x] 8.3 Update content repurposing to respect tier-aware Twitter limits
    - When repurposing LinkedIn → Twitter, resolve the user's Twitter tier and apply the correct character limit
    - Use Brand_Profile for voice consistency during repurposing
    - Allow repurposed drafts to be independently schedulable
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 8.4 Write property test for repurposed content character limit (Property 8)
    - **Property 8: Repurposed Twitter content respects character limit**
    - **Validates: Requirements 6.1**
    - Test file: `tests/test_repurpose_props.py`
    - Generator: random LinkedIn posts (50-5000 chars)

- [x] 9. Implement sync API endpoints and settings page backend
  - [x] 9.1 Create sync router with generic `/api/sync/{platform}` and `/api/sync/{platform}/status` endpoints
    - `POST /api/sync/{platform}`: trigger manual sync for any platform (routes to correct provider)
    - `GET /api/sync/{platform}/status`: return `PlatformStatus` for the platform
    - Register provider services via a registry dict keyed by platform name
    - _Requirements: 5.4, 5.5, 7.1, 7.5_

  - [x] 9.2 Implement settings data endpoint returning all connected platforms
    - Return per-platform: username, connection date, last sync time, posting readiness, sync readiness, missing scopes
    - Include sync-in-progress indicator and error states
    - Support disconnect/reconnect actions
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 9.3 Add auto-post toggle and preferred posting times per platform
    - Store auto-post preference and posting times per platform in connection metadata or user preferences
    - _Requirements: 5.6, 5.7_

- [x] 10. Implement frontend updates
  - [x] 10.1 Build settings page sync status component
    - Implement `PlatformSyncStatus` interface in TypeScript
    - Show per-platform: connected username, last sync time, sync readiness, posting readiness, missing scopes
    - Add "Sync Now" button per platform with loading state
    - Show LinkedIn scope limitation message when `r_member_social` is missing
    - Show sync progress (initiated, in-progress, completed, failed)
    - Display number of posts imported after sync completion
    - _Requirements: 1.4, 1.5, 1.6, 1.8, 1.9, 2.8, 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 10.2 Update calendar page to display multi-platform posts
    - Show Twitter and LinkedIn posts in the calendar view
    - Visually differentiate posts by platform (icon, color, or label)
    - Include platform identifier in each calendar event
    - _Requirements: 4.5, 4.6, 7.6_

  - [ ]* 10.3 Write property test for calendar including all platforms (Property 7)
    - **Property 7: Calendar includes all platform drafts**
    - **Validates: Requirements 4.3**
    - Test file: `tests/test_calendar_props.py`
    - Generator: random scheduled drafts across platforms

  - [x] 10.4 Update content creation page for Twitter support
    - Allow Twitter as target platform selection
    - Show real-time character count against tier-aware limit
    - Display thread preview when free-tier content exceeds 280 chars
    - Add Twitter tier selector in settings (free/premium)
    - Show post-threshold progress toward brand profile generation (X/5 posts)
    - _Requirements: 4.1, 4.2, 3.6, 8.4, 8.9_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- No database migrations required — all data fits existing schema via the `platform` column and `connection_metadata` JSON
- Thread content stored as JSON array in `content_drafts.content`
- Twitter subscription tier stored in `connection_metadata` on social_connections

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "1.4", "1.5", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "4.1"] },
    { "id": 3, "tasks": ["4.2", "4.3", "4.4", "5.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "5.4", "7.1"] },
    { "id": 5, "tasks": ["7.2", "7.3", "7.4", "8.1"] },
    { "id": 6, "tasks": ["8.2", "8.3", "8.4", "9.1"] },
    { "id": 7, "tasks": ["9.2", "9.3", "10.1"] },
    { "id": 8, "tasks": ["10.2", "10.3", "10.4"] }
  ]
}
```
