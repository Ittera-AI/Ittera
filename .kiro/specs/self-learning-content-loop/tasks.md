# Implementation Plan: Self-Learning Content Loop

## Overview

This plan implements the self-learning content loop as a thin agent layer over the existing
`iterra_ai` engines and Celery orchestration. Work proceeds contracts-first: data models and
the Alembic migration, the new `InsightSynthesisEngine`, and the platform-agnostic metrics
math come first, followed by the service agents (bridge, insight memory, fact promotion,
context injection), then the Celery orchestrator that wires the asynchronous loop together,
and finally the beat-scheduled cadence and weekly report. Each step builds on the previous one
and ends by integrating into the live publish/generate flow so no code is left orphaned.

Language: Python (matching the existing `apps/api` and `packages/ai-engine` stack). Property
tests use `hypothesis`; unit/engine tests use `pytest`.

## Tasks

- [x] 1. Data models and migration
  - [x] 1.1 Add the `LearnedInsight` model and User relationship
    - Create `apps/api/app/models/learned_insight.py` with the `LearnedInsight` model per design B.1.1 (String UUID PK, `user_id`, `platform`, `summary`, `why_wins`/`why_losses`/`recommendations`/`candidate_facts` JSON, `confidence`, `based_on_posts`, `based_on_analyses`, `period_days`, `model`, `is_mock`, `version`, timestamps, and the `uq_learned_insight_user_platform` unique constraint)
    - Add `learned_insights = relationship("LearnedInsight", back_populates="user", cascade="all, delete-orphan")` to `app/models/user.py`
    - _Requirements: 3.1, 3.7_

  - [x] 1.2 Add draft↔post link and Post provenance columns
    - Add nullable `post_id` FK (`ondelete="SET NULL"`) plus `post` relationship to `app/models/content_draft.py` per B.1.2
    - Add `source` column (default `"imported"`, indexed) to `app/models/post.py` per B.1.3
    - _Requirements: 1.1, 1.4_

  - [x] 1.3 Create the Alembic migration with upgrade and downgrade
    - Write one revision per B.1.4 that creates `learned_insights` (with indexes + unique constraint), adds `content_drafts.post_id` (FK + index), and adds `posts.source` (+ index)
    - Implement a symmetric `downgrade()` that drops the columns, constraints, indexes, and table in reverse order
    - _Requirements: 1.1, 1.4, 3.1_

- [x] 2. Insight Synthesis Engine (iterra_ai)
  - [x] 2.1 Define synthesis schemas
    - Create `packages/ai-engine/iterra_ai/insight/schemas.py` with `PostPerformanceRecord`, `InsightSynthesisInput`, `CandidateFact` (confidence constrained 0.0–1.0), and `InsightSynthesisOutput` per B.2.1
    - _Requirements: 3.1, 5.1_

  - [x] 2.2 Add the versioned synthesis prompt
    - Create `packages/ai-engine/iterra_ai/prompts/insight.py` with `INSIGHT_SYNTHESIS_SYSTEM_V1`, `INSIGHT_SYNTHESIS_USER_V1`, and `format_insight_prompt(input) -> tuple[str, str]` following the `coach.py` convention
    - _Requirements: 3.1_

  - [x] 2.3 Implement `InsightSynthesisEngine`
    - Create `packages/ai-engine/iterra_ai/insight/engine.py` extending `BaseEngine[InsightSynthesisInput, InsightSynthesisOutput]` with cost-tracked `_call_llm`, coach-style JSON parsing, and a deterministic `_heuristic_synthesize` fallback reusing the `analytics_service.get_content_insights` pattern math
    - Register the engine in `iterra_ai/__init__.py` exports
    - _Requirements: 3.3, 3.6_

  - [x]* 2.4 Write unit tests for `InsightSynthesisEngine`
    - Mock the client to assert JSON parsing of a well-formed response and the heuristic fallback path when no API key/client is present, mirroring `tests/test_coach.py`
    - _Requirements: 3.3, 3.6_

