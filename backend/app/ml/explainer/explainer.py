# RF: RF146-RF150 (M10) — explicaciones en lenguaje coloquial
import structlog

logger = structlog.get_logger()

LABEL_MAP = {
    "Alta": (0.70, 1.01),
    "Media": (0.45, 0.70),
    "Baja": (0.00, 0.45),
}


def explain_match(
    combined_score: float,
    worker_skills: list[str],
    offer_required_skills: list[str],
    offer_preferred_skills: list[str],
    worker_type: str,
) -> dict:
    """
    Genera explicacion legible del match para el trabajador.
    Cubre RF146-RF150.
    """
    worker_set = {s.lower().strip() for s in worker_skills}
    required_set = {s.lower().strip() for s in offer_required_skills}
    preferred_set = {s.lower().strip() for s in offer_preferred_skills}

    matching_skills = list(worker_set & (required_set | preferred_set))
    missing_skills = list(required_set - worker_set)
    extra_skills = list(worker_set - required_set - preferred_set)

    label = "Baja"
    for lbl, (lo, hi) in LABEL_MAP.items():
        if lo <= combined_score < hi:
            label = lbl
            break

    message = _build_message(label, matching_skills, missing_skills, worker_type)

    return {
        "combined_score": round(combined_score, 4),
        "compatibility_label": label,
        "matching_skills": matching_skills[:5],
        "missing_skills": missing_skills[:5],
        "extra_skills": extra_skills[:3],
        "message": message,
    }


def _build_message(
    label: str,
    matching: list[str],
    missing: list[str],
    worker_type: str,
) -> str:
    if label == "Alta":
        if matching:
            return f"Excelente compatibilidad. Tus habilidades en {', '.join(matching[:2])} coinciden bien con esta oferta."
        return "Excelente compatibilidad con esta oferta."

    if label == "Media":
        msgs = ["Compatibilidad media con esta oferta."]
        if missing:
            msgs.append(f"Podria fortalecerte en: {', '.join(missing[:2])}.")
        return " ".join(msgs)

    # Baja
    msgs = ["Compatibilidad baja con esta oferta."]
    if missing:
        msgs.append(f"Esta oferta requiere: {', '.join(missing[:3])}.")
    if worker_type == "primer_empleo":
        msgs.append("Sigue completando tu perfil para mejorar tus posibilidades.")
    return " ".join(msgs)
