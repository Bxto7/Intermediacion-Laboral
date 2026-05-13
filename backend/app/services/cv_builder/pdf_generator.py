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

    base_ctx = {
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "district": worker.district or "Junin",
    }

    if worker_type == "primer_empleo":
        res = await db.execute(
            select(WizardProgress).where(WizardProgress.worker_id == str(worker.id))
        )
        progress = res.scalar_one_or_none()
        answers = progress.answers if progress else {}
        skills = list(progress.extracted_skills or []) if progress else []

        return {
            **base_ctx,
            "skills": skills,
            "education": answers.get("education", []),
            "activities": answers.get("activities", []),
            "objective": answers.get("job_interests", ""),
            "linkedin": answers.get("linkedin", ""),
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

        return {
            **base_ctx,
            "trade_category": worker.trade_category or "Oficio",
            "years_experience": worker.years_experience or 0,
            "avg_rating": f"{avg_rating:.1f}",
            "portfolio_count": len(entries),
            "slug": getattr(worker, "username", "") or "",
            "availability_text": availability_text,
            "skills": list(set(all_skills))[:12],
            "portfolio_entries": [
                {
                    "title": e.title,
                    "description": (e.description or "")[:200],
                    "period": (
                        f"{e.period_start} - {e.period_end or 'actualidad'}"
                        if e.period_start
                        else ""
                    ),
                    "client_rating": float(e.client_rating) if e.client_rating else None,
                }
                for e in entries
            ],
        }

    else:  # experiencia
        profile: dict = {}
        if hasattr(worker, "bio") and worker.bio:
            profile["bio"] = worker.bio
        if hasattr(worker, "job_title") and worker.job_title:
            profile["job_title"] = worker.job_title

        return {
            **base_ctx,
            "job_title": profile.get("job_title", "Profesional"),
            "years_experience": worker.years_experience or 0,
            "bio": profile.get("bio", ""),
            "experiences": profile.get("experiences", []),
            "education": profile.get("education", []),
            "skills": profile.get("skills", []),
            "linkedin": profile.get("linkedin", ""),
        }
