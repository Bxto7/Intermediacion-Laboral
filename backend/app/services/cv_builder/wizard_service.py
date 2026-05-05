# RF: RF096-RF100
from datetime import UTC, datetime

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wizard import WizardProgress
from app.nlp.skill_extractor.first_job_extractor import (
    extract_skills_from_wizard_answer,
    suggest_job_sectors,
)

logger = structlog.get_logger()


async def get_or_create_wizard(worker_id: str, db: AsyncSession) -> WizardProgress:
    result = await db.execute(
        select(WizardProgress).where(WizardProgress.worker_id == worker_id)
    )
    wizard = result.scalar_one_or_none()
    if wizard is None:
        wizard = WizardProgress(
            worker_id=worker_id,
            current_step=1,
            answers={},
            extracted_skills=[],
            job_interests=[],
        )
        db.add(wizard)
        await db.flush()
    return wizard


async def save_wizard_step(
    worker_id: str, step: int, step_data: dict, db: AsyncSession
) -> WizardProgress:
    if not 1 <= step <= 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El paso debe estar entre 1 y 6",
        )

    wizard = await get_or_create_wizard(worker_id, db)

    if step > wizard.current_step + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No puedes saltar al paso {step} sin completar el paso {wizard.current_step}",
        )

    accumulated_skills = list(wizard.extracted_skills or [])

    if step in (3, 4):
        text = step_data.get("text", "")
        if text:
            new_skills = extract_skills_from_wizard_answer(text, step)
            for s in new_skills:
                if s not in accumulated_skills:
                    accumulated_skills.append(s)
            wizard.extracted_skills = accumulated_skills

    if step == 5:
        interests = step_data.get("interests", [])
        if isinstance(interests, list):
            wizard.job_interests = interests

    answers = dict(wizard.answers or {})
    answers[str(step)] = step_data
    wizard.answers = answers
    wizard.current_step = max(wizard.current_step, step)
    wizard.last_saved_at = datetime.now(tz=UTC)

    if wizard.current_step == 6:
        from app.tasks.embeddings import generate_worker_embedding
        generate_worker_embedding.delay(worker_id)
        logger.info("wizard_complete_embedding_queued", worker_id=worker_id)

    await db.commit()
    await db.refresh(wizard)
    return wizard


async def get_wizard_summary(worker_id: str, db: AsyncSession) -> dict:
    from app.core.security import decrypt_field
    from app.models.worker import Worker

    result = await db.execute(
        select(WizardProgress).where(WizardProgress.worker_id == worker_id)
    )
    wizard = result.scalar_one_or_none()
    if not wizard or wizard.current_step < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El wizard no esta completo. Completa todos los pasos primero.",
        )

    worker_result = await db.execute(
        select(Worker).where(Worker.id == worker_id)
    )
    worker = worker_result.scalar_one_or_none()

    full_name = ""
    if worker and worker.full_name:
        try:
            full_name = decrypt_field(worker.full_name)
        except Exception:
            full_name = ""

    answers = wizard.answers or {}
    step1 = answers.get("1", {})
    step2 = answers.get("2", {})

    skills = wizard.extracted_skills or []
    interests = wizard.job_interests or []
    suggested_sectors = suggest_job_sectors(skills)

    return {
        "full_name": full_name,
        "district": worker.district if worker else step1.get("district", ""),
        "education": step2,
        "skills": skills,
        "interests": interests,
        "suggested_sectors": suggested_sectors,
    }
