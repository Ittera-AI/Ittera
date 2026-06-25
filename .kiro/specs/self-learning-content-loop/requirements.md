# Requirements Document

## Introduction

The Self-Learning Content Loop is the agentic feedback cycle that makes Iterra's generated
content measurably improve over time. The loop closes five broken links in the existing
platform so that the system can: publish content, pull its own analytics after posting,
decode why a post succeeded or failed, store those learnings in a compact summarized form,
and apply those learnings when generating the next post.

This feature adds a thin agent layer on top of the existing `iterra_ai` engines and Celery
orchestration. It depends on adjacent specs (`x-integration-hardening` and
`iterra-platform-stabilization-and-twitter`) for reliable publishing and raw-metric
retrieval and does not duplicate their OAuth, connect, or publish internals. These
requirements are derived from the approved design document and describe the externally
observable behavior of each loop stage so that the implementation and its property-based
tests can be traced back to a verifiable specification.

## Glossary

- **Loop_System**: The overall self-learning content loop comprising all agents below.
- **Publication_Bridge**: The agent that creates or links a `Post` when an Iterra-generated draft is published (`post_bridge_service`).
- **Loop_Orchestrator**: The Celery agent that sequences publish → metric-sync → auto-analysis → synthesis → fact-promotion with correct timing and idempotency (`learning_loop` tasks).
- **Metrics_Sync_Agent**: The platform-agnostic agent that pulls raw post metrics via a `MetricsProvider` for LinkedIn or X (`performance_sync`).
- **Per_Post_Why_Agent**: The reused `EngagementCoach` engine that scores and explains one post.
- **Insight_Synthesis_Engine**: The new `iterra_ai` engine that synthesizes many analyzed posts into a compact narrative, recommendations, and candidate facts.
- **Insight_Memory_Agent**: The agent that persists and versions the summarized insight per user and platform (`learning_insight_service`).
- **Fact_Promotion_Agent**: The agent that writes high-confidence learned facts into a new `UserContext` version (`fact_promotion_service`).
- **Context_Assembler**: The changed `context_service` that builds the 3-layer system prompt and injects learnings into Layer 3.
- **Weekly_Report_Agent**: The reimplemented `send_weekly_reports` Celery task that emails a learning digest.
- **LearnedInsight**: The summarized "why posts win or lose" memory row, one active version per `(user, platform)`.
- **Candidate_Fact**: A proposed learned fact with a `key`, `value`, `confidence` (0..1), and `evidence`.
- **Promotion_Confidence_Threshold**: The minimum confidence (0.7) required to promote a candidate fact into `UserContext`.
- **Post**: A persisted published item that the loop learns from.
- **ContentDraft**: A generated draft that may be published and bridged to a `Post`.
- **PostAnalysis**: The per-post AI WHY-analysis produced by the Per_Post_Why_Agent.
- **UserContext**: The append-only, versioned per-user context whose `platform_facts` feed prompt generation.
- **Engagement_Rate**: Interactions divided by a platform-correct denominator (impressions when reported, otherwise a follower/reach proxy).

## Requirements

### Requirement 1: Publication Bridge (draft to Post linking)

**User Story:** As a content creator, I want every draft I publish through Iterra to be linked to a learnable Post, so that the system has the data it needs to learn from my published content.

#### Acceptance Criteria

1. WHEN a ContentDraft is published through Iterra AND a non-empty platform_post_id (1 to 255 characters) is available, THE Publication_Bridge SHALL create exactly one Post for that draft, linked on the natural key (platform, platform_post_id) using a case-sensitive exact match.
2. WHEN a draft already has its post_id set, THE Publication_Bridge SHALL return the existing linked Post without creating an additional Post.
3. WHEN a Post with the same (platform, platform_post_id) already exists, THE Publication_Bridge SHALL link the draft to that existing Post and set the Post source to "iterra_published".
4. WHEN the Publication_Bridge creates or links a Post, THE Publication_Bridge SHALL set ContentDraft.post_id to the linked Post identifier before returning a success result.
5. IF a published draft has no platform_post_id or an empty platform_post_id, THEN THE Publication_Bridge SHALL skip Post creation, emit a "post_bridge_failed" event, and allow the publish to succeed without rolling back the publish.
6. WHEN the Publication_Bridge successfully creates a Post, THE Publication_Bridge SHALL enqueue the Loop_Orchestrator for that Post identifier within 5 seconds.
7. WHILE two publish operations for the same (platform, platform_post_id) occur simultaneously, THE Publication_Bridge SHALL ensure at most one Post exists for that natural key.
8. IF enqueuing the Loop_Orchestrator fails, THEN THE Publication_Bridge SHALL retry up to 3 times, emit a failure event if all retries fail, and retain the created Post and the draft-to-Post linkage.

### Requirement 2: Automatic per-post analysis orchestration

**User Story:** As a content creator, I want my published posts analyzed automatically after they accumulate engagement, so that I do not have to trigger analysis manually.

#### Acceptance Criteria

