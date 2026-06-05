# Requirements Document

## Introduction

Stabilize the existing Ittera platform by fixing critical integration gaps (primarily LinkedIn historical content retrieval), then implement Twitter/X as a fully integrated provider with feature parity to LinkedIn — using the existing multi-platform architecture. Additionally, ensure the content generation engine respects platform-specific character limits based on user subscription tiers.

## Glossary

- **Ittera_Platform**: The AI-powered social media content management platform that supports multi-platform publishing, analytics, and persona-based content generation.
- **Content_Engine**: The AI writing/generation subsystem responsible for producing platform-appropriate content drafts.
- **Social_Connection**: A linked social media account stored in the `social_connections` table, including OAuth credentials and platform metadata.
- **Twitter_Free_Tier**: A standard Twitter/X account with a 280-character post limit.
- **Twitter_Premium_Tier**: A Twitter/X Premium (paid) subscriber account with a 25,000-character post limit.
- **LinkedIn_Platform**: The LinkedIn social network with a 3,000-character post limit.
- **Thread**: A sequence of connected tweets published as a series, used to convey content exceeding the single-tweet character limit.
- **Subscription_Tier**: The user's subscription level on a given platform, which determines platform feature limits (e.g., character count).
- **Brand_Profile**: An AI-generated persona profile derived from historical posts across connected platforms.
- **Content_Sync**: The process of retrieving historical posts from a connected platform and storing them in the Ittera database.
- **Publisher_Service**: The backend service responsible for dispatching content to the appropriate social platform API.

## Current State Analysis

### What Works
- LinkedIn OAuth 2.0 connection (social_oauth.py)
- Twitter OAuth 2.0 connection with PKCE (social_oauth.py)
- Instagram OAuth connection (social_oauth.py)
- Content calendar (scheduling, viewing, managing)
- Content drafts (CRUD, media attachments)
- Publishing to LinkedIn (text + single image via REST API)
- Publishing to Twitter/X (text + up to 4 images)
- Brand profile generation (AI-powered)
- Coach/Radar/Repurpose AI engines
- Analytics with AI post analysis
- Zustand product store with caching
- Frontend pages: dashboard, calendar, create, coach, radar, analytics, settings

### What's Partially Working
- LinkedIn historical content retrieval (requires r_member_social scope — separate approval from LinkedIn)
- Cookie-based LinkedIn scraper fallback (requires stored credentials)
- Performance sync (Celery worker for engagement metric updates)

