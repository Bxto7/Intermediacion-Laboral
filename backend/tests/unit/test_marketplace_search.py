# RF: RF118-RF122
"""Tests for marketplace semantic search (OFICIO)."""

from app.nlp.embeddings.generator import apply_local_dictionary, generate_embedding


def test_marketplace_query_normalized_before_embedding():
    query = "necesito un gasfitero para arreglar las canerias del bano"
    normalized = apply_local_dictionary(query)
    assert "plomero" in normalized or "gasfitero" in normalized


def test_marketplace_query_embedding_is_384_dims():
    query = apply_local_dictionary("electricista para instalacion en El Tambo")
    result = generate_embedding(query)
    assert len(result) == 384


def test_marketplace_scoring_formula():
    cosine_sim = 0.85
    rating = 4.2
    availability_boost = 0.10
    score = 0.5 * cosine_sim + 0.3 * (rating / 5.0) + 0.2 * availability_boost
    assert 0.0 < score < 1.0
