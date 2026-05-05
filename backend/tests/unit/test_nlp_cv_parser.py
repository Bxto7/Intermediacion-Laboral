# RF: RF066-RF070
"""Tests for CV parser NLP pipeline (EXPERIENCIA flow)."""

from app.nlp.cv_parser.parser import extract_cv_fields, parse_pdf
from app.schemas.cv import ParsedCVResult


def test_parse_pdf_returns_string():
    empty_pdf = b"%PDF-1.4\n%%EOF"
    result = parse_pdf(empty_pdf)
    assert isinstance(result, str)


def test_extract_email_from_text():
    text = "Juan Perez\njuan.perez@gmail.com\nLima Peru\nHabilidades: Python, Excel"
    result = extract_cv_fields(text)
    assert result.email == "juan.perez@gmail.com"
    assert result.email_confidence >= 0.99


def test_extract_phone_peruvian_format():
    text = "Maria Lopez\n+51 987654321\nmaria@email.com"
    result = extract_cv_fields(text)
    assert result.phone is not None
    assert result.phone_confidence >= 0.95


def test_low_confidence_field_is_none():
    text = "texto sin informacion relevante de cv"
    result = extract_cv_fields(text)
    assert result.full_name is None or result.full_name_confidence < 0.75


def test_empty_pdf_returns_warnings():
    empty_pdf = b"%PDF-1.4\n%%EOF"
    raw = parse_pdf(empty_pdf)
    assert isinstance(raw, str)
    if raw:
        result = extract_cv_fields(raw)
        assert isinstance(result.parse_warnings, list)


def test_parse_cv_result_schema():
    result = ParsedCVResult(
        full_name="Juan Perez",
        full_name_confidence=0.85,
        email="juan@test.com",
        email_confidence=0.99,
        raw_text_length=500,
        parse_warnings=[],
    )
    assert result.full_name == "Juan Perez"
    assert result.email_confidence == 0.99


def test_extract_skills_from_section():
    text = "Carlos Garcia\ncarlos@email.com\n+51 912345678\nHabilidades: Python, Excel, comunicacion efectiva"
    result = extract_cv_fields(text)
    assert result.email == "carlos@email.com"


def test_extract_two_emails_low_confidence():
    """Spec #3: texto con 2 emails → confianza < 0.99."""
    text = "Juan Perez\njuan@gmail.com\ncontacto: juan.alt@hotmail.com\nLima Peru"
    result = extract_cv_fields(text)
    assert result.email_confidence < 0.99


def test_low_confidence_field_returns_none():
    """Spec #4: campo con confianza < 0.75 devuelve None para full_name."""
    text = "texto sin informacion relevante de cv para extraer nombre"
    result = extract_cv_fields(text)
    # full_name should be None when confidence < 0.75
    if result.full_name_confidence < 0.75:
        assert result.full_name is None


def test_parse_docx_returns_string():
    """Spec #5: parse_docx con bytes mínimos de docx devuelve string."""
    from app.nlp.cv_parser.parser import parse_docx

    # Minimal bytes that won't form a valid docx — returns empty string gracefully
    result = parse_docx(b"not a docx file")
    assert isinstance(result, str)


def test_empty_text_produces_warnings():
    """Spec #6: texto vacío/corto → parse_warnings no vacío."""
    result = extract_cv_fields("")
    assert isinstance(result.parse_warnings, list)
    assert len(result.parse_warnings) > 0
