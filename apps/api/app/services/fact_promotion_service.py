"""
Fact Promotion Agent (Gap 5).

Executes the long-dormant ``fact_promotion`` path: turns high-confidence learned
facts (proposed by the Insight Synthesis Agent) into a durable, prompt-visible
``UserContext`` version. Because ``UserContext`` is append-only and versioned, a
promotion never mutates an existing row — it inserts a NEW active version and
atomically deactivates the prior one, so exactly one version stays active.

Design reference: design.md section B.3.3.

Key guarantees:
  - Only facts with ``confidence >= PROMOTION_CONFIDENCE_THRESHOLD`` (0.7) are
    written (Requirement 5.1).
  - Facts merge by key into per-platform ``platform_facts``: an existing key's
    value is replaced and a new key is added (Requirement 5.3).
  - A new active version (``change_source="fact_promotion"``, ``version + 1``) is
    created only when the merged facts actually differ from the active version
    (Requirements 5.2, 5.5).
  - The previously active version is atomically deactivated so exactly one version
    remains active (Requirement 5.6).
  - No-op when nothing qualifies or nothing changed (Requirements 5.4, 5.5).
  - Rolls back and re-raises on any persistence failure, leaving the previously
    active version active (Requirement 5.7).
"""

import copy
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.datetime_helpers import utc_now
from app.models.user import User
from app.models.user_context import UserContext
from app.services import context_service

logger = logging.getLogger(__name__)

# Minimum confidence (0..1) required to promote a candidate fact into UserContext.
PROMOTION_CONFIDENCE_THRESHOLD = 0.7


def promote_facts(
    db: Session,
    user: User,
    platform: str,
    candidate_facts: list[Any],
) -> UserContext | None:
    """
    Promote high-confidence candidate facts into a new active ``UserContext``
    version for ``user``.

    ``candidate_facts`` items may be plain dicts (as stored on
    ``LearnedInsight.candidate_facts``) or ``CandidateFact`` pydantic models; both
    shapes expose ``key``, ``value``, and ``confidence``.

    Returns the newly created ``UserContext`` version, or ``None`` when no fact
    qualifies or the merged facts are unchanged.
    """
    promotable = [
        f for f in (candidate_facts or []) if _confidence(f) >= PROMOTION_CONFIDENCE_THRESHOLD
    ]
    if not promotable:
        # Nothing meets the threshold — leave the active context untouched (5.4).
        return None

    active = context_service.get_active_user_context(db, user)
    existing_facts = active.platform_facts if active and active.platform_facts else {}
    new_facts = _merge_platform_facts(existing_facts, platform, promotable)

    # Idempotency: if merging changed nothing, do not create a new version (5.5).
    if active and new_facts == (active.platform_facts or {}):
        return None

    try:
        # Append-only: deactivate the prior version and insert a new active one so
        # exactly one version remains active (5.6). The flush+commit are atomic —
        # a failure rolls both changes back together (5.7).
        if active:
            active.is_active = False

        new_ctx = UserContext(
            user_id=user.id,
            brand_name=active.brand_name if active else None,
            bio=active.bio if active else None,
            target_audience=active.target_audience if active else None,
            content_mission=active.content_mission if active else None,
            platform_facts=new_facts,
            version=(active.version + 1) if active else 1,
            change_source="fact_promotion",
            change_summary=_describe(promotable, platform),
            is_active=True,
        )
        db.add(new_ctx)
        db.commit()
        db.refresh(new_ctx)
    except Exception:
        # Persistence failed — restore the prior active version and surface the
        # error to the caller (5.7).
        db.rollback()
        logger.exception(
            "fact_promotion failed for user=%s platform=%s; rolled back", user.id, platform
        )
        raise

    _emit_event(
        db,
        user.id,
        "fact_promoted",
        metrics={"platform": platform, "facts": [_key(f) for f in promotable]},
    )
    return new_ctx


def _merge_platform_facts(
    existing_facts: dict,
    platform: str,
    promotable: list[Any],
) -> dict:
    """
    Merge promotable facts into a copy of ``existing_facts`` under ``platform``.

    Merges by fact key: an existing key's value is replaced and a new key is added
    (Requirement 5.3). ``confirmed_at`` is only refreshed when at least one value
    actually changes, so re-promoting identical facts is a true no-op and keeps
    the idempotency guarantee (Requirement 5.5).
    """
    merged = copy.deepcopy(existing_facts) if existing_facts else {}
    platform_dict = dict(merged.get(platform, {}) or {})

    changed = False
    for fact in promotable:
        key = _key(fact)
        value = _value(fact)
        if platform_dict.get(key) != value:
            platform_dict[key] = value
            changed = True

    if changed:
        platform_dict["confirmed_at"] = utc_now().isoformat()

    merged[platform] = platform_dict
    return merged


def _describe(promotable: list[Any], platform: str) -> str:
    """Human-readable change summary for the new UserContext version."""
    keys = ", ".join(_key(f) for f in promotable)
    return f"Promoted {len(promotable)} learned fact(s) for {platform}: {keys}"


def _emit_event(
    db: Session,
    user_id: str,
    event_type: str,
    metrics: dict | None = None,
) -> None:
    """
    Record an ``AnalyticsEvent`` for promotion audit/idempotency.

    Imported locally to mirror ``analytics_service`` / ``post_bridge_service`` and
    avoid import cycles.
    """
    from app.models.analytics_snapshot import AnalyticsEvent

    event = AnalyticsEvent(
        user_id=user_id,
        event_type=event_type,
        metrics=metrics or {},
    )
    db.add(event)
    db.commit()


# ── Field accessors (support both dict and CandidateFact shapes) ──────────────


def _confidence(fact: Any) -> float:
    raw = fact.get("confidence", 0) if isinstance(fact, dict) else getattr(fact, "confidence", 0)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def _key(fact: Any) -> str:
    return fact.get("key", "") if isinstance(fact, dict) else getattr(fact, "key", "")


def _value(fact: Any) -> list:
    value = fact.get("value", []) if isinstance(fact, dict) else getattr(fact, "value", [])
    return list(value) if value is not None else []
