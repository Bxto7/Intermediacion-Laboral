# RF: RF086-RF095 — Feature engineering for the supervised matching model
from dataclasses import dataclass

import numpy as np

FEATURE_NAMES = [
    "cosine_sim",
    "skill_overlap",
    "district_match",
    "experience_gap",
    "salary_fit",
    "reputation",
    "recency_boost",
    "portfolio_size",
    "worker_type_encoded",
]

WORKER_TYPE_ENCODING: dict[str, float] = {
    "primer_empleo": 0.0,
    "experiencia": 0.5,
    "oficio": 1.0,
}

_JUNIN_DISTRICTS = {"Huancayo", "El Tambo", "Chilca"}


@dataclass
class MatchFeatureVector:
    cosine_sim: float
    skill_overlap: float
    district_match: float
    experience_gap: float
    salary_fit: float
    reputation: float
    recency_boost: float
    portfolio_size: float
    worker_type_encoded: float


def _get_attr(obj: object, attr: str, default=None):
    """Safely get attribute from ORM row or Row mapping."""
    val = getattr(obj, attr, None)
    if val is None and hasattr(obj, "_mapping"):
        val = obj._mapping.get(attr)  # type: ignore[attr-defined]
    return val if val is not None else default


def build_feature_vector(
    worker: object,
    offer: object,
    cosine_sim: float,
    skill_overlap: float,
) -> np.ndarray:
    """Build the 9-element feature vector for the supervised classifier.

    This function is intentionally side-effect free so it can be called in
    parallel across candidates without requiring an async context.
    """
    worker_type = getattr(worker, "worker_type", "experiencia")

    # ── district_match ────────────────────────────────────────────────────────
    offer_district = _get_attr(offer, "district", "")
    worker_district = getattr(worker, "district", "") or ""
    if worker_district and worker_district == offer_district:
        district_match = 1.0
    elif offer_district in _JUNIN_DISTRICTS:
        district_match = 0.5
    else:
        district_match = 0.0

    # ── experience_gap ────────────────────────────────────────────────────────
    years_req = float(_get_attr(offer, "years_required", 0) or 0)
    years_exp = float(getattr(worker, "years_experience", 0) or 0)
    experience_gap = min(abs(years_req - years_exp) / 10.0, 1.0)

    # ── salary_fit ────────────────────────────────────────────────────────────
    expected_salary = getattr(worker, "expected_salary", None)
    salary_min = _get_attr(offer, "salary_min", None)
    salary_max = _get_attr(offer, "salary_max", None)
    if expected_salary and salary_min and salary_max:
        expected_f = float(expected_salary)
        smin_f = float(salary_min)
        smax_f = float(salary_max)
        if smin_f <= expected_f <= smax_f:
            salary_fit = 1.0
        elif expected_f < smin_f:
            salary_fit = max(0.0, 1.0 - (smin_f - expected_f) / smin_f)
        else:
            salary_fit = 0.5
    else:
        salary_fit = 0.0

    # ── reputation (0 for primer_empleo per CLAUDE.md) ────────────────────────
    avg_rating = float(getattr(worker, "avg_rating", 0) or 0)
    reputation = 0.0 if worker_type == "primer_empleo" else (avg_rating / 5.0)

    # ── portfolio_size (only for oficio) ─────────────────────────────────────
    portfolio_size = 0.0
    if worker_type == "oficio":
        portfolio_count = float(getattr(worker, "portfolio_count", 0) or 0)
        portfolio_size = min(portfolio_count / 20.0, 1.0)

    return np.array(
        [
            cosine_sim,
            skill_overlap,
            district_match,
            experience_gap,
            salary_fit,
            reputation,
            0.0,  # recency_boost — computed externally if needed
            portfolio_size,
            WORKER_TYPE_ENCODING.get(worker_type, 0.5),
        ],
        dtype=np.float32,
    )
