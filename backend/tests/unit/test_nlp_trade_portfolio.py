# RF: RF071-RF075
"""Tests for NLP extraction from OFICIO portfolio entries."""

from app.nlp.portfolio_nlp.trade_extractor import (
    build_trade_profile_text,
    extract_skills_from_job_description,
)


def test_extract_skills_electricidad():
    desc = "Instale el cableado de una casa de dos pisos, puse tomacorrientes y el tablero electrico"
    result = extract_skills_from_job_description(desc, "Electricidad")
    assert len(result.skills) > 0
    assert any("cableado" in s or "tablero" in s or "tomacorriente" in s for s in result.skills)


def test_extract_skills_gasfiteria():
    desc = "Repare canerias del bano, instale ducha y grifos nuevos para cliente en El Tambo"
    result = extract_skills_from_job_description(desc, "Gasfiteria")
    assert len(result.skills) > 0


def test_extract_skills_carpinteria():
    desc = "Fabrique muebles de madera y puertas para una casa en Huancayo, use herramientas electricas"
    result = extract_skills_from_job_description(desc, "Carpinteria")
    assert len(result.skills) > 0


def test_estimated_level_avanzado():
    # 35 words × 6 = 210 words, well above the 200-word threshold for "avanzado"
    skills_desc = " ".join(
        [
            "instalacion electrica residencial cableado estructurado tableros electricos",
            "tomacorrientes interruptores medicion con multimetro lectura de planos electricos",
            "instalacion de luminarias puesta a tierra norma em010 instalacion trifasica",
            "mantenimiento preventivo electrico instalacion de paneles solares cableado subterraneo",
        ]
        * 6
    )
    result = extract_skills_from_job_description(skills_desc, "Electricidad")
    assert result.estimated_level == "avanzado"


def test_estimated_level_basico():
    result = extract_skills_from_job_description("pinte una pared", "Pintura")
    assert result.estimated_level == "basico"


def test_build_trade_profile_text_format():
    text = build_trade_profile_text(
        trade_category="Electricidad",
        years_experience=5,
        district="Huancayo",
        avg_rating=4.5,
        portfolio_skills=["instalacion electrica", "tableros"],
        portfolio_count=10,
    )
    assert "Electricidad" in text
    assert "5" in text
    assert "Huancayo" in text


def test_extract_skills_electricidad_cableado():
    """Spec #1: descripción con 'cableado' → skills de electricidad."""
    # Use description that matches "cableado estructurado" (both tokens present)
    desc = "Realize el cableado estructurado de una vivienda y el cableado subterraneo en Huancayo"
    result = extract_skills_from_job_description(desc, "Electricidad")
    assert len(result.skills) > 0
    assert any("cableado" in s for s in result.skills)


def test_extract_skills_electricidad_tablero():
    """Spec #2: descripción con 'tablero' → skills de electricidad."""
    # Use description that matches "tableros electricos" (both tokens present)
    desc = "Instale los tableros electricos principales y tomacorrientes en casa de dos pisos"
    result = extract_skills_from_job_description(desc, "Electricidad")
    assert len(result.skills) > 0
    assert any("tablero" in s for s in result.skills)


def test_extract_skills_gasfiteria_caneria():
    """Spec #3: descripción con 'cañería' y 'baño' → skills de gasfitería."""
    # Use description that matches "reparacion de canerias" and "instalacion sanitaria"
    desc = "Reparacion de canerias rotas e instalacion sanitaria nueva en El Tambo"
    result = extract_skills_from_job_description(desc, "Gasfiteria")
    assert len(result.skills) > 0
    skill_text = " ".join(result.skills).lower()
    assert any(term in skill_text for term in ["caner", "sanitar", "instalac", "gasfite", "plomer"])


def test_build_trade_profile_text_contains_category():
    """Spec #6: texto contiene trade_category, años y district."""
    text = build_trade_profile_text(
        trade_category="Carpinteria",
        years_experience=3,
        district="Chilca",
        avg_rating=4.0,
        portfolio_skills=["trabajo en madera"],
        portfolio_count=5,
    )
    assert "Carpinteria" in text
    assert "3" in text
    assert "Chilca" in text


def test_confidence_between_0_and_1():
    """Spec #7: confidence en [0.0, 1.0]."""
    desc = "Pinte una casa de dos pisos en Huancayo con pintura latex"
    result = extract_skills_from_job_description(desc, "Pintura")
    assert 0.0 <= result.confidence <= 1.0