1. WHEN the Loop_Orchestrator executes a scheduled analysis pass for a published Post, THE Loop_Orchestrator SHALL invoke the Per_Post_Why_Agent exactly once per pass to produce a new PostAnalysis or refresh the existing one, without manual action.
2. IF a PostAnalysis whose age from its last-updated timestamp is strictly less than 30 days already exists for a Post, THEN THE Per_Post_Why_Agent SHALL reuse the existing analysis and perform zero additional LLM calls.
3. WHEN a Post is published, THE Loop_Orchestrator SHALL schedule delayed metric-pull and analysis passes at the configured fixed positive post-publish delays and SHALL NOT run any pass before the earliest configured window has elapsed.
4. WHEN the Loop_Orchestrator receives a duplicate publish notification for the same Post, THE Loop_Orchestrator SHALL reschedule the same windows while producing at most one fresh PostAnalysis under the 30-day rule.
5. WHEN per-post analysis completes successfully, THE Loop_Orchestrator SHALL record exactly one "auto_analysis_complete" event so that synthesis can detect new analyses.

### Requirement 3: Cross-post insight synthesis and memory

**User Story:** As a content creator, I want the system to summarize why my posts win or lose across many posts, so that the platform keeps a durable, improving memory of my content patterns.

#### Acceptance Criteria

1. WHEN the Insight_Memory_Agent synthesizes insights for a (user, platform) that has no existing LearnedInsight, THE Insight_Memory_Agent SHALL create the single LearnedInsight row for that (user, platform) with version 1.
2. WHILE fewer than 5 analyzed posts exist for a (user, platform), THE Insight_Memory_Agent SHALL skip synthesis and leave any prior LearnedInsight unchanged.
3. IF the Insight_Synthesis_Engine LLM call fails after 3 retry attempts or a 30-second timeout, THEN THE Insight_Synthesis_Engine SHALL produce a deterministic heuristic result AND THE Insight_Memory_Agent SHALL retain the prior LearnedInsight unchanged rather than overwriting it with empty content.
4. WHEN the Insight_Memory_Agent synthesizes insights for one platform, THE Insight_Memory_Agent SHALL leave every other platform's LearnedInsight unchanged.
5. WHILE no new analyses exist since the last LearnedInsight update for a (user, platform), THE Insight_Memory_Agent SHALL skip synthesis for that (user, platform).
6. THE Insight_Synthesis_Engine SHALL record each synthesis call through the cost tracker so that synthesis spend is logged like every other engine call.
7. WHEN the Insight_Memory_Agent synthesizes insights for a (user, platform) that already has a LearnedInsight, THE Insight_Memory_Agent SHALL update that row and increment its version by exactly one.
8. WHEN multiple publishes occur for the same (user, platform) within a 60-second window, THE Loop_Orchestrator SHALL debounce them into a single synthesis run.

### Requirement 4: Learning injection into generation context

**User Story:** As a content creator, I want past learnings applied when the next post is generated, so that my content improves automatically each cycle.

#### Acceptance Criteria

1. WHEN the Context_Assembler builds the system prompt AND exactly one active LearnedInsight exists for the (user, platform), THE Context_Assembler SHALL include that insight's summary text in the Layer 3 portion of the assembled system prompt.
2. WHEN an active LearnedInsight exists for the (user, platform), THE Context_Assembler SHALL include the recorded win patterns and recommendations in the Layer 3 portion of the system prompt.
3. WHEN the Context_Assembler reads the PostAnalysis records created within the most recent 30 days for the (user, platform), THE Context_Assembler SHALL aggregate the average hook score (rounded to two decimal places) and the single most frequently recurring improvement into the report context.
4. IF no active LearnedInsight exists for the (user, platform), THEN THE Context_Assembler SHALL produce the prior system prompt behavior without learning blocks.
5. IF an active LearnedInsight exists but contains no win patterns and no recommendations, THEN THE Context_Assembler SHALL include the available summary text and omit the empty win-pattern and recommendation blocks without raising an error.
6. IF no PostAnalysis records exist within the most recent 30 days for the (user, platform), THEN THE Context_Assembler SHALL omit the aggregated hook score and recurring improvement from the report context without raising an error.

### Requirement 5: Fact promotion into user context

**User Story:** As a content creator, I want high-confidence learnings turned into durable facts about my content, so that proven patterns persistently shape future generation.

#### Acceptance Criteria