### What's Missing or Broken
- Twitter/X historical content retrieval (no service implemented)
- Twitter content sync into posts table
- Multi-platform persona analysis (currently LinkedIn-only data source)
- Onboarding flow completion (persona page exists but flow unclear)
- Historical content import UX (user doesn't see progress/status clearly)

---

## Requirements

### Requirement 1: LinkedIn Historical Content Retrieval Stabilization

**User Story:** As a content creator, I want reliable retrieval of my historical LinkedIn posts, so that the platform can extract my persona and writing patterns.

**Priority: P0 (Critical)**

#### Acceptance Criteria

1. WHEN a user has `r_member_social` scope granted, THE Ittera_Platform SHALL fetch up to 50 historical posts via the LinkedIn UGC Posts API
2. WHEN a token expires during retrieval, THE Ittera_Platform SHALL prompt the user for reconnection without losing previously fetched data
3. THE Ittera_Platform SHALL store raw API responses for debugging purposes
4. WHEN `r_member_social` scope is missing, THE Ittera_Platform SHALL display a message explaining that this is a LinkedIn developer app approval requirement
5. THE Ittera_Platform SHALL show sync readiness status per platform on the settings page
6. IF the OAuth API fails due to missing scopes, THEN THE Ittera_Platform SHALL provide clear messaging about alternative approaches
7. THE Ittera_Platform SHALL maintain the cookie-auth fallback path as functional for users who provide credentials
8. WHEN a sync operation initiates, THE Ittera_Platform SHALL display real-time progress (initiated, in-progress, completed, failed)
9. WHEN sync completes, THE Ittera_Platform SHALL show the number of posts imported and whether analysis is ready

---

### Requirement 2: Twitter/X Historical Content Retrieval

**User Story:** As a content creator, I want the platform to retrieve my historical tweets, so that persona extraction and performance analysis include my Twitter activity.

**Priority: P1 (Core Functionality)**

#### Acceptance Criteria

1. THE Ittera_Platform SHALL implement a Twitter content sync service parallel to the existing linkedin_service.py
2. WHEN a Twitter account is connected, THE Content_Sync SHALL fetch the user's recent tweets (up to 100) using Twitter API v2
3. THE Content_Sync SHALL store tweets in the existing `posts` table with `platform = "twitter"`
4. WHEN storing a tweet, THE Ittera_Platform SHALL capture: content, platform_post_id, published_at, and content_type
5. WHEN storing engagement metrics, THE Ittera_Platform SHALL capture: likes, retweets, replies, and impressions where available
6. WHEN sequential tweets are in reply to the same user's own tweets, THE Ittera_Platform SHALL identify and link them as a thread
7. WHEN Twitter OAuth callback completes successfully, THE Ittera_Platform SHALL automatically queue a content sync task via Celery
8. THE Ittera_Platform SHALL allow users to trigger a manual re-sync from the settings page
9. WHEN re-syncing, THE Ittera_Platform SHALL deduplicate posts by upserting on platform_post_id

---

### Requirement 3: Multi-Platform Persona Analysis

**User Story:** As a content creator, I want my brand profile to reflect all my connected platforms, so that AI recommendations are holistic and accurate.

**Priority: P1 (Core Functionality)**

#### Acceptance Criteria

1. WHEN generating a brand profile, THE Content_Engine SHALL pull posts from all connected platforms
2. THE Content_Engine SHALL tag posts by platform so it can identify cross-platform patterns
3. THE Brand_Profile SHALL note platform-specific style variations (e.g., shorter/punchier on Twitter vs. narrative on LinkedIn)
4. THE Ittera_Platform SHALL compare engagement patterns across platforms in performance analysis
5. THE Ittera_Platform SHALL require at least 5 posts total (any platform combination) before triggering brand profile generation
6. WHILE the post count is below 5, THE Ittera_Platform SHALL show progress toward the threshold in the UI

---

### Requirement 4: Twitter Content Publishing Enhancement

**User Story:** As a content creator, I want Twitter publishing fully integrated into the content workflow, so that I can create, schedule, and publish tweets alongside my LinkedIn content.

**Priority: P1 (Core Functionality)**

#### Acceptance Criteria

1. WHEN creating content, THE Ittera_Platform SHALL allow users to select Twitter as the target platform
2. WHEN Twitter is selected as target, THE Content_Engine SHALL apply Twitter-specific constraints (character limit based on user's Subscription_Tier, thread format for longer content)
3. THE Ittera_Platform SHALL support publishing Twitter threads (multiple connected tweets)
4. THE Ittera_Platform SHALL store thread content as a single draft with thread markers
5. WHEN viewing the content calendar, THE Ittera_Platform SHALL display scheduled Twitter posts alongside LinkedIn posts
6. THE Ittera_Platform SHALL visually differentiate posts by platform in the calendar view
7. WHEN a Twitter token expires before publishing, THE Publisher_Service SHALL automatically attempt a token refresh
8. IF token refresh fails, THEN THE Ittera_Platform SHALL prompt the user to reconnect their Twitter account

---

### Requirement 5: Settings & Account Management

**User Story:** As a user, I want centralized management of all my connected platforms, so that I can monitor status, trigger syncs, and configure publishing preferences.

**Priority: P1 (Core Functionality)**

#### Acceptance Criteria

1. THE Ittera_Platform SHALL display all connected platforms with their status on the settings page
2. THE Ittera_Platform SHALL display per-platform: connected username, connection date, last sync time, posting readiness, and sync readiness
3. THE Ittera_Platform SHALL support disconnect and reconnect actions for all platforms
4. THE Ittera_Platform SHALL provide a "Sync Now" button per platform in settings
5. WHEN a sync is in progress, THE Ittera_Platform SHALL show a sync status indicator (last synced, in-progress, error state)
6. THE Ittera_Platform SHALL provide an auto-post toggle that applies per-platform
7. THE Ittera_Platform SHALL allow users to set preferred posting times per platform

---

### Requirement 6: Content Repurposing

**User Story:** As a content creator, I want to repurpose content across platforms while maintaining my voice, so that I can maximize reach without duplicating effort.

**Priority: P2 (Polish)**

#### Acceptance Criteria

1. WHEN repurposing LinkedIn content to Twitter, THE Content_Engine SHALL respect Twitter's character constraints based on the user's Subscription_Tier
2. THE Ittera_Platform SHALL allow repurposed drafts to be independently schedulable
3. WHEN repurposing content, THE Content_Engine SHALL maintain the creator's voice while adapting format
4. THE Content_Engine SHALL use the confirmed Brand_Profile for voice consistency during repurposing

---

### Requirement 7: Provider Architecture Extensibility

**User Story:** As a developer, I want social platform integrations to follow a consistent provider pattern, so that adding new platforms is straightforward and predictable.

**Priority: P2 (Polish)**

#### Acceptance Criteria

1. THE Ittera_Platform SHALL follow a consistent provider pattern for all social platform integrations
2. THE Ittera_Platform SHALL require only OAuth config, content sync service, and publishing adapter to add a new platform
3. THE Ittera_Platform SHALL serve all platforms from the existing `social_connections` table and `SocialConnection` model without schema changes
4. THE Content_Sync SHALL use a common interface: fetch posts, map to Post model, upsert
5. THE Publisher_Service SHALL use the existing dispatch pattern for all platforms
6. THE Iterra_Platform SHALL automatically include all platforms in calendar and analytics views

---

### Requirement 8: Platform-Aware Content Generation Limits

**User Story:** As a content creator, I want the AI content generator to respect platform-specific character limits based on my subscription tier, so that generated content is always publishable without manual truncation.

**Priority: P1 (Core Functionality)**

#### Acceptance Criteria

1. THE Content_Engine SHALL enforce a 3,000-character limit when generating content targeted at LinkedIn_Platform
2. WHEN generating content for a Twitter_Free_Tier user, THE Content_Engine SHALL enforce a 280-character limit per tweet
3. WHEN generating content for a Twitter_Premium_Tier user, THE Content_Engine SHALL enforce a 25,000-character limit per post
4. THE Ittera_Platform SHALL store the user's Twitter subscription tier in the Social_Connection metadata or user preferences
5. WHEN a Twitter_Free_Tier user's generated content exceeds 280 characters, THE Content_Engine SHALL offer to convert the content into a thread by splitting it into multiple segments each within the 280-character limit
6. WHEN splitting content into a thread, THE Content_Engine SHALL preserve sentence boundaries and logical flow across segments
7. WHILE generating content, THE Content_Engine SHALL validate output length against the applicable platform character limit before presenting the draft to the user
8. IF the user's Twitter Subscription_Tier is unknown, THEN THE Ittera_Platform SHALL default to Twitter_Free_Tier constraints (280 characters)
9. WHEN a user upgrades or changes their Twitter subscription tier, THE Ittera_Platform SHALL update the stored Subscription_Tier and apply the new limits to subsequent content generation

---

## Non-Functional Requirements

### NFR-1: Performance
- Content sync must complete within 30 seconds for up to 100 posts
- Calendar page must load within 2 seconds
- Publishing must respond within 10 seconds

### NFR-2: Reliability
- Failed syncs must not lose previously stored data
- Publishing failures must preserve the draft in "failed" status with error details
- Token refresh failures must not disconnect the account silently

### NFR-3: Security
- Access tokens must be stored encrypted at rest
- OAuth state parameters must be signed and time-limited (already implemented via JWT)
- PKCE must be used for all public OAuth clients (Twitter already uses this)

### NFR-4: Observability
- All sync operations must log: path used, posts fetched, errors encountered
- Publishing operations must log: platform, success/failure, error details
- Background tasks must report status via Celery result backend

---

## Out of Scope (This Phase)
- Instagram content publishing (OAuth connected but no publish flow)
- YouTube/TikTok integration
- Advanced analytics dashboards
- Real-time websocket notifications
- Mobile-responsive overhaul
- Multi-user workspace collaboration features
