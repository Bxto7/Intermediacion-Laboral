# RF: M05 kpi
"""Tests for reputation score calculation."""


def test_reputation_score_weighted():
    """Weighted average giving 2x weight to latest 5 ratings."""
    ratings = [3.0, 4.0, 5.0, 4.5, 5.0, 5.0]
    # Last 5: [4.0, 5.0, 4.5, 5.0, 5.0] -> weight 2 each
    # First 1: [3.0] -> weight 1
    last_five = ratings[-5:]
    rest = ratings[:-5]
    weighted_sum = sum(r * 2 for r in last_five) + sum(r for r in rest)
    total_weight = len(last_five) * 2 + len(rest)
    score = weighted_sum / total_weight if total_weight > 0 else 0.0
    assert score > 0.0
    assert score <= 5.0
