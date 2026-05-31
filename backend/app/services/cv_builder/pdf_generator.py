# RF: RF096-RF110 (M06) — generacion de CVs PDF con WeasyPrint
from pathlib import Path
from uuid import UUID

import structlog
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_field
from app.models import PortfolioEntry, WizardProgress, Worker

logger = structlog.get_logger()

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "utils" / "cv_templates"

TEMPLATE_MAP = {
    "primer_empleo": "primer_empleo.html",
    "oficio": "oficio.html",
    "experiencia": "experiencia.html",
}

# Color de acento (barra lateral del CV) por tipo de trabajador
ACCENT_COLOR = {
    "primer_empleo": "#34508c",  # azul profesional
    "oficio": "#1f4e5f",         # azul petroleo
    "experiencia": "#8b1e2d",    # vino (estilo CV ejecutivo)
}
DEFAULT_ACCENT = "#8b1e2d"


def _initials(name: str) -> str:
    """Dos iniciales en mayuscula para el placeholder de foto."""
    parts = [p for p in (name or "").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _norm_education(raw: list) -> list[dict]:
    """Normaliza educacion (acepta dicts variados o strings)."""
    out: list[dict] = []
    for it in raw or []:
        if isinstance(it, dict):
            out.append({
                "degree": it.get("degree") or it.get("title") or it.get("name") or "",
                "institution": it.get("institution") or it.get("school") or it.get("place") or "",
                "period": it.get("period") or "",
            })
        elif isinstance(it, str) and it.strip():
            out.append({"degree": it, "institution": "", "period": ""})
    return out


def _norm_experiences(raw: list) -> list[dict]:
    """Normaliza experiencias/actividades a {role, company, period, bullets, achievements}."""
    out: list[dict] = []
    for it in raw or []:
        if isinstance(it, dict):
            desc = it.get("description") or it.get("tasks") or ""
            bullets = desc if isinstance(desc, list) else ([desc] if desc else [])
            out.append({
                "role": it.get("role") or it.get("title") or it.get("position") or "",
                "company": it.get("company") or it.get("place") or it.get("organization") or "",
                "period": it.get("period") or "",
                "bullets": bullets,
                "achievements": it.get("achievements") or [],
            })
        elif isinstance(it, str) and it.strip():
            out.append({"role": it, "company": "", "period": "", "bullets": [], "achievements": []})
    return out

# Module-level singleton: building Environment per call is expensive (filesystem scan + caching)
_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


async def generate_cv_pdf(
    worker_id: UUID | str,
    db: AsyncSession,
) -> bytes:
    """Genera el PDF del CV segun tipo de trabajador. Cubre RF096-RF110."""
    res = await db.execute(select(Worker).where(Worker.id == str(worker_id)))
    worker = res.scalar_one_or_none()
    if not worker:
        raise ValueError(f"Worker {worker_id} no encontrado")

    worker_type = worker.worker_type
    template_file = TEMPLATE_MAP.get(worker_type, "experiencia.html")
    context = await _build_template_context(worker, worker_type, db)

    template = _jinja_env.get_template(template_file)
    html_content = template.render(**context)

    try:
        from weasyprint import HTML as WeasyHTML  # type: ignore[import-untyped]  # noqa: N811
        pdf_bytes: bytes = WeasyHTML(string=html_content).write_pdf()
    except ImportError as exc:
        raise RuntimeError(
            "WeasyPrint no disponible: asegurate de tener las dependencias del sistema instaladas "
            "(libglib2.0-0, libpango-1.0-0, libcairo2). Ver Dockerfile."
        ) from exc

    logger.info(
        "cv_pdf_generated",
        worker_id=str(worker_id),
        worker_type=worker_type,
        size_bytes=len(pdf_bytes),
    )
    return pdf_bytes


async def _build_template_context(
    worker: Worker,
    worker_type: str,
    db: AsyncSession,
) -> dict:
    """Construye el contexto del template segun tipo de trabajador."""
    full_name = decrypt_field(worker.full_name) if isinstance(worker.full_name, bytes) else str(worker.full_name)
    phone = ""
    if worker.phone:
        try:
            phone = decrypt_field(worker.phone) if isinstance(worker.phone, bytes) else str(worker.phone)
        except Exception:
            phone = ""

    # Buscar email desde la tabla users via user_id
    from app.models.user import User
    user_res = await db.execute(select(User).where(User.id == str(worker.user_id)))
    user = user_res.scalar_one_or_none()
    email = user.email if user else ""

    district = worker.district or ""
    address = f"{district}, Junin" if district else "Junin, Peru"

    base_ctx = {
        "full_name": full_name,
        "initials": _initials(full_name),
        "phone": phone,
        "email": email,
        "address": address,
        "district": district or "Junin",
        "photo_url": None,  # el modelo Worker aun no almacena foto
        "accent_color": ACCENT_COLOR.get(worker_type, DEFAULT_ACCENT),
        "languages": [],    # sin fuente de datos estructurada todavia
        "additional_info": [],
        "public_url": None,
        "linkedin": None,
    }

    if worker_type == "primer_empleo":
        res = await db.execute(
            select(WizardProgress).where(WizardProgress.worker_id == str(worker.id))
        )
        progress = res.scalar_one_or_none()
        answers = progress.answers if progress else {}
        skills = list(progress.extracted_skills or []) if progress else []

        objective = answers.get("job_interests") or answers.get("objective") or ""
        if isinstance(objective, list):
            objective = ", ".join(str(o) for o in objective)

        return {
            **base_ctx,
            "job_title": "En busqueda de primer empleo",
            "summary": objective,
            "education": _norm_education(answers.get("education", [])),
            "experiences": _norm_experiences(answers.get("activities", [])),
            "skills": skills,
            "linkedin": answers.get("linkedin") or None,
        }

    elif worker_type == "oficio":
        res = await db.execute(
            select(PortfolioEntry)
            .where(
                PortfolioEntry.worker_id == str(worker.id),
                PortfolioEntry.is_public.is_(True),
            )
            .order_by(PortfolioEntry.created_at.desc())
            .limit(6)
        )
        entries = res.scalars().all()
        all_skills: list[str] = []
        for entry in entries:
            all_skills.extend(entry.extracted_skills or [])

        avg_rating = float(worker.avg_rating or 0)
        availability_text = {
            "inmediata": "Disponible ahora",
            "semana": "Disponible esta semana",
            "mes": "Disponible este mes",
        }.get(getattr(worker, "availability", "inmediata"), "Disponible")

        trade = worker.trade_category or "Oficio"
        years = worker.years_experience or 0
        slug = getattr(worker, "username", "") or ""

        experiences = []
        for e in entries:
            period = (
                f"{e.period_start} - {e.period_end or 'actualidad'}" if e.period_start else ""
            )
            achievements = (
                [f"Calificacion del cliente: {float(e.client_rating):.1f}/5.0"]
                if e.client_rating
                else []
            )
            experiences.append({
                "role": e.title,
                "company": "",
                "period": period,
                "bullets": [(e.description or "")[:220]] if e.description else [],
                "achievements": achievements,
            })

        return {
            **base_ctx,
            "job_title": trade,
            "trade_category": trade,
            "years_experience": years,
            "avg_rating": f"{avg_rating:.1f}",
            "portfolio_count": len(entries),
            "availability_text": availability_text,
            "public_url": f"drtpe.gob.pe/p/{slug}" if slug else None,
            "summary": f"{trade} con {years} anios de experiencia en la region Junin.",
            "skills": list(dict.fromkeys(all_skills))[:12],
            "experiences": experiences,
            "education": [],
        }

    else:  # experiencia
        bio = worker.bio if (hasattr(worker, "bio") and worker.bio) else ""
        job_title = (
            worker.job_title if (hasattr(worker, "job_title") and worker.job_title) else "Profesional"
        )
        years = worker.years_experience or 0
        if not bio and years:
            bio = f"Profesional con {years} anios de experiencia en la region Junin."

        # NOTA (CV-EXP-VACIO): experiencias/educacion/skills no se persisten aun
        # (parse-cv devuelve los datos pero no los guarda). Se renderiza con estado vacio.
        return {
            **base_ctx,
            "job_title": job_title,
            "years_experience": years,
            "summary": bio,
            "experiences": [],
            "education": [],
            "skills": [],
        }
