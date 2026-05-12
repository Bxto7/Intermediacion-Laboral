# RF: RF151-RF155 (M10) — re-ranking equitativo por genero/zona
import structlog

logger = structlog.get_logger()

EQUITY_THRESHOLD = 0.80


def compute_disparate_impact(
    scores_group_a: list[float],
    scores_group_b: list[float],
) -> float:
    """
    Calcula disparate impact ratio entre dos grupos.
    Ratio < 0.80 activa re-ranking automatico.
    """
    if not scores_group_a or not scores_group_b:
        return 1.0

    mean_a = sum(scores_group_a) / len(scores_group_a)
    mean_b = sum(scores_group_b) / len(scores_group_b)

    if mean_b == 0:
        return 1.0

    return mean_a / mean_b


def apply_equity_reranking(
    matches: list[dict],
    group_field: str = "district",
    weight_boost: float = 0.05,
) -> list[dict]:
    """
    Aplica re-ranking equitativo cuando disparate impact < 0.80.
    Boost a grupos sub-representados en el top-K.
    """
    if not matches:
        return matches

    groups: dict[str, list[float]] = {}
    for match in matches:
        group = match.get(group_field, "unknown")
        score = match.get("combined_score", 0.0)
        groups.setdefault(group, []).append(score)

    group_names = list(groups.keys())
    if len(group_names) < 2:
        return matches

    all_scores = [s for scores in groups.values() for s in scores]
    if not all_scores:
        return matches

    global_mean = sum(all_scores) / len(all_scores)
    boosted = []
    for match in matches:
        group = match.get(group_field, "unknown")
        group_mean = sum(groups[group]) / len(groups[group]) if groups[group] else 0.0
        ratio = group_mean / global_mean if global_mean > 0 else 1.0

        new_score = match["combined_score"]
        if ratio < EQUITY_THRESHOLD:
            new_score = min(1.0, new_score + weight_boost)

        boosted.append({**match, "combined_score": new_score, "equity_adjusted": ratio < EQUITY_THRESHOLD})

    boosted.sort(key=lambda m: m["combined_score"], reverse=True)

    logger.info(
        "equity_reranking_applied",
        total_matches=len(boosted),
        groups=list(groups.keys()),
    )
    return boosted


def log_equity_audit(
    worker_id: str,
    worker_type: str,
    disparate_impact: float,
    reranking_applied: bool,
) -> None:
    logger.info(
        "equity_audit",
        worker_id=worker_id,
        worker_type=worker_type,
        disparate_impact=disparate_impact,
        reranking_applied=reranking_applied,
        threshold=EQUITY_THRESHOLD,
    )
