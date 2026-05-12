# SPRINT 5 — INSTRUCCIÓN 2 de 6
# Agente: `python-pro`
# Skills a cargar: `skills/python-fastapi`, `skills/senior-backend`
# Tarea: Moderación de marketplace + RF faltantes (RF23, RF34, RF124/125, RF150) + seed realista

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
La instrucción 1 del Sprint 5 cerró la auditoría de seguridad y creó SECURITY_AUDIT.md.

**RF que implementas:**
- RF023 (M02): Cambio de tipo de usuario con confirmación
- RF034 (M02): Eliminación de cuenta con soft-delete
- RF118–RF125 (M07): Moderación del marketplace (ban/unban de listings)
- RF124/RF125 (M07): Contratos desde marketplace
- RF150 (M10): Estado de equidad visible al usuario

---

## PARTE A — Moderación del marketplace (M07 / RF118–RF125)

### A1 — Migración: tabla de flags de contenido

```bash
alembic revision --autogenerate -m "add content_flags moderation sprint5"
alembic upgrade head
```

```sql
CREATE TABLE content_flags (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id      UUID NOT NULL REFERENCES service_listings(id),
    reported_by     UUID NOT NULL REFERENCES users(id),
    reason          VARCHAR(50) NOT NULL,   -- 'spam', 'falso', 'ofensivo', 'otro'
    details         TEXT,
    status          VARCHAR(20) DEFAULT 'pending', -- 'pending', 'resolved', 'dismissed'
    resolved_by     UUID REFERENCES users(id),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON content_flags (listing_id, status);
CREATE INDEX ON content_flags (status, created_at DESC);
```

### A2 — Endpoints de moderación

Crea `app/api/v1/moderation.py`:

```python
# app/api/v1/moderation.py
"""
Moderación de contenido del marketplace.
WORKER puede reportar listings. MODERATOR/ADMIN pueden banear/desbanear.
Cubre RF118–RF125 (M07 — moderación de marketplace).
"""
from uuid import UUID
import uuid as uuid_mod
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import get_db
from app.core.security import require_role, UserRole
from app.models import ContentFlag, ServiceListing, User
from app.schemas.moderation import FlagCreate, FlagResponse, ModerationQueueResponse
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/moderation", tags=["moderation"])


@router.post("/listings/{listing_id}/flag", response_model=FlagResponse)
async def flag_listing(
    listing_id: UUID,
    data: FlagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """Reportar un listing del marketplace por contenido inapropiado."""
    # Verificar que el listing existe
    res = await db.execute(select(ServiceListing).where(ServiceListing.id == listing_id))
    listing = res.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing no encontrado")

    # Un usuario no puede reportar su propio listing
    if listing.worker.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes reportar tu propio servicio")

    flag = ContentFlag(
        id=uuid_mod.uuid4(),
        listing_id=listing_id,
        reported_by=current_user.id,
        reason=data.reason,
        details=data.details,
        status="pending",
    )
    db.add(flag)
    await db.commit()

    logger.info("listing_flagged", listing_id=str(listing_id), reason=data.reason)
    return FlagResponse(id=flag.id, status=flag.status)


@router.get("/queue", response_model=ModerationQueueResponse)
async def get_moderation_queue(
    status: str = "pending",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MODERATOR)),
):
    """
    Cola de moderación — solo MODERATOR y ADMIN.
    Lista los flags pendientes de revisión.
    """
    res = await db.execute(
        select(ContentFlag)
        .where(ContentFlag.status == status)
        .order_by(ContentFlag.created_at.asc())
        .limit(50)
    )
    flags = res.scalars().all()
    return ModerationQueueResponse(flags=flags, total=len(flags))


@router.post("/listings/{listing_id}/ban")
async def ban_listing(
    listing_id: UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MODERATOR)),
):
    """Desactivar un listing por violación de términos."""
    res = await db.execute(select(ServiceListing).where(ServiceListing.id == listing_id))
    listing = res.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing no encontrado")

    listing.is_active = False
    listing.ban_reason = reason
    listing.banned_at = __import__('datetime').datetime.utcnow()
    listing.banned_by = current_user.id

    await db.commit()
    logger.info("listing_banned", listing_id=str(listing_id), reason=reason, by=str(current_user.id))
    return {"status": "banned", "listing_id": str(listing_id)}


@router.post("/listings/{listing_id}/unban")
async def unban_listing(
    listing_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MODERATOR)),
):
    """Reactivar un listing que fue baneado incorrectamente."""
    res = await db.execute(select(ServiceListing).where(ServiceListing.id == listing_id))
    listing = res.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing no encontrado")

    listing.is_active = True
    listing.ban_reason = None
    listing.banned_at = None
    listing.banned_by = None
    await db.commit()

    logger.info("listing_unbanned", listing_id=str(listing_id), by=str(current_user.id))
    return {"status": "active", "listing_id": str(listing_id)}
```