1. WHEN the Fact_Promotion_Agent promotes candidate facts, THE Fact_Promotion_Agent SHALL write only facts whose confidence (on a 0.0 to 1.0 scale) is greater than or equal to the Promotion_Confidence_Threshold of 0.7.
2. WHEN at least one qualifying fact is promoted AND the merged platform_facts differ from the active UserContext platform_facts, THE Fact_Promotion_Agent SHALL create a new active UserContext version with change_source set to "fact_promotion" and version incremented by one.
3. WHEN merging qualifying facts into platform_facts, THE Fact_Promotion_Agent SHALL merge by fact key, replacing the value of any existing key and adding any new key.
4. IF no candidate fact meets the Promotion_Confidence_Threshold, THEN THE Fact_Promotion_Agent SHALL create no new UserContext version and leave the active UserContext unchanged.
5. IF the merged platform_facts equal the active UserContext platform_facts, THEN THE Fact_Promotion_Agent SHALL create no new UserContext version and leave the active UserContext unchanged.
6. WHEN a new UserContext version is created, THE Fact_Promotion_Agent SHALL atomically deactivate the previously active version so that exactly one version remains active.
7. IF persisting the new UserContext version fails, THEN THE Fact_Promotion_Agent SHALL roll back the change, leave the previously active version active, and indicate the error.

### Requirement 6: Weekly learning report

**User Story:** As a content creator, I want a weekly digest of what the system learned, so that I stay informed about my content performance trends.

#### Acceptance Criteria

1. WHEN the Weekly_Report_Agent runs for an active user (a user with at least one active platform), THE Weekly_Report_Agent SHALL read the active LearnedInsight for each platform and email a digest derived from it.
2. WHILE a user's LearnedInsight is stale (older than 7 days), THE Weekly_Report_Agent SHALL synthesize insights before composing the digest.
3. THE Weekly_Report_Agent SHALL derive the digest from the same active LearnedInsight version that the Context_Assembler injects so that the weekly email and the prompt-injected learnings remain consistent.
4. IF no LearnedInsight exists for any of a user's platforms, THEN THE Weekly_Report_Agent SHALL skip sending a digest for that user without raising an error.
5. IF sending the digest email fails, THEN THE Weekly_Report_Agent SHALL record the failure and continue processing the remaining users.

### Requirement 7: Platform-agnostic metrics synchronization

**User Story:** As a content creator who posts on multiple platforms, I want accurate engagement metrics pulled for each platform, so that learnings are based on correct performance data.

#### Acceptance Criteria

1. WHEN the Metrics_Sync_Agent computes Engagement_Rate, THE Metrics_Sync_Agent SHALL produce a finite numeric value greater than or equal to 0.0 for any combination of metric values and denominator, and SHALL NOT produce a NaN, infinite, or negative value.
2. IF no impressions value, no follower-count denominator, and no reach-proxy denominator are available for a Post, THEN THE Metrics_Sync_Agent SHALL report an Engagement_Rate of 0.0.
3. WHEN a platform does not report impressions for a Post, THE Metrics_Sync_Agent SHALL preserve the most recently stored impressions value for that Post rather than overwriting it with zero.
4. IF a platform does not report impressions for a Post and no previously stored impressions value exists for that Post, THEN THE Metrics_Sync_Agent SHALL leave the impressions value unset rather than writing a zero value.
5. WHEN fetching metrics for a Post, THE Metrics_Sync_Agent SHALL route the request to the MetricsProvider whose platform matches the Post platform.
6. IF no MetricsProvider matches the Post platform when fetching metrics, THEN THE Metrics_Sync_Agent SHALL skip metrics retrieval for that Post and record an error indicating the platform is unsupported, without modifying the Post's existing metric values.
7. WHEN a platform reports an impressions value greater than 0 for a Post, THE Metrics_Sync_Agent SHALL compute Engagement_Rate using that impressions value as the denominator.
8. WHEN a platform does not report an impressions value greater than 0 for a Post, THE Metrics_Sync_Agent SHALL compute Engagement_Rate using the follower-count denominator when it is available, and SHALL otherwise use the reach-proxy denominator.

### Requirement 8: Loop resilience and graceful degradation

**User Story:** As a platform operator, I want each loop stage to degrade independently, so that one failing stage never corrupts learned memory or blocks publishing.

#### Acceptance Criteria

1. IF any stage of the loop chain raises an error, THEN THE Loop_Orchestrator SHALL stop at the failing stage, commit the persisted results of every stage that completed before the failing stage, leave all prior LearnedInsight, PostAnalysis, and UserContext records unchanged, and record an event identifying the failing stage.
2. IF the Per_Post_Why_Agent LLM call fails, THEN THE Per_Post_Why_Agent SHALL return a PostAnalysis produced by its deterministic heuristic path and SHALL flag that result as heuristic so that callers can distinguish it from an LLM-produced analysis.
3. WHILE the learning loop is disabled by configuration, THE Loop_System SHALL not schedule or execute any beat-scheduled or event-driven learning-loop task.
4. WHEN a beat-scheduled cadence run executes, THE Loop_Orchestrator SHALL fan out synthesis for every active user and platform, processing each (user, platform) independently so that a failure for one (user, platform) does not prevent synthesis for any other (user, platform).
5. WHEN a cadence run executes after a prior stage failure, THE Loop_Orchestrator SHALL resume from the current database state and SHALL not reprocess stages whose results were already persisted.
6. IF a loop stage fails for one Post, THEN THE Loop_Orchestrator SHALL continue processing the other queued Posts and SHALL allow the originating publish operation to complete successfully.
