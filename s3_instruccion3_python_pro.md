# SPRINT 3 — INSTRUCCIÓN 3 de 5
# Agente: `python-pro`
# Skills a cargar: `skills/python-fastapi`, `skills/senior-backend`
# Tarea: Generación de CVs PDF (WeasyPrint, 3 plantillas) + Notificaciones WebSocket + Alertas de empleo

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
Las instrucciones 1 y 2 del Sprint 3 ya entregaron:
- Seguridad hardened (file_validator, security_headers, match_events table)
- Motor de matching M05 completo (engine, scorer, cold_start, equity_ranker, explainer)

**Tu trabajo:** Implementar la generación de CVs PDF con WeasyPrint (3 plantillas diferenciadas),
el sistema de notificaciones en tiempo real vía WebSocket con Redis pub/sub, y las alertas
configurables de empleo.

**RF que implementas:**
- RF096–RF110 (M06): CV generado desde wizard (primer_empleo) y desde portfolio (oficio)
- RF126–RF135 (M08): Notificaciones en tiempo real
- RF111–RF117 (M07 parcial): Alertas de empleo configurables

---

## PARTE A — GENERACIÓN DE CVs PDF (WeasyPrint)

### A1 — Migraciones

```bash
alembic revision --autogenerate -m "add cv_templates and job_alerts tables sprint3"
alembic upgrade head
```

**Tablas nuevas:**
```sql
-- Alertas de empleo configurables
CREATE TABLE job_alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    worker_type     VARCHAR(20) NOT NULL,
    keywords        JSONB DEFAULT '[]',         -- ["programador", "técnico"]
    districts       JSONB DEFAULT '[]',         -- ["Huancayo", "El Tambo"]
    trade_categories JSONB DEFAULT '[]',        -- solo OFICIO
    salary_min      DECIMAL(10,2),
    is_active       BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Notificaciones del sistema
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    worker_type     VARCHAR(20),
    notification_type VARCHAR(50) NOT NULL,    -- 'new_match', 'application_update', 'alert_job', 'message'
    title           VARCHAR(200) NOT NULL,
    body            TEXT NOT NULL,
    payload         JSONB DEFAULT '{}',        -- datos adicionales (job_id, etc.)
    is_read         BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON notifications (user_id, is_read, created_at DESC);
CREATE INDEX ON job_alerts (worker_id, is_active);
```

### A2 — Plantillas HTML para CVs (3 plantillas diferenciadas)

Crea la carpeta `app/utils/cv_templates/` con 3 archivos HTML + CSS inline:

