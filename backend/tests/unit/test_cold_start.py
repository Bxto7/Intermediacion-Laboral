# RF: RF096-RF105
"""Tests for cold-start embedding generation (primer_empleo and oficio)."""
import re
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_cold_start_embedding_generates_384_dims():
    """Cold-start embedding returns 384-dim vector (real model, not stub)."""
    from app.nlp.embeddings.generator import generate_embedding_async
    result = await generate_embedding_async("primer empleo habilidades blandas")
    assert len(result) == 384
    assert isinstance(result[0], float)


@pytest.mark.asyncio
async def test_cold_start_primer_empleo_with_wizard():
    """PRIMER_EMPLEO con respuestas del wizard genera texto con habilidades."""
    from app.ml.cold_start.resolver import _build_first_job_text

    worker = MagicMock()
    worker.id = str(uuid4())
    worker.worker_type = "primer_empleo"
    worker.district = "Huancayo"

    wizard_progress = MagicMock()
    wizard_progress.extracted_skills = ["trabajo en equipo", "puntualidad"]
    wizard_progress.answers = {"job_interests": "administracion"}

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = wizard_progress

    db = AsyncMock()
    db.execute.return_value = mock_result

    text = await _build_first_job_text(worker, db)
    assert "primer empleo" in text
    assert "Huancayo" in text
    assert "trabajo en equipo" in text or "puntualidad" in text


@pytest.mark.asyncio
async def test_cold_start_primer_empleo_empty_wizard():
    """PRIMER_EMPLEO sin wizard genera texto minimo sin error."""
    from app.ml.cold_start.resolver import _build_first_job_text

    worker = MagicMock()
    worker.id = str(uuid4())
    worker.district = "El Tambo"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = mock_result

    text = await _build_first_job_text(worker, db)
    assert "primer empleo" in text
    assert "El Tambo" in text


@pytest.mark.asyncio
async def test_cold_start_oficio_with_portfolio():
    """OFICIO con portfolio genera texto con habilidades extraidas."""
    from app.ml.cold_start.resolver import _build_trade_text

    worker = MagicMock()
    worker.id = str(uuid4())
    worker.trade_category = "Electricidad"
    worker.district = "Chilca"
    worker.years_experience = 5

    entry1 = MagicMock()
    entry1.extracted_skills = ["instalacion electrica", "cableado"]
    entry2 = MagicMock()
    entry2.extracted_skills = ["tableros electricos"]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [entry1, entry2]

    db = AsyncMock()
    db.execute.return_value = mock_result

    text = await _build_trade_text(worker, db)
    assert "Electricidad" in text
    assert "Chilca" in text
    assert "instalacion electrica" in text or "cableado" in text


@pytest.mark.asyncio
async def test_cold_start_oficio_without_portfolio():
    """OFICIO sin portfolio genera texto solo desde metadata del worker."""
    from app.ml.cold_start.resolver import _build_trade_text

    worker = MagicMock()
    worker.id = str(uuid4())
    worker.trade_category = "Gasfiteria"
    worker.district = "Huancayo"
    worker.years_experience = 3

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    db = AsyncMock()
    db.execute.return_value = mock_result

    text = await _build_trade_text(worker, db)
    assert "Gasfiteria" in text
    assert "trabajos: 0" in text


def test_cold_start_experiencia_text():
    """EXPERIENCIA genera texto desde bio y job_title."""
    from app.ml.cold_start.resolver import _build_experiencia_text

    worker = MagicMock()
    worker.bio = "Contador con experiencia en empresas medianas"
    worker.job_title = "Contador"
    worker.years_experience = 7
    worker.district = "Huancayo"

    text = _build_experiencia_text(worker)
    assert "Contador" in text
    assert "7" in text
    assert "Huancayo" in text


def test_embedding_profile_no_pii():
    """El texto de perfil no debe contener DNI, telefono ni email."""
    from app.ml.cold_start.resolver import _build_experiencia_text

    worker = MagicMock()
    worker.bio = "Profesional con experiencia"
    worker.job_title = "Tecnico"
    worker.years_experience = 3
    worker.district = "El Tambo"

    text = _build_experiencia_text(worker)
    assert not re.search(r"\b\d{8}\b", text)
    assert "@" not in text
    assert not re.search(r"\+51\s*9\d{8}", text)