---

## PARTE B — RF023: Cambio de tipo de usuario

```python
# En app/api/v1/workers.py — agregar endpoint:

@router.post("/api/v1/workers/{worker_id}/change-type")
async def request_type_change(
    worker_id: UUID,
    new_type: WorkerType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """
    RF023: Cambio de tipo de usuario con solicitud explícita y confirmación.
    El CLAUDE.md establece: "cambiar el tipo solo es posible con solicitud
    explícita del usuario y confirmación".
    
    En esta implementación: crea una solicitud pendiente de confirmación
    por email. El usuario debe confirmar en 24h.
    """
    res = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = res.scalar_one_or_none()
    if not worker or worker.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin autorización")

    if worker.worker_type == new_type.value:
        raise HTTPException(status_code=400, detail="Ya tienes este tipo de perfil")

    # Crear solicitud de cambio pendiente (no cambiar directamente)
    import uuid as uuid_mod
    from app.models import TypeChangeRequest
    request = TypeChangeRequest(
        id=uuid_mod.uuid4(),
        worker_id=worker_id,
        current_type=worker.worker_type,
        requested_type=new_type.value,
        status="pending_confirmation",
        expires_at=__import__('datetime').datetime.utcnow() + __import__('datetime').timedelta(hours=24),
    )
    db.add(request)
    await db.commit()

    # Enviar email de confirmación (tarea Celery)
    # send_type_change_confirmation_email.delay(str(current_user.id), str(request.id))

    logger.info(
        "type_change_requested",
        worker_id=str(worker_id),
        from_type=worker.worker_type,
        to_type=new_type.value,
    )
    return {
        "message": "Solicitud registrada. Revisa tu email para confirmar el cambio.",
        "request_id": str(request.id),
        "expires_in_hours": 24,
    }


@router.post("/api/v1/workers/change-type/confirm/{request_id}")
async def confirm_type_change(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """Confirmar el cambio de tipo via enlace del email."""
    from app.models import TypeChangeRequest
    res = await db.execute(
        select(TypeChangeRequest).where(
            TypeChangeRequest.id == request_id,
            TypeChangeRequest.status == "pending_confirmation",
        )
    )
    change_req = res.scalar_one_or_none()
    if not change_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada o expirada")

    if change_req.expires_at < __import__('datetime').datetime.utcnow():
        change_req.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="La solicitud de cambio ha expirado")

    # Aplicar el cambio
    res = await db.execute(select(Worker).where(Worker.id == change_req.worker_id))
    worker = res.scalar_one_or_none()
    worker.worker_type = change_req.requested_type
    change_req.status = "completed"
    await db.commit()

    logger.info(
        "type_change_confirmed",
        worker_id=str(worker.id),
        new_type=worker.worker_type,
    )
    return {"message": "Tipo de perfil actualizado correctamente.", "new_type": worker.worker_type}
```

Migración para `type_change_requests`:

```bash
alembic revision --autogenerate -m "add type_change_requests sprint5"
alembic upgrade head
```

---

## PARTE C — RF034: Eliminación de cuenta (soft-delete completo)

```python
# En app/api/v1/workers.py — agregar:

@router.delete("/api/v1/workers/{worker_id}/account")
async def delete_account(
    worker_id: UUID,
    confirmation: str,  # query param: ?confirmation=ELIMINAR
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """
    RF034: Eliminación de cuenta con soft-delete.
    El usuario debe escribir "ELIMINAR" para confirmar.
    No se elimina físicamente — datos retenidos 30 días para auditoría (Ley 29733).
    """
    if confirmation != "ELIMINAR":
        raise HTTPException(
            status_code=400,
            detail="Debes confirmar escribiendo 'ELIMINAR' como parámetro de confirmación."
        )

    res = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = res.scalar_one_or_none()
    if not worker or worker.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin autorización")

    now = __import__('datetime').datetime.utcnow()
    
    # Soft-delete: marcar para eliminación en 30 días
    worker.deleted_at = now
    worker.deletion_scheduled_at = now + __import__('datetime').timedelta(days=30)
    current_user.is_active = False
    current_user.deletion_requested_at = now

    # Desactivar listings del marketplace si OFICIO
    if worker.worker_type == "oficio":
        from sqlalchemy import update
        await db.execute(
            update(ServiceListing)
            .where(ServiceListing.worker_id == worker_id)
            .values(is_active=False)
        )

    await db.commit()
    logger.info("account_deletion_requested", worker_id=str(worker_id))
    
    return {
        "message": "Tu cuenta ha sido marcada para eliminación.",
        "scheduled_deletion_date": worker.deletion_scheduled_at.isoformat(),
        "note": "Tus datos se eliminarán permanentemente en 30 días. Contacta a DRTPE si quieres cancelar.",
    }
```