**`app/utils/cv_templates/primer_empleo.html`**
```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  /* Paleta amigable y motivadora para jóvenes sin experiencia */
  body { font-family: 'Arial', sans-serif; margin: 0; color: #2d3748; font-size: 11pt; }
  .header { background: #4299e1; color: white; padding: 24px 32px; }
  .header h1 { margin: 0; font-size: 22pt; }
  .header .subtitle { font-size: 10pt; opacity: 0.9; margin-top: 4px; }
  .contact-bar { background: #ebf8ff; padding: 8px 32px; font-size: 9pt; color: #2b6cb0; }
  .section { padding: 16px 32px; border-bottom: 1px solid #e2e8f0; }
  .section h2 { color: #4299e1; font-size: 13pt; margin-bottom: 8px; border-left: 4px solid #4299e1; padding-left: 8px; }
  .skill-tag { display: inline-block; background: #bee3f8; color: #2b6cb0; padding: 2px 8px; border-radius: 4px; margin: 2px; font-size: 9pt; }
  .activity { margin-bottom: 8px; }
  .activity strong { color: #2d3748; }
  .footer { text-align: center; font-size: 8pt; color: #a0aec0; padding: 16px; }
  .badge { background: #c6f6d5; color: #276749; padding: 2px 8px; border-radius: 4px; font-size: 9pt; display: inline-block; }
</style>
</head>
<body>
  <div class="header">
    <h1>{{ full_name }}</h1>
    <div class="subtitle">En búsqueda de mi primer empleo · {{ district }}, Junín</div>
  </div>
  <div class="contact-bar">
    📱 {{ phone }} &nbsp;|&nbsp; ✉️ {{ email }}
    {% if linkedin %}&nbsp;|&nbsp; 🔗 {{ linkedin }}{% endif %}
  </div>
  {% if objective %}
  <div class="section">
    <h2>Objetivo Profesional</h2>
    <p>{{ objective }}</p>
  </div>
  {% endif %}
  <div class="section">
    <h2>Habilidades</h2>
    {% for skill in skills %}
    <span class="skill-tag">{{ skill }}</span>
    {% endfor %}
  </div>
  <div class="section">
    <h2>Educación</h2>
    {% for edu in education %}
    <div class="activity">
      <strong>{{ edu.institution }}</strong> — {{ edu.degree }}<br>
      <span style="color:#718096">{{ edu.period }}</span>
    </div>
    {% endfor %}
  </div>
  {% if activities %}
  <div class="section">
    <h2>Actividades y Experiencias Previas</h2>
    {% for act in activities %}
    <div class="activity">
      <strong>{{ act.title }}</strong><br>
      {{ act.description }}
    </div>
    {% endfor %}
  </div>
  {% endif %}
  <div class="footer">
    CV generado por el Sistema de Intermediación Laboral · DRTPE-Junín
    <span class="badge">✅ Identidad verificada DRTPE</span>
  </div>
</body>
</html>
```

**`app/utils/cv_templates/oficio.html`**
```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  /* Diseño profesional y robusto para trabajadores de oficio */
  body { font-family: 'Arial', sans-serif; margin: 0; color: #1a202c; font-size: 11pt; }
  .header { background: #744210; color: white; padding: 24px 32px; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { margin: 0; font-size: 20pt; }
  .trade-badge { background: #f6ad55; color: #744210; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 10pt; }
  .rating { color: #f6ad55; font-size: 16pt; }
  .contact-bar { background: #fefcbf; padding: 8px 32px; font-size: 9pt; }
  .section { padding: 16px 32px; border-bottom: 1px solid #e2e8f0; }
  .section h2 { color: #744210; font-size: 12pt; border-left: 4px solid #f6ad55; padding-left: 8px; margin-bottom: 10px; }
  .job-card { background: #fffbeb; border: 1px solid #f6e05e; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; }
  .job-card .title { font-weight: bold; color: #744210; }
  .skill-tag { display: inline-block; background: #fefcbf; color: #744210; padding: 2px 8px; border-radius: 4px; margin: 2px; font-size: 9pt; border: 1px solid #f6e05e; }
  .stars { color: #f6ad55; }
  .footer { text-align: center; font-size: 8pt; color: #a0aec0; padding: 16px; }
  .availability { display: inline-block; background: #c6f6d5; color: #276749; padding: 2px 10px; border-radius: 10px; font-size: 9pt; }
</style>
</head>
<body>
  <div class="header">
    <div>
      <h1>{{ full_name }}</h1>
      <div style="margin-top:4px;font-size:10pt;opacity:0.85">{{ district }}, Junín</div>
    </div>
    <div style="text-align:right">
      <div class="trade-badge">{{ trade_category }}</div>
      <div class="rating" style="margin-top:6px">{{ stars }}</div>
      <div style="font-size:9pt;opacity:0.85">{{ avg_rating }}/5.0 · {{ portfolio_count }} trabajos</div>
    </div>
  </div>
  <div class="contact-bar">
    📱 {{ phone }} &nbsp;|&nbsp; ✉️ {{ email }}
    &nbsp;|&nbsp; 🌐 drtpe.gob.pe/p/{{ slug }}
    <span class="availability">{{ availability_text }}</span>
  </div>
  <div class="section">
    <h2>Habilidades del Oficio</h2>
    {% for skill in skills %}
    <span class="skill-tag">{{ skill }}</span>
    {% endfor %}
  </div>
  {% if portfolio_entries %}
  <div class="section">
    <h2>Trabajos Realizados</h2>
    {% for entry in portfolio_entries %}
    <div class="job-card">
      <div class="title">{{ entry.title }}</div>
      <div style="font-size:9pt;color:#718096;margin-top:2px">{{ entry.period }}</div>
      <div style="margin-top:4px;font-size:10pt">{{ entry.description }}</div>
      {% if entry.client_rating %}
      <div class="stars">{{ entry.stars }} {{ entry.client_rating }}/5.0</div>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}
  <div class="section">
    <h2>Experiencia</h2>
    <p>{{ years_experience }} años de experiencia como {{ trade_category }} en la región Junín.</p>
  </div>
  <div class="footer">
    CV generado por el Sistema de Intermediación Laboral · DRTPE-Junín
    <span style="background:#c6f6d5;color:#276749;padding:2px 8px;border-radius:4px;">✅ Identidad verificada DNI</span>
  </div>
</body>
</html>
```

