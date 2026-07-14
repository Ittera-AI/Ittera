"""
Property-based test for ``compute_engagement_rate`` in
``workers.celery.tasks.performance_sync`` (spec task 3.3).

**Property 8: Engagement rate is well-defined on any denominator**
**Validates: Requirements 7.1, 7.5**

Requirement 7.1 demands that the engagement rate is a finite number >= 0.0 for
ANY combination of metric values and denominator — never NaN, never +/-inf, and
never negative. Requirement 7.5 (denominator selection) implies that when no
positive denominator exists (neither a positive impressions value nor a positive
follower/reach proxy), the engagement rate is exactly 0.0.

This test generates arbitrary likes/comments/shares (including negative and very
large), arbitrary impressions (None / 0 / negative / positive / huge), and
arbitrary followers (None / 0 / negative / positive / huge), and asserts the
invariants hold for every generated case.
"""

import math
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from workers.celery.tasks.performance_sync import (  # noqa: E402
    PostMetrics,
    compute_engagement_rate,
)

# Integer metric values: span negative, zero, small, and very large magnitudes.
_METRIC_INTS = st.integers(min_value=-(10**18), max_value=10**18)

# Denominators (impressions / followers): None plus the full int range above.
_DENOMINATORS = st.one_of(st.none(), _METRIC_INTS)


@settings(max_examples=300)
@given(
    likes=_METRIC_INTS,
    comments=_METRIC_INTS,
    shares=_METRIC_INTS,
    impressions=_DENOMINATORS,
    followers=_DENOMINATORS,
)
def test_engagement_rate_is_well_defined_on_any_denominator(
    likes, comments, shares, impressions, followers
):
    """Property 8: the result is always a finite, non-negative float, and is
    exactly 0.0 when no positive denominator exists."""
    metrics = PostMetrics(
        likes=likes, comments=comments, shares=shares, impressions=impressions
    )

    rate = compute_engagement_rate(metrics, followers)

    # The result is a real float.
    assert isinstance(rate, float)

    # Never NaN, never +/-inf.
    assert not math.isnan(rate)
    assert not math.isinf(rate)
    assert math.isfinite(rate)

    # Never negative, and never greater than 1.0 (a rate is a fraction of its
    # denominator; interactions exceeding the denominator clamp to 1.0).
    assert rate >= 0.0
    assert rate <= 1.0

    # When there is no positive denominator (neither a positive impressions value
    # nor a positive follower/reach proxy), the rate must be exactly 0.0.
    has_positive_impressions = impressions is not None and impressions > 0
    has_positive_followers = followers is not None and followers > 0
    if not has_positive_impressions and not has_positive_followers:
        assert rate == 0.0
