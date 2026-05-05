# RF: RF071-RF075
from dataclasses import dataclass

from app.nlp.embeddings.generator import apply_local_dictionary, normalize_text

_nlp = None

TRADE_SKILLS_MAP: dict[str, list[str]] = {
    "Electricidad": [
        "instalacion electrica residencial", "cableado estructurado", "tableros electricos",
        "tomacorrientes", "interruptores", "medicion con multimetro", "lectura de planos electricos",
        "instalacion de luminarias", "puesta a tierra", "norma em.010", "instalacion trifasica",
        "mantenimiento preventivo electrico", "instalacion de paneles solares", "cableado subterraneo",
        "instalacion de aire acondicionado", "instalacion de cerco electrico",
    ],
    "Gasfiteria": [
        "instalacion de tuberias", "reparacion de canerias", "instalacion sanitaria",
        "deteccion de fugas", "instalacion de calentadores", "instalacion de inodoros",
        "instalacion de lavaderos", "desatoro de tuberias", "soldadura de tuberias pvc",
        "instalacion de medidores de agua", "reparacion de grifos", "instalacion de duchas",
        "mantenimiento de cisterna", "instalacion de bomba de agua", "conexion de gas natural",
    ],
    "Carpinteria": [
        "fabricacion de muebles", "trabajo en madera", "instalacion de puertas",
        "instalacion de ventanas", "fabricacion de closets", "enchapado de madera",
        "uso de herramientas manuales", "uso de herramientas electricas", "barnizado y lacado",
        "carpinteria de obra", "fabricacion de marcos", "reparacion de muebles",
        "instalacion de pisos de madera", "corte con sierra circular", "medicion y trazado",
    ],
    "Albanileria": [
        "construccion de muros", "vaciado de concreto", "instalacion de ceramicos",
        "tarrajeo de paredes", "nivelado de pisos", "encofrado", "acero de refuerzo",
        "mezcla de concreto", "impermeabilizacion", "instalacion de drywall",
        "construccion de columnas", "reparacion de fisuras", "instalacion de adoquines",
        "construccion de escaleras", "lectura de planos de construccion",
    ],
    "Pintura": [
        "pintura de interiores", "pintura de exteriores", "preparacion de superficies",
        "aplicacion de masilla", "pintura al temple", "pintura latex", "pintura esmalte",
        "uso de rodillo y brocha", "pintura con pistola", "tratamiento de humedad",
        "pintura decorativa", "aplicacion de barniz", "pintura de fachadas",
        "pintura anticorrosiva", "texturizado de paredes",
    ],
}

_GENERIC_SKILLS = ["habilidad tecnica manual", "trabajo en obra", "herramientas de oficio"]


@dataclass
class JobSkillExtraction:
    skills: list[str]
    estimated_level: str
    confidence: float


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("es_core_news_md")
        except Exception:
            _nlp = None
    return _nlp


def _token_overlap(phrase: str, text: str) -> float:
    phrase_tokens = set(phrase.lower().split())
    text_tokens = set(text.lower().split())
    if not phrase_tokens:
        return 0.0
    overlap = len(phrase_tokens & text_tokens)
    return overlap / len(phrase_tokens)


def extract_skills_from_job_description(description: str, trade_category: str) -> JobSkillExtraction:
    normalized = normalize_text(apply_local_dictionary(description))

    category_skills = TRADE_SKILLS_MAP.get(trade_category, _GENERIC_SKILLS)
    max_expected = len(category_skills)

    found: list[str] = []
    freq: dict[str, int] = {}

    for skill in category_skills:
        overlap = _token_overlap(skill, normalized)
        if overlap >= 0.6:
            found.append(skill)
            freq[skill] = sum(normalized.count(t) for t in skill.split())

    if not found:
        for skill in _GENERIC_SKILLS:
            if any(t in normalized for t in skill.split()):
                found.append(skill)

    found = list(dict.fromkeys(found))
    found.sort(key=lambda s: freq.get(s, 0), reverse=True)

    word_count = len(description.split())
    if word_count >= 200 and len(found) >= 8:
        level = "avanzado"
    elif len(found) >= 5:
        level = "intermedio"
    else:
        level = "basico"

    confidence = min(1.0, len(found) / max(max_expected, 1))

    return JobSkillExtraction(skills=found, estimated_level=level, confidence=confidence)


def build_trade_profile_text(
    trade_category: str,
    years_experience: int,
    district: str,
    avg_rating: float,
    portfolio_skills: list[str],
    portfolio_count: int,
) -> str:
    return (
        f"{trade_category} | {years_experience} anios | {district} | "
        f"{avg_rating:.1f}/5.0 | trabajos: {portfolio_count} | "
        f"habilidades: {', '.join(portfolio_skills)}"
    )