**`app/utils/cv_templates/experiencia.html`**
```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  /* Diseño profesional estilo bolsa de trabajo */
  body { font-family: 'Arial', sans-serif; margin: 0; color: #2d3748; font-size: 11pt; }
  .header { background: #2d3748; color: white; padding: 24px 32px; }
  .header h1 { margin: 0; font-size: 20pt; }
  .header .title { font-size: 12pt; color: #a0aec0; margin-top: 4px; }
  .contact-bar { background: #edf2f7; padding: 8px 32px; font-size: 9pt; color: #4a5568; }
  .section { padding: 16px 32px; border-bottom: 1px solid #e2e8f0; }
  .section h2 { font-size: 11pt; text-transform: uppercase; letter-spacing: 1px; color: #718096; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; margin-bottom: 10px; }
  .exp-entry { margin-bottom: 12px; }
  .exp-entry .role { font-weight: bold; color: #2d3748; }
  .exp-entry .company { color: #4a5568; }
  .exp-entry .period { font-size: 9pt; color: #a0aec0; }
  .exp-entry .tasks { margin-top: 4px; color: #4a5568; }
  .skill-tag { display: inline-block; background: #edf2f7; color: #4a5568; padding: 2px 8px; border-radius: 4px; margin: 2px; font-size: 9pt; }
</style>
</head>
<body>
  <div class="header">
    <h1>{{ full_name }}</h1>
    <div class="title">{{ job_title }}</div>
    <div style="font-size:9pt;color:#a0aec0;margin-top:2px">{{ years_experience }} años de experiencia · {{ district }}, Junín</div>
  </div>
  <div class="contact-bar">
    📱 {{ phone }} &nbsp;|&nbsp; ✉️ {{ email }}
    {% if linkedin %}&nbsp;|&nbsp; 🔗 {{ linkedin }}{% endif %}
  </div>
  {% if bio %}
  <div class="section">
    <h2>Perfil Profesional</h2>
    <p>{{ bio }}</p>
  </div>
  {% endif %}
  <div class="section">
    <h2>Experiencia Laboral</h2>
    {% for exp in experiences %}
    <div class="exp-entry">
      <div class="role">{{ exp.role }}</div>
      <div class="company">{{ exp.company }}</div>
      <div class="period">{{ exp.period }}</div>
      <div class="tasks">{{ exp.tasks }}</div>
    </div>
    {% endfor %}
  </div>
  <div class="section">
    <h2>Educación</h2>
    {% for edu in education %}
    <div class="exp-entry">
      <strong>{{ edu.institution }}</strong> — {{ edu.degree }}<br>
      <span style="color:#a0aec0">{{ edu.period }}</span>
    </div>
    {% endfor %}
  </div>
  <div class="section">
    <h2>Habilidades</h2>
    {% for skill in skills %}
    <span class="skill-tag">{{ skill }}</span>
    {% endfor %}
  </div>
</body>
</html>
```

