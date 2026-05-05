# RF: RF096-RF105
"""Tests for cold-start embedding generation (primer_empleo and oficio)."""
import pytest


@pytest.mark.asyncio
async def test_cold_start_embedding_generates_384_dims():
    """Cold-start embedding returns 384-dim vector (real model, not stub)."""
    from app.nlp.embeddings.generator import generate_embedding_async
    result = await generate_embedding_async("primer empleo habilidades blandas")
    assert len(result) == 384
    assert isinstance(result[0], float)
