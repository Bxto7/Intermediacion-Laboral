# RF: RF076-RF079, RNF001
# Security: all task arguments that are UUIDs are validated before any DB query
# to prevent task injection with malformed inputs (Sprint 3 audit).
import uuid as _uuid_module

import structlog
from sqlalchemy import select

from app.tasks import app

logger = structlog.get_logger()


def _validate_uuid(value: str, field_name: str = "id") -> bool:
    """Return True if value is a valid UUID v4; log and return False otherwise."""
    try:
        _uuid_module.UUID(value, version=4)
        return True
    except (ValueError, AttributeError):
        logger.error("invalid_uuid_in_task", field=field_name, value=repr(value))
        return False


def _get_sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    return sessionmaker(bind=engine)


@app.task(name="generate_worker_embedding", queue="embeddings")
def generate_worker_embedding(worker_id: str) -> None:
    if not _validate_uuid(worker_id, "worker_id"):
        return  # Silenced — invalid input, do not retry
    import time

    from app.models.portfolio import PortfolioEntry
    from app.models.wizard import WizardProgress
    from app.models.worker import Worker
    from app.nlp.embeddings.generator import generate_embedding
    from app.nlp.portfolio_nlp.trade_extractor import build_trade_profile_text
    from app.nlp.skill_extractor.first_job_extractor import build_first_job_profile_text

    start = time.monotonic()
    session_factory = _get_sync_session()

    with session_factory() as db:
        worker = db.get(Worker, worker_id)
        if not worker:
            logger.warning("worker_not_found_for_embedding", worker_id=worker_id)
            return

        wtype = worker.worker_type
        profile_text = ""

        if wtype == "primer_empleo":
            wizard = db.execute(
                select(WizardProgress).where(WizardProgress.worker_id == worker_id)
            ).scalar_one_or_none()
            skills = wizard.extracted_skills if wizard else []
            interests = (wizard.job_interests if wizard else []) or []
            education = (wizard.answers or {}).get("2", {}).get("education_level", "")
            profile_text = build_first_job_profile_text(
                district=worker.district or "",
                skills=skills,
                interests=interests,
                education_level=education,
            )

        elif wtype == "oficio":
            entries = db.execute(
                select(PortfolioEntry).where(PortfolioEntry.worker_id == worker_id)
            ).scalars().all()
            all_skills: list[str] = []
            for e in entries:
                all_skills.extend(e.extracted_skills or [])
            all_skills = list(dict.fromkeys(all_skills))
            profile_text = build_trade_profile_text(
                trade_category=worker.trade_category or "",
                years_experience=worker.years_experience or 0,
                district=worker.district or "",
                avg_rating=float(worker.avg_rating or 0),
                portfolio_skills=all_skills,
                portfolio_count=len(entries),
            )

        else:
            profile_text = (
                f"{worker.job_title or ''} | {worker.years_experience or 0} anios | "
                f"{worker.district or ''} | {float(worker.avg_rating or 0):.1f}/5.0 | "
                f"{worker.bio or ''}"
            )

        embedding = generate_embedding(profile_text)
        worker.embedding = embedding
        db.commit()

    elapsed = round((time.monotonic() - start) * 1000, 2)
    logger.info(
        "worker_embedding_generated",
        worker_id=worker_id,
        worker_type=wtype,
        profile_text_length=len(profile_text),
        duration_ms=elapsed,
    )


@app.task(name="generate_job_embedding", queue="embeddings")
def generate_job_embedding(job_offer_id: str) -> None:
    if not _validate_uuid(job_offer_id, "job_offer_id"):
        return  # Silenced — invalid input, do not retry
    from app.models.job_offer import JobOffer
    from app.nlp.embeddings.generator import generate_embedding, normalize_text

    session_factory = _get_sync_session()

    with session_factory() as db:
        offer = db.get(JobOffer, job_offer_id)
        if not offer:
            logger.warning("job_offer_not_found_for_embedding", job_offer_id=job_offer_id)
            return

        skills_str = ", ".join(offer.required_skills or [])
        text = (
            f"{offer.title} | {offer.modality} | {offer.district or ''} | "
            f"skills requeridas: {skills_str} | {offer.description[:500]}"
        )
        normalized = normalize_text(text)
        offer.embedding = generate_embedding(normalized)
        db.commit()

    logger.info("job_embedding_generated", job_offer_id=job_offer_id)


@app.task(name="generate_portfolio_entry_embedding", queue="embeddings")
def generate_portfolio_entry_embedding(entry_id: str) -> None:
    if not _validate_uuid(entry_id, "entry_id"):
        return  # Silenced — invalid input, do not retry
    from app.models.portfolio import PortfolioEntry
    from app.nlp.embeddings.generator import generate_embedding

    session_factory = _get_sync_session()

    with session_factory() as db:
        entry = db.get(PortfolioEntry, entry_id)
        if not entry:
            logger.warning("portfolio_entry_not_found_for_embedding", entry_id=entry_id)
            return

        skills_str = ", ".join(entry.extracted_skills or [])
        text = f"{entry.title} | habilidades: {skills_str} | {entry.description[:300]}"
        entry.embedding = generate_embedding(text)
        db.commit()

    logger.info("portfolio_entry_embedding_generated", entry_id=entry_id)


@app.task(name="generate_listing_embedding", queue="embeddings")
def generate_listing_embedding(listing_id: str) -> None:
    if not _validate_uuid(listing_id, "listing_id"):
        return
    from app.models.service_listing import ServiceListing
    from app.nlp.embeddings.generator import generate_embedding

    session_factory = _get_sync_session()

    with session_factory() as db:
        listing = db.get(ServiceListing, listing_id)
        if not listing:
            logger.warning("listing_not_found_for_embedding", listing_id=listing_id)
            return

        keywords_str = ", ".join(listing.enriched_keywords or [])
        text = f"{listing.trade_category} | {listing.title} | habilidades: {keywords_str} | {listing.description[:400]}"
        from app.nlp.embeddings.generator import apply_local_dictionary
        text = apply_local_dictionary(text)
        listing.embedding = generate_embedding(text)
        db.commit()

    logger.info("listing_embedding_generated", listing_id=listing_id)


@app.task(name="regenerate_all_embeddings", queue="embeddings")
def regenerate_all_embeddings(worker_type: str = "all") -> None:
    from app.models.worker import Worker

    session_factory = _get_sync_session()
    batch_size = 50

    with session_factory() as db:
        query = select(Worker)
        if worker_type != "all":
            query = query.where(Worker.worker_type == worker_type)

        workers = db.execute(query).scalars().all()
        total = len(workers)
        processed = 0

        for i in range(0, total, batch_size):
            batch = workers[i : i + batch_size]
            if processed % 100 == 0:
                logger.info("regenerate_progress", processed=processed, total=total)

            for w in batch:
                generate_worker_embedding.apply(args=[w.id])
                processed += 1

    logger.info("regenerate_all_embeddings_complete", worker_type=worker_type, total=total)