### A3 — Servicio de generación de CVs

Crea `app/services/cv_builder/pdf_generator.py`:

```python
# app/services/cv_builder/pdf_generator.py
"""
Generación de CVs PDF con WeasyPrint.
3 plantillas diferenciadas por WorkerType.
Cubre RF096–RF110 (M06).
"""
from pathlib import Path
from uuid import UUID
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.types import WorkerType
from app.models import Worker, WizardProgress, PortfolioEntry, GeneratedCV
from app.core.config import settings
from app.core.encryption import decrypt_field

logger = structlog.get_logger()

TEMPLATES_DIR = Path("app/utils/cv_templates")
TEMPLATE_MAP = {
    WorkerType.PRIMER_EMPLEO: "primer_empleo.html",
    WorkerType.OFICIO:        "oficio.html",
    WorkerType.EXPERIENCIA:   "experiencia.html",
}


async def generate_cv_pdf(
    worker_id: UUID,
    db: AsyncSession,
) -> bytes:
    """
    Genera el PDF del CV para el trabajador según su tipo.
    Retorna bytes del PDF para subir a GCS/S3.
    Cubre RF096–RF110.
    """
    # Cargar worker
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise ValueError(f"Worker {worker_id} no encontrado")

    worker_type = WorkerType(worker.worker_type)
    template_file = TEMPLATE_MAP[worker_type]

    # Construir contexto del template según tipo
    context = await _build_template_context(worker, worker_type, db)

    # Renderizar HTML con Jinja2
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(template_file)
    html_content = template.render(**context)

    # Generar PDF con WeasyPrint
    pdf_bytes = HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()

    logger.info(
        "cv_pdf_generated",
        worker_id=str(worker_id),
        worker_type=worker.worker_type,
        size_bytes=len(pdf_bytes),
    )

    return pdf_bytes


async def _build_template_context(
    worker: Worker,
    worker_type: WorkerType,
    db: AsyncSession,
) -> dict:
    """Construye el contexto del template según el tipo de trabajador."""
    # Descifrar datos sensibles para el PDF (NO para logs)
    full_name = decrypt_field(worker.full_name)
    phone = decrypt_field(worker.phone) if worker.phone else ""

    base_ctx = {
        "full_name": full_name,
        "phone": phone,
        "email": worker.email,          # email no cifrado (FK a users)
        "district": worker.district,
    }

    if worker_type == WorkerType.PRIMER_EMPLEO:
        # Cargar datos del wizard
        res = await db.execute(
            select(WizardProgress).where(WizardProgress.worker_id == worker.id)
        )
        progress = res.scalar_one_or_none()
        answers = progress.answers if progress else {}
        skills = progress.extracted_skills if progress else []

        return {**base_ctx,
            "skills": skills,
            "education": answers.get("education", []),
            "activities": answers.get("activities", []),
            "objective": answers.get("job_interests", ""),
            "linkedin": answers.get("linkedin", ""),
        }

    elif worker_type == WorkerType.OFICIO:
        # Cargar portfolio entries
        res = await db.execute(
            select(PortfolioEntry)
            .where(PortfolioEntry.worker_id == worker.id, PortfolioEntry.is_public == True)
            .order_by(PortfolioEntry.period_start.desc())
            .limit(6)
        )
        entries = res.scalars().all()
        all_skills = []
        for entry in entries:
            all_skills.extend(entry.extracted_skills or [])

        # Estrellas visuales
        stars = "★" * round(worker.avg_rating or 0) + "☆" * (5 - round(worker.avg_rating or 0))
        availability_text = {
            "inmediata": "✅ Disponible ahora",
            "semana":    "📅 Disponible esta semana",
            "mes":       "🗓️ Disponible este mes",
        }.get(getattr(worker, "availability", "inmediata"), "✅ Disponible")

        return {**base_ctx,
            "trade_category": worker.trade_category,
            "years_experience": worker.years_experience,
            "avg_rating": f"{worker.avg_rating:.1f}" if worker.avg_rating else "N/A",
            "portfolio_count": len(entries),
            "stars": stars,
            "slug": getattr(worker, "slug", ""),
            "availability_text": availability_text,
            "skills": list(set(all_skills))[:12],
            "portfolio_entries": [
                {
                    "title": e.title,
                    "description": e.description[:200],
                    "period": f"{e.period_start} – {e.period_end or 'actualidad'}" if e.period_start else "",
                    "client_rating": e.client_rating,
                    "stars": "★" * round(e.client_rating or 0) if e.client_rating else "",
                }
                for e in entries
            ],
        }

    else:  # EXPERIENCIA
        profile = getattr(worker, "profile_data", {}) or {}
        return {**base_ctx,
            "job_title": profile.get("job_title", "Profesional"),
            "years_experience": worker.years_experience,
            "bio": profile.get("bio", ""),
            "experiences": profile.get("experiences", []),
            "education": profile.get("education", []),
            "skills": profile.get("skills", []),
            "linkedin": profile.get("linkedin", ""),
        }
```

