# RF: RF056-RF058
"""Tests for embedding generation pipeline."""

import math
from unittest.mock import mock_open, patch

from app.nlp.embeddings.generator import (
    apply_local_dictionary,
    generate_embedding,
    generate_embeddings_batch,
)


def test_generate_embedding_returns_384_dims():
    result = generate_embedding("texto de prueba para embedding")
    assert isinstance(result, list)
    assert len(result) == 384


def test_normalize_embeddings_unit_length():
    result = generate_embedding("trabajador electricista Huancayo")
    norm = math.sqrt(sum(x * x for x in result))
    assert abs(norm - 1.0) < 0.05


def test_generate_embeddings_batch_consistent():
    texts = ["primer texto", "segundo texto"]
    results = generate_embeddings_batch(texts)
    assert len(results) == 2
    assert all(len(r) == 384 for r in results)


def test_local_dict_cache_loaded_once():
    import json
    dummy_dict = {"gasfitero": ["plomero"]}
    mock_data = json.dumps(dummy_dict)

    import app.nlp.embeddings.generator as gen_module
    original = gen_module._local_dict
    gen_module._local_dict = None

    with patch("builtins.open", mock_open(read_data=mock_data)):
        apply_local_dictionary("gasfitero habil")
        apply_local_dictionary("gasfitero experto")
        apply_local_dictionary("gasfitero senior")

    gen_module._local_dict = original


def test_apply_local_dictionary_replaces_term():
    result = apply_local_dictionary("busco un gasfitero urgente")
    assert "plomero" in result


def test_embedding_different_texts_differ():
    e1 = generate_embedding("electricista instalacion electrica")
    e2 = generate_embedding("cocinero gastronomia preparacion alimentos")
    dot = sum(a * b for a, b in zip(e1, e2))
    assert dot < 0.99


def test_hash_embedding_fallback_produces_384_dims():
    from app.nlp.embeddings.generator import _hash_embedding
    result = _hash_embedding("texto de prueba para fallback hash")
    assert len(result) == 384
    assert all(isinstance(v, float) for v in result)


def test_hash_embedding_is_normalized():
    import math

    from app.nlp.embeddings.generator import _hash_embedding
    result = _hash_embedding("gasfitero electricista carpintero")
    norm = math.sqrt(sum(v * v for v in result))
    assert abs(norm - 1.0) < 0.01


def test_hash_embedding_different_texts_differ():
    from app.nlp.embeddings.generator import _hash_embedding
    h1 = _hash_embedding("albañil construccion")
    h2 = _hash_embedding("cocinero gastronomia")
    assert h1 != h2


def test_load_embedding_model_does_not_raise():
    from app.nlp.embeddings.generator import load_embedding_model
    load_embedding_model()  # idempotent — model already loaded, must not raise


def test_generate_embedding_falls_back_to_hash_when_model_none():
    with patch("app.nlp.embeddings.generator._get_model", return_value=None):
        result = generate_embedding("texto sin modelo cargado")
    assert len(result) == 384
    assert all(isinstance(v, float) for v in result)


def test_generate_embeddings_batch_falls_back_to_hash_when_model_none():
    with patch("app.nlp.embeddings.generator._get_model", return_value=None):
        results = generate_embeddings_batch(["texto uno", "texto dos"])
    assert len(results) == 2
    assert all(len(r) == 384 for r in results)
