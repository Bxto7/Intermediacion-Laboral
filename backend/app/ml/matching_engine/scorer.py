# RF: RF076-RF085 — combined_score formula (FIXED, per CLAUDE.md)
# Do NOT modify weights without validating F1 impact.

SCORE_WEIGHTS: dict[str, tuple[float, float, float]] = {
    "primer_empleo": (0.65, 0.35, 0.00),  # (cosine, ml, reputation)
    "experiencia": (0.50, 0.30, 0.20),
    "oficio": (0.45, 0.25, 0.30),
}


def combined_score(
    cosine_sim: float,
    ml_score: float,
    reputation: float,
    worker_type: str,
) -> float:
    """Fixed combined_score formula from CLAUDE.md.

    Args:
        cosine_sim: Cosine similarity from pgvector search (0-1).
        ml_score: Supervised model score (0-1).
        reputation: Worker avg_rating (0-5 scale, normalised internally).
        worker_type: One of primer_empleo | experiencia | oficio.

    Returns:
        Combined score in [0, 1].
    """
    alpha, beta, gamma = SCORE_WEIGHTS[worker_type]
    return alpha * cosine_sim + beta * ml_score + gamma * (reputation / 5.0)
