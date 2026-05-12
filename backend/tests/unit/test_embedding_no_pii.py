"""Verifica que el texto de perfil para embeddings no contiene PII.

RF: RNF001, RNF006 — Sprint 3 Security Audit
Covers: build_profile_text() in app/nlp/embeddings/generator.py
"""
import re
from unittest.mock import MagicMock

import pytest

from app.nlp.embeddings.generator import build_profile_text

DNI_PATTERN = re.compile(r"\b\d{8}\b")
PHONE_PATTERN = re.compile(r"\+51\s*9\d{8}")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def _make_worker(worker_type: str):
    w = MagicMock()
    w.worker_type = worker_type
    # PII fields — must NEVER appear in output
    w.full_name = "Juan Perez Lopez"
    w.dni = b"encrypted_dni"
    w.phone = b"encrypted_phone"
    # Non-PII operational fields — allowed in output
    w.district = "Huancayo"
    w.trade_category = "Electricidad"
    w.years_experience = 5
    w.avg_rating = 4.2
    return w


@pytest.mark.parametrize("worker_type", ["primer_empleo", "experiencia", "oficio"])
def test_profile_text_no_pii(worker_type):
    """build_profile_text() must not include any PII in the returned string."""
    worker = _make_worker(worker_type)
    extra = {
        "wizard_skills": ["trabajo en equipo", "puntualidad"],
        "job_interests": "electricidad, construccion",
        "portfolio_count": 3,
        "portfolio_skills": ["instalacion electrica", "tableros"],
        "job_title": "Tecnico electrico",
        "bio": "Experiencia en instalaciones residenciales",
    }
    text = build_profile_text(worker, extra)

    assert not DNI_PATTERN.search(text), f"DNI encontrado en texto: {text!r}"
    assert not PHONE_PATTERN.search(text), f"Telefono encontrado en texto: {text!r}"
    assert not EMAIL_PATTERN.search(text), f"Email encontrado en texto: {text!r}"
    assert "Juan" not in text and "Perez" not in text, (
        f"Nombre encontrado en texto: {text!r}"
    )
    assert isinstance(text, str) and len(text) > 0, "El texto de perfil no debe estar vacio"


@pytest.mark.parametrize("worker_type", ["primer_empleo", "experiencia", "oficio"])
def test_profile_text_contains_expected_fields(worker_type):
    """build_profile_text() must include non-PII operational data."""
    worker = _make_worker(worker_type)
    extra = {
        "wizard_skills": ["puntualidad"],
        "job_interests": "electricidad",
        "portfolio_count": 2,
        "portfolio_skills": ["cableado"],
        "job_title": "Tecnico",
        "bio": "bio de ejemplo",
    }
    text = build_profile_text(worker, extra)

    if worker_type == "primer_empleo":
        assert "Huancayo" in text
        assert "puntualidad" in text
    elif worker_type == "oficio":
        assert "Electricidad" in text
        assert "Huancayo" in text
        assert "cableado" in text
    else:  # experiencia
        assert "Tecnico" in text or "Huancayo" in text


def test_profile_text_no_encrypted_bytes_repr():
    """Encrypted bytes (b'...') must not appear as repr strings in embedding text."""
    worker = _make_worker("oficio")
    extra = {"portfolio_count": 1, "portfolio_skills": ["soldadura"]}
    text = build_profile_text(worker, extra)

    assert "b'" not in text, f"Bytes repr encontrado en texto: {text!r}"
    assert "encrypted" not in text.lower(), (
        f"Literal 'encrypted' encontrado en texto: {text!r}"
    )