---

## PARTE D — RF124/RF125: Contratos desde marketplace

```python
# app/api/v1/contracts.py
"""
Gestión de contratos generados desde el marketplace.
RF124: crear contrato entre cliente y trabajador OFICIO.
RF125: historial de contratos del trabajador.
"""
from uuid import UUID
import uuid as uuid_mod
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import get_db
from app.core.security import require_role, UserRole
from app.core.encryption import encrypt_field
from app.models import Contract, Worker, User

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])


@router.post("")
async def create_contract(
    worker_id: UUID,
    listing_id: UUID,
    agreed_amount: float,
    contract_type: str,  # 'formal', 'marketplace'
    consent_given: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """RF124: Crear contrato desde marketplace."""
    from app.core.consent import require_consent
    require_consent(consent_given, "contrato_laboral")

    # Calcular número de contrato del trabajador
    from sqlalchemy import func, select as sa_select
    res = await db.execute(
        sa_select(func.count(Contract.id)).where(Contract.worker_id == worker_id)
    )
    contract_count = res.scalar_one() or 0

    contract = Contract(
        id=uuid_mod.uuid4(),
        worker_id=worker_id,
        employer_id=None,              # cliente anónimo del marketplace
        contract_number=contract_count + 1,
        contract_type=contract_type,
        monthly_salary=encrypt_field(str(agreed_amount)) if agreed_amount else None,
        signed_at=__import__('datetime').datetime.utcnow(),
        is_active=True,
    )
    db.add(contract)
    await db.commit()

    return {"contract_id": str(contract.id), "contract_number": contract.contract_number}


@router.get("/worker/{worker_id}")
async def get_worker_contracts(
    worker_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """RF125: Historial de contratos del trabajador."""
    res = await db.execute(
        select(Contract)
        .where(Contract.worker_id == worker_id)
        .order_by(Contract.signed_at.desc())
    )
    contracts = res.scalars().all()
    return {
        "contracts": [
            {
                "id": str(c.id),
                "contract_number": c.contract_number,
                "contract_type": c.contract_type,
                "signed_at": c.signed_at.isoformat() if c.signed_at else None,
                "is_active": c.is_active,
            }
            for c in contracts
        ]
    }
```

---

## PARTE E — RF150: Estado de equidad visible al usuario

```python
# En app/api/v1/matching.py — agregar endpoint:

@router.get("/api/v1/match/{worker_id}/equity-status")
async def get_equity_status(
    worker_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """
    RF150: Mostrar al trabajador si su perfil se vio afectado por re-ranking equitativo.
    Lenguaje positivo y explicativo — no alarmar al usuario.
    """
    from sqlalchemy import select
    from app.models import EquityAuditLog
    from sqlalchemy import func

    res = await db.execute(
        select(EquityAuditLog)
        .where(EquityAuditLog.worker_id == worker_id)
        .order_by(EquityAuditLog.created_at.desc())
        .limit(10)
    )
    logs = res.scalars().all()

    reranking_count = sum(1 for log in logs if log.reranking_applied)
    total = len(logs)

    message = (
        "Tu perfil aparece en resultados de búsqueda de manera equitativa."
        if reranking_count == 0 else
        f"El sistema aplicó ajustes de visibilidad en {reranking_count} de "
        f"tus {total} últimas búsquedas para garantizar que trabajadores de "
        f"todos los distritos tengan igualdad de oportunidades."
    )

    return {
        "worker_id": str(worker_id),
        "equity_adjustments_applied": reranking_count,
        "total_searches_analyzed": total,
        "message": message,
        "disparate_impact_avg": (
            sum(log.disparate_impact or 0 for log in logs) / max(total, 1)
        ),
        "explanation": (
            "El sistema de equidad garantiza que trabajadores de El Tambo y Chilca "
            "tengan la misma visibilidad que los de Huancayo central."
        ),
    }
```

---

## PARTE F — Seed de datos realistas de Huancayo

Crea `app/utils/seed_research.py`:

```python
# app/utils/seed_research.py
"""
Seed de datos de investigación — 20 workers por tipo (60 total).
Datos realistas de Huancayo, Perú para pruebas del sistema.
Cubre el requisito de datos de prueba diferenciados por tipo.
"""
import asyncio
import uuid
from app.core.db import AsyncSessionFactory
from app.core.encryption import encrypt_field
from app.models import User, Worker, WizardProgress, PortfolioEntry, ServiceListing, JobOffer, Employer
import structlog

logger = structlog.get_logger()

# ─── Datos de primer empleo ───────────────────────────────────────────
PRIMER_EMPLEO_SEED = [
    {"name": "Ana Quispe Huamán", "district": "Huancayo", "interests": "administración y ventas",
     "skills": ["puntual", "responsable", "trabajo en equipo", "computación básica"]},
    {"name": "Carlos Mendoza Flores", "district": "El Tambo", "interests": "mecánica automotriz",
     "skills": ["trabajo manual", "mecánica básica", "ordenado"]},
    {"name": "María Ccente Quispe", "district": "Chilca", "interests": "enfermería y salud",
     "skills": ["cuidado de personas", "puntual", "comunicación"]},
    {"name": "José Palomino Torres", "district": "Huancayo", "interests": "sistemas y computación",
     "skills": ["programación básica", "Excel", "resolución de problemas"]},
    {"name": "Rosa Huanca Mamani", "district": "El Tambo", "interests": "cocina y gastronomía",
     "skills": ["cocina andina", "repostería", "limpieza y orden"]},
    {"name": "Diego Ayala Carbajal", "district": "Huancayo", "interests": "educación y docencia",
     "skills": ["comunicación", "paciencia", "trabajo con niños"]},
    {"name": "Lucía Ramos Vega", "district": "Chilca", "interests": "contabilidad",
     "skills": ["matemáticas", "Excel", "ordenada", "análisis"]},
    {"name": "Pedro Cóndor Sulca", "district": "El Tambo", "interests": "construcción civil",
     "skills": ["trabajo físico", "albañilería básica", "puntual"]},
    {"name": "Sofía Lazo Inga", "district": "Huancayo", "interests": "marketing digital",
     "skills": ["redes sociales", "fotografía", "creatividad"]},
    {"name": "Miguel Asto Ccora", "district": "Chilca", "interests": "logística y almacén",
     "skills": ["ordenado", "trabajo en equipo", "manejo de carga"]},
    # 10 más...
    {"name": "Elena Tello Paucar", "district": "Huancayo", "interests": "atención al cliente",
     "skills": ["comunicación", "amable", "paciencia", "ventas"]},
    {"name": "Fernando Huari Lima", "district": "El Tambo", "interests": "electricidad",
     "skills": ["electricidad básica", "trabajo manual", "seguridad"]},
    {"name": "Carmen Ore Soto", "district": "Chilca", "interests": "costura y confección",
     "skills": ["costura", "diseño básico", "detalle"]},
    {"name": "Luis Poma Rojas", "district": "Huancayo", "interests": "gastronomía",
     "skills": ["cocina", "atención al cliente", "rapidez"]},
    {"name": "Gina Quispe Atauje", "district": "El Tambo", "interests": "recursos humanos",
     "skills": ["comunicación", "organización", "Word", "Excel"]},
    {"name": "Roberto Coras Sulca", "district": "Chilca", "interests": "carpintería",
     "skills": ["trabajo en madera", "medidas", "detalle"]},
    {"name": "Milagros Huanca Ore", "district": "Huancayo", "interests": "turismo y hotelería",
     "skills": ["inglés básico", "amable", "organización"]},
    {"name": "Ángel Palma Taipe", "district": "El Tambo", "interests": "soldadura",
     "skills": ["trabajo manual", "metales", "seguridad"]},
    {"name": "Patricia Ccente Vega", "district": "Chilca", "interests": "enfermería",
     "skills": ["cuidado de pacientes", "responsable", "puntual"]},
    {"name": "César Inca Flores", "district": "Huancayo", "interests": "informática",
     "skills": ["computación", "internet", "redes básicas"]},
]

# ─── Datos de oficio ────────────────────────────────────────────────
OFICIO_SEED = [
    {"name": "Juan Huamán Asto", "district": "El Tambo", "trade": "Electricidad",
     "years": 8, "rating": 4.7, "portfolio": [
        {"title": "Cableado casa 2 pisos El Tambo", "desc": "Instalé el cableado completo de una casa de 2 pisos en El Tambo, incluyendo tablero y tomacorrientes", "skills": ["instalación eléctrica", "tableros", "cableado"]},
        {"title": "Reparación instalación Chilca", "desc": "Reparé la instalación eléctrica de un local comercial en Chilca después de un cortocircuito", "skills": ["diagnóstico eléctrico", "reparación"]},
    ]},
    {"name": "Roberto Quispe Poma", "district": "Huancayo", "trade": "Gasfitería",
     "years": 12, "rating": 4.9, "portfolio": [
        {"title": "Instalación baño completo Huancayo centro", "desc": "Instalé todos los servicios sanitarios de un baño nuevo: inodoro, lavatorio, ducha y cañerías", "skills": ["plomería", "sanitarios", "cañerías"]},
    ]},
    {"name": "Mario Ccente Torres", "district": "Chilca", "trade": "Carpintería",
     "years": 15, "rating": 4.8, "portfolio": [
        {"title": "Cocina empotrada Chilca", "desc": "Fabriqué e instalé una cocina empotrada de melanina para una familia en Chilca", "skills": ["melanina", "cocina", "medidas", "carpintería"]},
        {"title": "Dormitorio completo madera", "desc": "Cama, closet y cómoda de madera cedro para dormitorio matrimonial", "skills": ["madera cedro", "ebanistería", "acabados"]},
    ]},
    {"name": "Sergio Lazo Mamani", "district": "El Tambo", "trade": "Albañilería",
     "years": 10, "rating": 4.5, "portfolio": [
        {"title": "Ampliación segundo piso El Tambo", "desc": "Construí el segundo piso de una casa familiar en El Tambo, 60 m2", "skills": ["construcción", "ladrillo", "concreto", "fierro"]},
    ]},
    {"name": "Félix Ayala Inga", "district": "Huancayo", "trade": "Pintura",
     "years": 7, "rating": 4.4, "portfolio": [
        {"title": "Pintado casa 3 pisos Huancayo", "desc": "Pintado interior y exterior de casa de 3 pisos en Huancayo, con base y acabado látex", "skills": ["pintura látex", "empaste", "base", "acabados"]},
    ]},
    {"name": "Raúl Sulca Flores", "district": "Chilca", "trade": "Mecánica automotriz",
     "years": 9, "rating": 4.6, "portfolio": [
        {"title": "Mantenimiento preventivo 50 autos/mes", "desc": "Taller en Chilca, hago mantenimiento preventivo y correctivo a vehículos de todo tipo", "skills": ["motor", "frenos", "transmisión", "diagnóstico"]},
    ]},
    {"name": "Hugo Cóndor Vera", "district": "El Tambo", "trade": "Techado",
     "years": 11, "rating": 4.7, "portfolio": [
        {"title": "Techo calamina 200 m2 El Tambo", "desc": "Instalé techo de calamina galvanizada de 200 m2 para almacén industrial en El Tambo", "skills": ["calamina", "estructura metálica", "trabajo en altura"]},
    ]},
    {"name": "Arturo Palomino Cruz", "district": "Huancayo", "trade": "Soldadura y metalurgia",
     "years": 13, "rating": 4.8, "portfolio": [
        {"title": "Rejas y puertas metálicas Huancayo", "desc": "Fabrico e instalo rejas de seguridad, puertas y portones metálicos a medida", "skills": ["soldadura MIG", "soldadura TIG", "fierro", "diseño"]},
    ]},
    {"name": "Leoncio Ramos Huanca", "district": "Chilca", "trade": "Jardinería",
     "years": 6, "rating": 4.3, "portfolio": [
        {"title": "Jardín residencial El Tambo", "desc": "Diseñé e implementé jardín de 80 m2 con sistema de riego tecnificado", "skills": ["diseño paisajístico", "plantas ornamentales", "riego tecnificado"]},
    ]},
    {"name": "Víctor Huanca Rojas", "district": "El Tambo", "trade": "Limpieza y mantenimiento",
     "years": 4, "rating": 4.2, "portfolio": [
        {"title": "Limpieza oficinas 10 empresas/mes", "desc": "Servicio de limpieza profunda para oficinas y locales comerciales en El Tambo y Huancayo", "skills": ["limpieza industrial", "pulido de pisos", "desinfección"]},
    ]},
    # 10 más
    {"name": "Teodoro Quispe Ayala", "district": "Huancayo", "trade": "Electricidad",
     "years": 5, "rating": 4.5, "portfolio": [
        {"title": "Instalación eléctrica local comercial", "desc": "Instalé el sistema eléctrico completo de una tienda de ropa en el mercado central de Huancayo", "skills": ["instalación comercial", "tableros trifásicos"]},
    ]},
    {"name": "Benigno Soto Lima", "district": "Chilca", "trade": "Gasfitería",
     "years": 8, "rating": 4.6, "portfolio": [
        {"title": "Red de agua edificio 4 pisos", "desc": "Instalé toda la red de agua y desagüe de un edificio de 4 pisos en Chilca", "skills": ["red de agua", "desagüe", "PVC", "termofusión"]},
    ]},
    {"name": "Eugenio Ore Palma", "district": "El Tambo", "trade": "Carpintería",
     "years": 20, "rating": 4.9, "portfolio": [
        {"title": "30 años fabricando muebles en Junín", "desc": "Especialista en muebles de madera nativa. Hago dormitorios, comedores y muebles a pedido", "skills": ["madera nativa", "barnizado", "tallado", "ebanistería"]},
    ]},
    {"name": "Simón Taipe Vega", "district": "Huancayo", "trade": "Albañilería",
     "years": 14, "rating": 4.7, "portfolio": [
        {"title": "Acabados y revestimientos Huancayo", "desc": "Especializado en acabados finos: porcelanato, mayólica, enchapado de piedra", "skills": ["porcelanato", "mayólica", "piedra", "enchapado"]},
    ]},
    {"name": "Clodomiro Ccente Asto", "district": "Chilca", "trade": "Pintura",
     "years": 3, "rating": 4.1, "portfolio": [
        {"title": "Pintado de interiores con texturas", "desc": "Aplico texturas decorativas, estuco veneciano y pinturas especiales para interiores", "skills": ["texturas", "estuco veneciano", "pintura decorativa"]},
    ]},
    {"name": "Justino Flores Poma", "district": "El Tambo", "trade": "Mecánica automotriz",
     "years": 16, "rating": 4.8, "portfolio": [
        {"title": "Especialista en autos japoneses", "desc": "20 años de experiencia en mecánica de autos japoneses: Toyota, Mitsubishi, Nissan, Subaru", "skills": ["mecánica japonesa", "inyección electrónica", "scanner"]},
    ]},
    {"name": "Esteban Huamán Coras", "district": "Huancayo", "trade": "Techado",
     "years": 8, "rating": 4.4, "portfolio": [
        {"title": "Techos de fibrocemento y eternit", "desc": "Instalación y reparación de techos de fibrocemento, eternit y policarbonato en Huancayo", "skills": ["fibrocemento", "eternit", "policarbonato"]},
    ]},
    {"name": "Nicanor Sulca Quispe", "district": "Chilca", "trade": "Soldadura y metalurgia",
     "years": 6, "rating": 4.3, "portfolio": [
        {"title": "Estructuras metálicas para galpones", "desc": "Fabrico estructuras metálicas, tijerales y coberturas para galpones industriales en Chilca", "skills": ["tijerales", "soldadura estructural", "fierro negro"]},
    ]},
    {"name": "Marcelino Inca Torres", "district": "El Tambo", "trade": "Costura y confección",
     "years": 9, "rating": 4.5, "portfolio": [
        {"title": "Uniformes escolares a pedido", "desc": "Confecciono uniformes escolares, ropa de trabajo y prendas en general para empresas de El Tambo", "skills": ["costura industrial", "patronaje", "uniformes"]},
    ]},
    {"name": "Damián Ramos Lazo", "district": "Huancayo", "trade": "Cocina y pastelería",
     "years": 7, "rating": 4.7, "portfolio": [
        {"title": "Catering y eventos en Huancayo", "desc": "Servicio de catering para eventos empresariales y sociales en Huancayo: menú andino y fusión", "skills": ["cocina andina", "catering", "menú ejecutivo", "repostería"]},
    ]},
]

# ─── Datos de experiencia ───────────────────────────────────────────
EXPERIENCIA_SEED = [
    {"name": "Javier Palomino Quispe", "district": "Huancayo", "title": "Contador público",
     "years": 8, "bio": "CPC con experiencia en empresas mineras de Junín", "skills": ["contabilidad", "SUNAT", "NIIF", "Excel avanzado"]},
    {"name": "Claudia Mendoza Rojas", "district": "El Tambo", "title": "Profesora de matemáticas",
     "years": 12, "bio": "Docente con experiencia en colegios de El Tambo y Huancayo", "skills": ["matemáticas", "pedagogía", "SIAGIE", "tutoría"]},
    {"name": "Héctor Ayala Vega", "district": "Chilca", "title": "Técnico en enfermería",
     "years": 6, "bio": "Técnico en enfermería con experiencia en ESSALUD Junín", "skills": ["enfermería", "primeros auxilios", "triage", "signos vitales"]},
    {"name": "Silvia Ore Cruz", "district": "Huancayo", "title": "Administradora de empresas",
     "years": 9, "bio": "Bachiller en Administración UNCP, experiencia en PYMES de Huancayo", "skills": ["administración", "planillas", "gestión", "Excel", "Word"]},
    {"name": "Augusto Huanca Lima", "district": "El Tambo", "title": "Técnico en sistemas",
     "years": 5, "bio": "Técnico egresado de SENATI, especialidad en redes y soporte", "skills": ["redes", "soporte técnico", "Windows Server", "Linux básico"]},
    {"name": "Natalia Ccente Soto", "district": "Chilca", "title": "Secretaria ejecutiva",
     "years": 7, "bio": "Secretaria con experiencia en entidades públicas de Junín", "skills": ["Office avanzado", "redacción", "archivos", "atención al público"]},
    {"name": "Gonzalo Asto Flores", "district": "Huancayo", "title": "Ingeniero civil",
     "years": 10, "bio": "Colegiado CIP, proyectos de saneamiento y vivienda en Junín", "skills": ["AutoCAD", "S10", "MS Project", "supervisión de obras"]},
    {"name": "Pilar Taipe Huamán", "district": "El Tambo", "title": "Psicóloga",
     "years": 4, "bio": "Psicóloga clínica con experiencia en centros de salud de El Tambo", "skills": ["terapia cognitivo-conductual", "evaluación psicológica", "orientación"]},
    {"name": "Ernesto Sulca Palomino", "district": "Chilca", "title": "Vendedor técnico",
     "years": 11, "bio": "Experiencia en ventas B2B de materiales de construcción en Junín", "skills": ["ventas", "CRM", "negociación", "prospección"]},
    {"name": "Fabiola Ramos Mamani", "district": "Huancayo", "title": "Nutricionista",
     "years": 6, "bio": "Nutricionista en hospitales y programas sociales de Huancayo", "skills": ["nutrición clínica", "valoración nutricional", "programas de alimentación"]},
    {"name": "Orlando Vera Quispe", "district": "El Tambo", "title": "Técnico agrónomo",
     "years": 8, "bio": "Técnico SENASA con experiencia en certificación de cultivos orgánicos", "skills": ["agronomía", "SENASA", "cultivos andinos", "fitosanidad"]},
    {"name": "Beatriz Inca Ccente", "district": "Chilca", "title": "Asistente social",
     "years": 9, "bio": "Trabajadora social con experiencia en programas del MIMP en Junín", "skills": ["trabajo social", "intervención familiar", "MIMP", "informes sociales"]},
    {"name": "Marco Lazo Torres", "district": "Huancayo", "title": "Analista de sistemas",
     "years": 7, "bio": "Analista con experiencia en ERP y sistemas de gestión pública", "skills": ["Java", "SQL Server", "Python", "SEACE", "sistemas gubernamentales"]},
    {"name": "Gloria Huanca Ayala", "district": "El Tambo", "title": "Periodista",
     "years": 5, "bio": "Periodista de radio y TV regional en Junín", "skills": ["periodismo", "locución", "edición de video", "redes sociales"]},
    {"name": "Teodoro Coras Ore", "district": "Chilca", "title": "Electricista industrial",
     "years": 13, "bio": "Técnico SENATI especializado en instalaciones industriales y automatización", "skills": ["PLC", "automatización", "instalaciones trifásicas", "seguridad eléctrica"]},
    {"name": "Isabel Poma Flores", "district": "Huancayo", "title": "Médico general",
     "years": 3, "bio": "Médico colegiado CMH, con SERUMS completado en Junín rural", "skills": ["medicina general", "SERUMS", "emergencias", "historia clínica"]},
    {"name": "Leandro Cruz Quispe", "district": "El Tambo", "title": "Técnico contable",
     "years": 10, "bio": "Técnico ISTP con experiencia en contabilidad de empresas comerciales", "skills": ["contabilidad", "CONCAR", "PDT", "facturación electrónica"]},
    {"name": "Mercedes Vega Sulca", "district": "Chilca", "title": "Abogada",
     "years": 8, "bio": "Abogada CAJ con especialidad en derecho laboral y familia", "skills": ["derecho laboral", "derecho familia", "procesos judiciales", "conciliación"]},
    {"name": "Pascual Lima Ccente", "district": "Huancayo", "title": "Técnico en farmacia",
     "years": 6, "bio": "Técnico farmacéutico con experiencia en boticas y farmacias de Huancayo", "skills": ["farmacología básica", "dispensación", "inventario", "BPA"]},
    {"name": "Sandra Huamán Rojas", "district": "El Tambo", "title": "Diseñadora gráfica",
     "years": 4, "bio": "Diseñadora freelance con clientes en Huancayo y El Tambo", "skills": ["Photoshop", "Illustrator", "diseño publicitario", "identidad corporativa"]},
]


async def run_seed():
    """Ejecutar seed de datos para investigación."""
    logger.info("seed_research_starting", total_workers=60)
    async with AsyncSessionFactory() as db:
        await _seed_primer_empleo(db)
        await _seed_oficio(db)
        await _seed_experiencia(db)
    logger.info("seed_research_completed")


async def _seed_primer_empleo(db):
    for i, data in enumerate(PRIMER_EMPLEO_SEED):
        user = User(id=uuid.uuid4(), email=f"pe_{i+1}@seed.drtpe.test", role="worker", is_active=True)
        db.add(user)
        worker = Worker(
            id=uuid.uuid4(),
            user_id=user.id,
            worker_type="primer_empleo",
            full_name=encrypt_field(data["name"]),
            dni=encrypt_field(f"0000000{i+1:01d}"),
            district=data["district"],
            profile_completeness=60 + (i * 2),
        )
        db.add(worker)
        progress = WizardProgress(
            id=uuid.uuid4(),
            worker_id=worker.id,
            current_step=4,
            extracted_skills=data["skills"],
            answers={"job_interests": data["interests"]},
        )
        db.add(progress)
    await db.commit()
    logger.info("seed_primer_empleo_done", count=len(PRIMER_EMPLEO_SEED))


async def _seed_oficio(db):
    for i, data in enumerate(OFICIO_SEED):
        user = User(id=uuid.uuid4(), email=f"of_{i+1}@seed.drtpe.test", role="worker", is_active=True)
        db.add(user)
        worker = Worker(
            id=uuid.uuid4(),
            user_id=user.id,
            worker_type="oficio",
            full_name=encrypt_field(data["name"]),
            dni=encrypt_field(f"1111111{i+1:01d}"),
            district=data["district"],
            trade_category=data["trade"],
            years_experience=data["years"],
            avg_rating=data["rating"],
            is_available=True,
            profile_completeness=85 + (i % 10),
        )
        db.add(worker)
        for j, entry_data in enumerate(data["portfolio"]):
            entry = PortfolioEntry(
                id=uuid.uuid4(),
                worker_id=worker.id,
                title=entry_data["title"],
                description=entry_data["desc"],
                extracted_skills=entry_data["skills"],
                is_public=True,
            )
            db.add(entry)
        listing = ServiceListing(
            id=uuid.uuid4(),
            worker_id=worker.id,
            trade_category=data["trade"],
            title=f"{data['trade']} profesional en {data['district']}",
            description=f"Servicio de {data['trade'].lower()} con {data['years']} años de experiencia en {data['district']} y alrededores.",
            districts=[data["district"], "Huancayo"],
            is_active=True,
        )
        db.add(listing)
    await db.commit()
    logger.info("seed_oficio_done", count=len(OFICIO_SEED))


async def _seed_experiencia(db):
    for i, data in enumerate(EXPERIENCIA_SEED):
        user = User(id=uuid.uuid4(), email=f"exp_{i+1}@seed.drtpe.test", role="worker", is_active=True)
        db.add(user)
        worker = Worker(
            id=uuid.uuid4(),
            user_id=user.id,
            worker_type="experiencia",
            full_name=encrypt_field(data["name"]),
            dni=encrypt_field(f"2222222{i+1:01d}"),
            district=data["district"],
            years_experience=data["years"],
            profile_completeness=75 + (i % 20),
        )
        db.add(worker)
    await db.commit()
    logger.info("seed_experiencia_done", count=len(EXPERIENCIA_SEED))


if __name__ == "__main__":
    asyncio.run(run_seed())
```

**Agregar al Makefile / comandos del CLAUDE.md:**
```bash
# Seed de datos de investigación (60 workers reales de Huancayo)
python -m app.utils.seed_research
```

---

## TESTS OBLIGATORIOS

```bash
touch tests/integration/test_api_moderation.py
touch tests/integration/test_api_type_change.py
touch tests/unit/test_equity_status.py
```

```bash
pytest tests/integration/test_api_moderation.py \
       tests/integration/test_api_type_change.py -v
ruff check app/api/v1/moderation.py app/utils/seed_research.py
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `app/api/v1/moderation.py` — flag, ban, unban
- `app/api/v1/contracts.py` — RF124/RF125
- `app/api/v1/workers.py` — RF023 (type change) + RF034 (delete account)
- `app/utils/seed_research.py` — 60 workers realistas de Huancayo
- `alembic/versions/` — content_flags, type_change_requests

---

**Cuando termines, el agente `senior-frontend` recibirá la instrucción 3
para implementar FlagContentButton, ModerationQueue, orientación laboral y accesibilidad WCAG 2.1 AA.**