- [x] 3. Platform-agnostic metrics sync
  - [x] 3.1 Implement `PostMetrics`, `MetricsProvider`, providers, and engagement-rate math
    - In `workers/celery/tasks/performance_sync.py` add `PostMetrics`, the `MetricsProvider` protocol, `LinkedInMetricsProvider`, `TwitterMetricsProvider`, the `PROVIDERS` registry, and `compute_engagement_rate` per B.4 (impressions denominator when reported, else follower/reach proxy, else 0.0; never NaN/inf/negative)
    - Ensure `_sync_single_post` writes `impressions` only when the provider returns a non-`None` value and preserves the prior value otherwise
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8_

  - [x] 3.2 Route per-post sync through the matching provider and handle unsupported platforms
    - Update `sync_single_post` / `_sync_single_post` to select the provider by `post.platform`; if no provider matches, skip retrieval, record an unsupported-platform error, and leave existing metrics unchanged
    - _Requirements: 7.5, 7.6_

  - [x]* 3.3 Write property test for engagement rate
    - **Property 8: Engagement rate is well-defined on any denominator**
    - **Validates: Requirements 7.1, 7.5**

- [x] 4. Checkpoint - data layer and core math
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Publication Bridge Agent
  - [x] 5.1 Implement `post_bridge_service.bridge_draft_to_post`
    - Create `apps/api/app/services/post_bridge_service.py` per B.3.1: create or link a `Post` on the natural key `(platform, platform_post_id)`, reuse when `draft.post_id` is set, set `source="iterra_published"` on link, set `draft.post_id`, emit `post_bridge_failed` when no `platform_post_id`, and keep publish succeeding regardless
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.7_

  - [x]* 5.2 Write property tests for the bridge
    - **Property 1: Bridge creates exactly one Post per published draft (idempotent)**
    - **Property 2: A published draft is always linked to a learnable Post**
    - **Validates: Requirements 1.1, 1.2, 1.4**

- [x] 6. Insight Memory Agent
  - [x] 6.1 Implement `learning_insight_service`
    - Create `apps/api/app/services/learning_insight_service.py` with `get_active_insight`, `synthesize_user_insights` (build records from joined Post+PostAnalysis, skip when fewer than `MIN_POSTS_FOR_SYNTHESIS`, run the engine, `_upsert_insight` version-bumps and stores `model`/`is_mock`, retains prior insight on heuristic/empty output, emits `insight_synthesized`), and the `_has_new_analyses_since_last_synthesis` guard
    - Per-platform isolation: only the synthesized `(user, platform)` row is touched
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.7_

  - [x]* 6.2 Write property tests for synthesis
    - **Property 4: Synthesis is monotonic and non-destructive**
    - **Property 7: Platform isolation**
    - **Validates: Requirements 3.1, 3.3, 3.4**

- [x] 7. Fact Promotion Agent
  - [x] 7.1 Implement `fact_promotion_service.promote_facts`
    - Create `apps/api/app/services/fact_promotion_service.py` per B.3.3: promote only facts with `confidence >= 0.7`, merge by fact key into `platform_facts`, create a new active `UserContext` version (`change_source="fact_promotion"`, version+1) only when merged facts differ, atomically deactivate the prior active version, no-op when nothing qualifies or nothing changed, and roll back on persistence failure
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [x]* 7.2 Write property test for fact promotion
    - **Property 5: Only confident facts are promoted, versioned + append-only**
    - **Validates: Requirements 5.1, 5.2, 5.5**

- [x] 8. Context injection and auto-analysis event
  - [x] 8.1 Inject learnings into the assembled prompt
    - Add optional `learned_summary`, `why_wins`, `recommendations`, `avg_hook_score`, `recurring_improvement` fields (empty defaults) to `ReportContext` in `app/schemas/context.py`
    - Update `app/services/context_service.py` `_get_report_context` to read the active `LearnedInsight` and aggregate recent `PostAnalysis` (avg hook score rounded to 2 decimals, most common improvement), and update `_build_system_prompt` to emit the "What We've Learned" Layer 3 block, omitting empty win/recommendation blocks and degrading to prior behavior when no insight or analyses exist
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x]* 8.2 Write property test for learning injection
    - **Property 6: Learnings reach the next prompt**
    - **Validates: Requirements 4.1, 4.2**

  - [x] 8.3 Emit `auto_analysis_complete` from `analyze_post`
    - In `app/services/analytics_service.py`, keep the existing fresh-analysis (<30d) short-circuit and emit exactly one `auto_analysis_complete` `AnalyticsEvent` when analysis completes so synthesis can detect new analyses
    - _Requirements: 2.1, 2.2, 2.5_

  - [x]* 8.4 Write property test for analysis idempotency
    - **Property 3: Auto-analysis never double-charges**
    - **Validates: Requirements 2.2**

