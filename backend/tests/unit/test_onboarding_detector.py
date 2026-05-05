# RF: RF016-RF022
"""Unit tests for onboarding worker-type detection logic."""

import pytest
from pydantic import ValidationError

from app.schemas.common import WorkerType
from app.schemas.onboarding import OnboardingAnswers
from app.services.onboarding.detector import detect_worker_type

# ── detect_worker_type ───────────────────────────────────────────────────────


def test_is_first_job_true_returns_primer_empleo() -> None:
    answers = OnboardingAnswers(is_first_job=True, is_trade_worker=False)
    result = detect_worker_type(answers)
    assert result == WorkerType.PRIMER_EMPLEO


def test_trade_worker_true_returns_oficio() -> None:
    from app.schemas.common import TradeCategory

    answers = OnboardingAnswers(
        is_first_job=False,
        is_trade_worker=True,
        trade_category=TradeCategory.ELECTRICIDAD,
    )
    result = detect_worker_type(answers)
    assert result == WorkerType.OFICIO


def test_neither_returns_experiencia() -> None:
    answers = OnboardingAnswers(is_first_job=False, is_trade_worker=False)
    result = detect_worker_type(answers)
    assert result == WorkerType.EXPERIENCIA


def test_first_job_overrides_trade_worker() -> None:
    """is_first_job=True always wins, even if is_trade_worker is True."""
    answers = OnboardingAnswers(is_first_job=True, is_trade_worker=True)
    result = detect_worker_type(answers)
    assert result == WorkerType.PRIMER_EMPLEO


def test_oficio_without_trade_category_raises_validation_error() -> None:
    """OnboardingAnswers raises Pydantic ValidationError when is_trade_worker=True
    and trade_category is None (but is_first_job=False)."""
    with pytest.raises(ValidationError):
        OnboardingAnswers(
            is_first_job=False,
            is_trade_worker=True,
            trade_category=None,
        )


def test_worker_type_values_are_lowercase_strings() -> None:
    assert WorkerType.PRIMER_EMPLEO.value == "primer_empleo"
    assert WorkerType.EXPERIENCIA.value == "experiencia"
    assert WorkerType.OFICIO.value == "oficio"
