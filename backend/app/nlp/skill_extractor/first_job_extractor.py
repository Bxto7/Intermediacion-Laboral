# RF: RF059-RF064
from app.nlp.embeddings.generator import normalize_text

_nlp = None

SOFT_SKILLS_MAP: dict[str, str] = {
    "puntual": "puntualidad",
    "responsable": "responsabilidad",
    "trabajo en equipo": "trabajo colaborativo",
    "trabajador": "disposicion al trabajo",
    "honesto": "integridad",
    "aprendo rapido": "aprendizaje rapido",
    "me adapto": "adaptabilidad",
    "me llevo bien con todos": "habilidades interpersonales",
    "soy ordenado": "organizacion",
    "tengo iniciativa": "proactividad",
    "ayudo en casa": "gestion domestica",
    "cuido a mis hermanos": "cuidado de personas",
    "vendo en el mercado": "ventas informales",
    "manejo caja": "manejo de efectivo",
    "atiendo clientes": "atencion al cliente",
    "reparto": "logistica de entrega",
    "cocino": "preparacion de alimentos",
    "computadora": "manejo de computadora",
    "excel": "Microsoft Excel",
    "internet": "navegacion web",
    "comunicativo": "comunicacion efectiva",
    "creativo": "creatividad",
    "lider": "liderazgo",
    "puntualidad": "puntualidad",
    "ayudo a mi papa": "trabajo familiar",
    "ayudo a mi mama": "trabajo familiar",
    "carpinteria": "trabajo en madera",
    "madera": "trabajo en madera",
    "costura": "confeccion textil",
    "cocina": "preparacion de alimentos",
    "limpieza": "limpieza y orden",
    "jardineria": "jardineria basica",
    "manualidades": "trabajo manual",
    "dibujo": "dibujo tecnico basico",
    "musica": "habilidades artisticas",
    "deporte": "trabajo en equipo deportivo",
    "voluntariado": "servicio a la comunidad",
    "ventas": "habilidades de venta",
    "conducir": "conduccion de vehiculos",
    "redes sociales": "manejo de redes sociales",
    "fotografia": "fotografia basica",
}

SECTOR_SKILLS_MAP: dict[str, list[str]] = {
    "Comercio": ["ventas informales", "atencion al cliente", "manejo de efectivo", "habilidades de venta", "logistica de entrega"],
    "Gastronomia": ["preparacion de alimentos", "limpieza y orden", "trabajo colaborativo", "organizacion"],
    "Construccion": ["trabajo manual", "trabajo en madera", "trabajo familiar", "organizacion"],
    "Tecnologia": ["manejo de computadora", "Microsoft Excel", "navegacion web", "manejo de redes sociales"],
    "Cuidado de personas": ["cuidado de personas", "gestion domestica", "servicio a la comunidad", "comunicacion efectiva"],
    "Manufactura": ["trabajo manual", "confeccion textil", "trabajo en madera", "organizacion"],
    "Transporte": ["conduccion de vehiculos", "logistica de entrega", "puntualidad"],
    "Servicios": ["atencion al cliente", "limpieza y orden", "puntualidad", "responsabilidad", "comunicacion efectiva"],
}


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("es_core_news_md")
        except Exception:
            _nlp = None
    return _nlp


def extract_skills_from_wizard_answer(text: str, step: int) -> list[str]:
    normalized = normalize_text(text)
    found: set[str] = set()

    text_lower = normalized.lower()
    for term, skill in SOFT_SKILLS_MAP.items():
        if len(term) >= 4 and term in text_lower:
            found.add(skill)

    nlp = _get_nlp()
    if nlp is not None:
        doc = nlp(text[:500])
        for ent in doc.ents:
            if ent.label_ in ("MISC", "PER", "ORG") and len(ent.text) >= 3:
                found.add(ent.text.lower())

    return sorted(found)


def suggest_job_sectors(skills: list[str]) -> list[str]:
    scores: dict[str, int] = {}
    skills_lower = [s.lower() for s in skills]

    for sector, sector_skills in SECTOR_SKILLS_MAP.items():
        score = sum(1 for ss in sector_skills if any(ss in sk or sk in ss for sk in skills_lower))
        if score > 0:
            scores[sector] = score

    sorted_sectors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [s for s, _ in sorted_sectors[:5]]


def build_first_job_profile_text(
    district: str,
    skills: list[str],
    interests: list[str],
    education_level: str,
) -> str:
    return (
        f"primer empleo | {district} | educacion: {education_level} | "
        f"habilidades: {', '.join(skills)} | intereses: {', '.join(interests)}"
    )