### A4 — Endpoint de generación de CV

```python
# En app/api/v1/cv.py — agregar endpoint:
@router.post("/api/v1/cv/generate/{worker_id}", response_model=GeneratedCVResponse)
async def generate_cv(
    worker_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """RF096–RF110: Generar CV PDF para el trabajador según su tipo."""
    # Verificar ownership
    ...
    # Encolar en Celery (asíncrono — no bloquear el request)
    from app.tasks.cv_generator import generate_cv_task
    task = generate_cv_task.delay(str(worker_id))
    return GeneratedCVResponse(task_id=task.id, status="processing")
```

---

## PARTE B — NOTIFICACIONES WEBSOCKET + REDIS PUB/SUB

Crea `app/api/v1/ws_notifications.py`:

```python
# app/api/v1/ws_notifications.py
"""
Notificaciones en tiempo real vía WebSocket con Redis pub/sub.
Cubre RF126–RF135 (M08).
"""
import json
import asyncio
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from redis.asyncio import Redis
import structlog

from app.core.db import get_redis
from app.core.security import verify_ws_token

router = APIRouter(tags=["notifications"])
logger = structlog.get_logger()

# Canal Redis por usuario: "notifications:{user_id}"
CHANNEL_PREFIX = "notifications:"


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: UUID,
    token: str,   # query param: ?token=...
    redis: Redis = Depends(get_redis),
):
    """
    WebSocket de notificaciones en tiempo real.
    El cliente se suscribe al canal del usuario.
    El servidor publica notificaciones cuando ocurren eventos.
    """
    # Verificar JWT por query param (WebSocket no tiene headers estándar)
    user = await verify_ws_token(token)
    if not user or user.id != user_id:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    channel = f"{CHANNEL_PREFIX}{user_id}"

    logger.info("ws_connected", user_id=str(user_id))

    # Suscribir a canal Redis
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    try:
        # Escuchar mensajes de Redis y enviar al WebSocket
        async def redis_listener():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode()
                    await websocket.send_text(data)

        # Escuchar pings del cliente (keepalive)
        async def ws_listener():
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                    if msg == "ping":
                        await websocket.send_text("pong")
                except asyncio.TimeoutError:
                    pass

        await asyncio.gather(redis_listener(), ws_listener())

    except WebSocketDisconnect:
        logger.info("ws_disconnected", user_id=str(user_id))
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


async def publish_notification(
    user_id: UUID,
    notification_type: str,
    title: str,
    body: str,
    payload: dict,
    redis: Redis,
):
    """
    Publicar notificación al canal Redis del usuario.
    Llamar desde cualquier servicio cuando ocurra un evento relevante.
    Tipos: 'new_match', 'application_update', 'alert_job', 'message'
    """
    channel = f"{CHANNEL_PREFIX}{user_id}"
    message = json.dumps({
        "type": notification_type,
        "title": title,
        "body": body,
        "payload": payload,
    })
    await redis.publish(channel, message)
    logger.info(
        "notification_published",
        user_id=str(user_id),
        notification_type=notification_type,
    )
```

