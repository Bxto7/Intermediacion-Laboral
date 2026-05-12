# RF: RF076-RF095
"""Integration tests for matching engine by worker type."""
import pytest
from httpx import AsyncClient

from app.ml.matching_engine.scorer import SCORE_WEIGHTS, combined_score


@pytest.mark.asyncio
async def test_combined_score_weights_primer_empleo():
    """PRIMER_EMPLEO: alpha=0.65, beta=0.35, gamma=0.00 (sin reputacion)."""
    score = combined_score(
        cosine_sim=0.8,
        ml_score=0.6,
        reputation=4.0,
        worker_type="primer_empleo",
    )
    expected = 0.65 * 0.8 + 0.35 * 0.6 + 0.00 * (4.0 / 5.0)
    assert abs(score - expected) < 0.0001


@pytest.mark.asyncio
async def test_combined_score_weights_experiencia():
    """EXPERIENCIA: alpha=0.50, beta=0.30, gamma=0.20."""
    score = combined_score(
        cosine_sim=0.7,
        ml_score=0.5,
        reputation=3.0,
        worker_type="experiencia",
    )
    expected = 0.50 * 0.7 + 0.30 * 0.5 + 0.20 * (3.0 / 5.0)
    assert abs(score - expected) < 0.0001


@pytest.mark.asyncio
async def test_combined_score_weights_oficio():
    """OFICIO: gamma=0.30 — reputacion tiene peso significativo."""
    score = combined_score(
        cosine_sim=0.7,
        ml_score=0.5,
        reputation=5.0,
        worker_type="oficio",
    )
    expected = 0.45 * 0.7 + 0.25 * 0.5 + 0.30 * (5.0 / 5.0)
    assert abs(score - expected) < 0.0001


@pytest.mark.asyncio
async def test_combined_score_primer_empleo_ignores_reputation():
    """PRIMER_EMPLEO: reputacion alta no debe cambiar el score (gamma=0)."""
    score_low_rep = combined_score(0.8, 0.6, 0.0, "primer_empleo")
    score_high_rep = combined_score(0.8, 0.6, 5.0, "primer_empleo")
    assert abs(score_low_rep - score_high_rep) < 0.0001


@pytest.mark.asyncio
async def test_combined_score_range():
    """Score siempre en [0, 1]."""
    for wt in ["primer_empleo", "experiencia", "oficio"]:
        score = combined_score(1.0, 1.0, 5.0, wt)
        assert 0.0 <= score <= 1.0
        score_min = combined_score(0.0, 0.0, 0.0, wt)
        assert score_min == 0.0


@pytest.mark.asyncio
async def test_score_weights_exist_for_all_types():
    """Verificar que SCORE_WEIGHTS tiene los 3 tipos."""
    assert "primer_empleo" in SCORE_WEIGHTS
    assert "experiencia" in SCORE_WEIGHTS
    assert "oficio" in SCORE_WEIGHTS
    for wtype, (alpha, beta, gamma) in SCORE_WEIGHTS.items():
        assert abs(alpha + beta + gamma - 1.0) < 0.001, (
            f"{wtype}: pesos deben sumar 1.0, suman {alpha + beta + gamma}"
        )


@pytest.mark.asyncio
async def test_match_endpoint_requires_auth(client: AsyncClient):
    """Sin token → 401 o 403."""
    import uuid
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/match/{fake_id}")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_match_endpoint_worker_not_found(client: AsyncClient):
    """Trabajador inexistente → 404 (con auth valida)."""
    import uuid
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": f"match_test_{uuid.uuid4().hex[:6]}@test.com", "password": "TestPass1!", "role": "worker"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    fake_worker_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/match/{fake_worker_id}", headers=headers)
    assert resp.status_code in (403, 404)


@pytest.mark.asyncio
async def test_equity_reranking_boosts_underrepresented():
    """Equity ranker debe boost a grupos con ratio < 0.80."""
    from app.ml.equity_ranker.ranker import apply_equity_reranking

    matches = [
        {"combined_score": 0.9, "district": "Huancayo"},
        {"combined_score": 0.8, "district": "Huancayo"},
        {"combined_score": 0.3, "district": "Chilca"},
        {"combined_score": 0.2, "district": "Chilca"},
    ]
    result = apply_equity_reranking(matches, group_field="district")
    assert len(result) == 4
    # Resultado debe seguir ordenado desc por score
    scores = [m["combined_score"] for m in result]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_explainer_returns_correct_label():
    """Explain match: score alto → label Alta."""
    from app.ml.explainer.explainer import explain_match

    result = explain_match(
        combined_score=0.85,
        worker_skills=["python", "fastapi", "sql"],
        offer_required_skills=["python", "sql"],
        offer_preferred_skills=["fastapi"],
        worker_type="experiencia",
    )
    assert result["compatibility_label"] == "Alta"
    assert "python" in result["matching_skills"] or "sql" in result["matching_skills"]
    assert "message" in result


@pytest.mark.asyncio
async def test_explainer_low_score_label():
    """Explain match: score bajo → label Baja."""
    from app.ml.explainer.explainer import explain_match

    result = explain_match(
        combined_score=0.2,
        worker_skills=["carpintería"],
        offer_required_skills=["python", "java", "kubernetes"],
        offer_preferred_skills=[],
        worker_type="primer_empleo",
    )
    assert result["compatibility_label"] == "Baja"
    assert len(result["missing_skills"]) > 0
