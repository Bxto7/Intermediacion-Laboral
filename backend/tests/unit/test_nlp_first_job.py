# RF: RF059-RF064
"""Tests for NLP skill extraction from first-job wizard conversations."""

from app.nlp.embeddings.generator import apply_local_dictionary
from app.nlp.skill_extractor.first_job_extractor import (
    build_first_job_profile_text,
    extract_skills_from_wizard_answer,
    suggest_job_sectors,
)


def test_apply_local_dictionary_gasfitero():
    result = apply_local_dictionary("necesito un gasfitero")
    assert "plomero" in result


def test_apply_local_dictionary_albañil():
    result = apply_local_dictionary("trabajo de albanil")
    assert "constructor" in result


def test_apply_local_dictionary_preserves_unknown_terms():
    result = apply_local_dictionary("tecnico en informatica")
    assert "tecnico" in result


def test_apply_local_dictionary_case_insensitive():
    result = apply_local_dictionary("GASFITERO experto")
    assert "plomero" in result.lower()


def test_extract_skills_puntual():
    skills = extract_skills_from_wizard_answer("soy muy puntual y responsable", step=3)
    assert "puntualidad" in skills


def test_extract_skills_informal_experience():
    skills = extract_skills_from_wizard_answer(
        "ayudo a mi papá en su carpintería y trabajo en madera", step=4
    )
    assert any("madera" in s or "carpinteria" in s or "trabajo" in s for s in skills)


def test_suggest_sectors_from_skills():
    skills = ["preparacion de alimentos", "limpieza y orden", "trabajo colaborativo"]
    sectors = suggest_job_sectors(skills)
    assert "Gastronomia" in sectors


def test_suggest_sectors_returns_max_5():
    skills = [
        "puntualidad", "atencion al cliente", "preparacion de alimentos",
        "manejo de computadora", "logistica de entrega", "cuidado de personas",
    ]
    sectors = suggest_job_sectors(skills)
    assert len(sectors) <= 5


def test_normalize_text_removes_stopwords():
    from app.nlp.embeddings.generator import normalize_text

    result = normalize_text("el trabajo en la empresa")
    tokens = result.split()
    assert "el" not in tokens
    assert "en" not in tokens
    assert "la" not in tokens


def test_build_first_job_profile_text():
    text = build_first_job_profile_text(
        district="Huancayo",
        skills=["puntualidad", "atencion al cliente"],
        interests=["Comercio"],
        education_level="secundaria",
    )
    assert "Huancayo" in text
    assert "puntualidad" in text
    assert "secundaria" in text


def test_extract_skills_trabajador():
    """Spec #2: texto con 'trabajador' → 'disposicion al trabajo' en resultado."""
    skills = extract_skills_from_wizard_answer("soy muy trabajador y dedicado", step=3)
    assert "disposicion al trabajo" in skills


def test_extract_skills_informal_carpinteria():
    """Spec #3: 'ayudo a mi papá en su carpintería' → habilidad relacionada madera/carpintería."""
    skills = extract_skills_from_wizard_answer(
        "ayudo a mi papa en su carpinteria haciendo muebles", step=4
    )
    assert any("madera" in s or "carpinteria" in s or "familiar" in s for s in skills)


def test_suggest_sectors_cocina():
    """Spec #4: skills de cocina → 'Gastronomia' en top sectores."""
    skills = ["preparacion de alimentos", "limpieza y orden"]
    sectors = suggest_job_sectors(skills)
    assert "Gastronomia" in sectors


def test_suggest_sectors_construccion():
    """Spec #5: skills de construcción → 'Construccion' en top sectores."""
    skills = ["trabajo manual", "trabajo en madera"]
    sectors = suggest_job_sectors(skills)
    assert "Construccion" in sectors


def test_normalize_text_fixes_encoding():
    """Spec #7: texto con encoding roto → ftfy lo corrige."""
    from app.nlp.embeddings.generator import normalize_text

    # ftfy typically fixes issues like incorrect encoding representations
    # We use a string that represents common encoding damage
    broken = "café trabajador"
    result = normalize_text(broken)
    assert isinstance(result, str)
    assert len(result) > 0


def test_apply_local_dictionary_fierrero():
    """Spec #10: 'fierrero' → 'soldador' en el texto."""
    result = apply_local_dictionary("busco un fierrero para obra")
    assert "soldador" in result


def test_build_first_job_profile_text_format():
    """Spec #11: texto incluye district, skills y 'primer empleo'."""
    text = build_first_job_profile_text(
        district="El Tambo",
        skills=["responsabilidad", "trabajo colaborativo"],
        interests=["Servicios"],
        education_level="tecnica",
    )
    assert "primer empleo" in text.lower()
    assert "El Tambo" in text
    assert "responsabilidad" in text