---

## PARTE C — ALERTAS DE EMPLEO CONFIGURABLES

Crea `app/services/matching/job_alerts.py`:

```python
# app/services/matching/job_alerts.py
"""
Sistema de alertas configurables de empleo.
Cubre RF111–RF117 (M07 parcial).
Tarea Celery programada: verificar alertas cada hora.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models import JobAlert, Worker, JobOffer, Notification
from app.tasks.notifications import notify_user_task

logger = structlog.get_logger()


async def create_job_alert(
    worker_id: UUID,
    keywords: list[str],
    districts: list[str],
    trade_categories: list[str],
    salary_min: float | None,
    db: AsyncSession,
) -> JobAlert:
    """RF111: Crear alerta de empleo configurable para el trabajador."""
    import uuid
    # Cargar worker para verificar tipo
    res = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = res.scalar_one_or_none()
    if not worker:
        raise ValueError(f"Worker {worker_id} no encontrado")

    alert = JobAlert(
        id=uuid.uuid4(),
        worker_id=worker_id,
        worker_type=worker.worker_type,
        keywords=keywords,
        districts=districts,
        trade_categories=trade_categories,
        salary_min=salary_min,
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    logger.info("job_alert_created", worker_id=str(worker_id), keywords=keywords)
    return alert


async def process_alerts_for_new_offer(
    offer: JobOffer,
    db: AsyncSession,
    redis,
):
    """
    Verificar qué alertas activas coinciden con una nueva oferta publicada.
    Llamar desde el endpoint de publicación de oferta (M03).
    """
    from app.api.v1.ws_notifications import publish_notification

    res = await db.execute(
        select(JobAlert).where(JobAlert.is_active == True)
    )
    alerts = res.scalars().all()

    for alert in alerts:
        if _alert_matches_offer(alert, offer):
            # Crear notificación en BD
            import uuid
            notif = Notification(
                id=uuid.uuid4(),
                user_id=alert.worker.user_id,
                worker_type=alert.worker_type,
                notification_type="alert_job",
                title="Nueva oferta que te podría interesar",
                body=f"Se publicó: {offer.title} en {offer.district}",
                payload={"job_id": str(offer.id)},
            )
            db.add(notif)

            # Publicar en WebSocket
            await publish_notification(
                user_id=alert.worker.user_id,
                notification_type="alert_job",
                title="Nueva oferta disponible",
                body=f"{offer.title} · {offer.district}",
                payload={"job_id": str(offer.id)},
                redis=redis,
            )

    await db.commit()


def _alert_matches_offer(alert: JobAlert, offer: JobOffer) -> bool:
    """Verificar si una oferta coincide con los criterios de una alerta."""
    # Keywords (texto en título o descripción)
    if alert.keywords:
        offer_text = f"{offer.title} {offer.description}".lower()
        if not any(kw.lower() in offer_text for kw in alert.keywords):
            return False

    # Distrito
    if alert.districts and offer.district not in alert.districts:
        return False

    # Categoría de oficio (solo alertas OFICIO)
    if alert.trade_categories and hasattr(offer, "trade_category"):
        if offer.trade_category not in alert.trade_categories:
            return False

    # Salario mínimo
    if alert.salary_min and offer.salary_min:
        if offer.salary_min < alert.salary_min:
            return False

    return True
```

