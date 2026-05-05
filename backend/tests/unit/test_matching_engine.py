# RF: RF076-RF090
"""Tests for ML matching engine differentiated by worker_type."""



def test_combined_score_primer_empleo():
    """PRIMER_EMPLEO: no reputation weight (gamma=0)."""
    cosine = 0.8
    ml_score = 0.7
    reputation = 4.5
    alpha, beta, gamma = 0.65, 0.35, 0.00
    score = alpha * cosine + beta * ml_score + gamma * (reputation / 5.0)
    assert abs(score - (0.65 * 0.8 + 0.35 * 0.7)) < 1e-6


def test_combined_score_experiencia():
    cosine = 0.8
    ml_score = 0.7
    reputation = 4.5
    alpha, beta, gamma = 0.50, 0.30, 0.20
    score = alpha * cosine + beta * ml_score + gamma * (reputation / 5.0)
    expected = 0.50 * 0.8 + 0.30 * 0.7 + 0.20 * (4.5 / 5.0)
    assert abs(score - expected) < 1e-6


def test_combined_score_oficio():
    cosine = 0.8
    ml_score = 0.7
    reputation = 4.5
    alpha, beta, gamma = 0.45, 0.25, 0.30
    score = alpha * cosine + beta * ml_score + gamma * (reputation / 5.0)
    expected = 0.45 * 0.8 + 0.25 * 0.7 + 0.30 * (4.5 / 5.0)
    assert abs(score - expected) < 1e-6