- [x] 9. Checkpoint - agents implemented
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Loop Orchestrator and publish wiring
  - [x] 10.1 Implement the orchestrator Celery tasks
    - Create `workers/celery/tasks/learning_loop.py` per B.5 with `on_post_published` (schedules delayed pulls at the configured positive delays, idempotent), `pull_and_analyze_post` (sync metrics → auto-analyze → debounced synthesis with 60s countdown, max_retries=3), `synthesize_user_insights` (guarded by `_has_new_analyses_since_last_synthesis`, runs memory + fact promotion), and `run_insight_cycle_all_users` (fan out per active user+platform, isolating per-(user,platform) failures); stop-at-failing-stage semantics with committed prior stages
    - _Requirements: 2.1, 2.3, 2.4, 3.8, 8.1, 8.4, 8.5, 8.6_

  - [x] 10.2 Register the orchestrator and gate it by config
    - Add `workers/celery/tasks/learning_loop` to the Celery app `include` in `workers/celery/app.py` and gate scheduling/execution behind `ENABLE_LEARNING_LOOP`
    - _Requirements: 8.3_

  - [x] 10.3 Wire the bridge and orchestrator into both publish paths
    - In `content_service.publish_now()` and `workers/celery/tasks/publisher.process_publishing_queue`, after a successful publish call `bridge_draft_to_post(...)` then `learning_loop.on_post_published.delay(post.id)`, retrying the enqueue up to 3 times and retaining the Post/linkage on failure
    - _Requirements: 1.6, 1.8_

- [x] 11. Beat cadence and weekly report
  - [x] 11.1 Add the beat schedule entry
    - Add the `insight-cycle-daily` entry to `workers/celery/beat_schedule.py`, gated by `ENABLE_LEARNING_LOOP`, per B.5
    - _Requirements: 8.3, 8.4_

  - [x] 11.2 Reimplement `send_weekly_reports` on the Insight Memory Agent
    - Replace the TODO stub in `workers/celery/tasks/weekly_reports.py` to read the active `LearnedInsight` per platform for each active user (synthesizing first if stale >7 days), email a digest via `app/services/email.py`, skip users with no insight, and continue past per-user email failures
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 12. End-to-end integration
  - [x]* 12.1 Write the full-loop integration test
    - Drive publish → bridge → `sync_single_post` (stubbed provider) → `analyze_post` (stubbed coach) → synthesis → promotion → re-assemble, asserting the learned summary appears in the regenerated system prompt and that a failing stage leaves prior memory intact
    - _Requirements: 8.1, 8.5, 8.6_

- [x] 13. Final checkpoint - full loop closure
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Each task references specific granular requirements for traceability.
- Property tests (`hypothesis`) encode the design's Correctness Properties P1–P8; each is its own sub-task placed next to the code it validates so errors surface early.
- Checkpoints provide incremental validation at the data layer, agent layer, and full-loop boundaries.
- This spec consumes the publish/raw-metric capabilities owned by the `x-integration-hardening` and `iterra-platform-stabilization-and-twitter` specs and does not modify their OAuth/connect/publish internals.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1", "2.2", "3.1", "8.3"] },
    { "id": 1, "tasks": ["1.3", "2.3", "3.2", "3.3", "5.1", "7.1", "8.4"] },
    { "id": 2, "tasks": ["2.4", "5.2", "6.1", "7.2"] },
    { "id": 3, "tasks": ["6.2", "8.1"] },
    { "id": 4, "tasks": ["8.2", "10.1"] },
    { "id": 5, "tasks": ["10.2", "10.3", "11.1", "11.2"] },
    { "id": 6, "tasks": ["12.1"] }
  ]
}
```