---

## PARTE D — TAREA CELERY PARA GENERACIÓN DE CVs

```python
# app/tasks/cv_generator.py — actualizar con la tarea real
from celery import shared_task
import uuid as uuid_mod
import structlog

logger = structlog.get_logger()


@shared_task(name="tasks.generate_cv", bind=True, max_retries=3)
def generate_cv_task(self, worker_id: str):
    """
    Tarea asíncrona: generar CV PDF y subir a GCS/S3.
    Notificar al usuario cuando esté listo.
    """
    # Validar UUID
    try:
        validated_id = uuid_mod.UUID(worker_id, version=4)
    except ValueError:
        logger.error("invalid_uuid_cv_task", worker_id=worker_id)
        return

    import asyncio
    from app.core.db import get_db_sync
    from app.services.cv_builder.pdf_generator import generate_cv_pdf
    from app.services.storage import upload_to_gcs
    from app.models import GeneratedCV

    try:
        # Generar PDF
        pdf_bytes = asyncio.run(generate_cv_pdf_sync(str(validated_id)))

        # Subir a GCS (URL con expiración 60 min — regla de seguridad)
        file_url = upload_to_gcs(
            content=pdf_bytes,
            filename=f"cvs/{worker_id}/cv_{uuid_mod.uuid4()}.pdf",
            content_type="application/pdf",
            expiration_minutes=60,
        )

        logger.info("cv_generated_and_uploaded", worker_id=worker_id, url=file_url[:50])

        # Notificar al usuario (publicar en Redis)
        # notify_user_task.delay(worker_id, "cv_ready", file_url)

    except Exception as exc:
        logger.error("cv_generation_failed", worker_id=worker_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)
```

---

## TESTS OBLIGATORIOS

```bash
# Crear archivos de test
touch tests/unit/test_cv_generator.py
touch tests/integration/test_api_cv.py
touch tests/integration/test_websocket_notifications.py
touch tests/integration/test_job_alerts.py
```

**`tests/unit/test_cv_generator.py`** debe cubrir:
- `generate_cv_pdf()` retorna bytes > 0 para los 3 tipos
- `_build_template_context()` no incluye DNI ni teléfono cifrado en texto plano
- Template PRIMER_EMPLEO con wizard vacío no lanza excepción
- Template OFICIO con portfolio de 0 entradas no lanza excepción

**`tests/integration/test_websocket_notifications.py`** debe cubrir:
- Conexión WebSocket sin token → cierra con código 4001
- Conexión con token válido → acepta
- `publish_notification()` llega al WebSocket conectado (con mock de Redis)

```bash
# Ejecutar
pytest tests/unit/test_cv_generator.py tests/integration/test_api_cv.py \
       tests/integration/test_websocket_notifications.py -v

# Sin print()
grep -rn "print(" app/services/cv_builder/ app/api/v1/ws_notifications.py

# Linting
ruff check app/services/cv_builder/ app/api/v1/ws_notifications.py app/services/matching/job_alerts.py
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `app/utils/cv_templates/primer_empleo.html`
- `app/utils/cv_templates/oficio.html`
- `app/utils/cv_templates/experiencia.html`
- `app/services/cv_builder/pdf_generator.py`
- `app/api/v1/ws_notifications.py`
- `app/services/matching/job_alerts.py`
- `app/tasks/cv_generator.py` (actualizado con tarea real)
- `app/api/v1/cv.py` (endpoint generate)
- `app/api/v1/alerts.py` (CRUD de alertas)
- `alembic/versions/XXXX_add_notifications_alerts_tables.py`
- `requirements.txt` actualizado: `weasyprint`, `jinja2`, `redis[asyncio]`
- Tests

---

**Cuando termines, el agente `devops-engineer` recibirá la instrucción 4
para configurar Celery Beat, docker-compose multi-worker y monitoreo Prometheus+Grafana.**
