# SPRINT 5 — INSTRUCCIÓN 1 de 6
# Agente: `security-auditor`
# Tarea: Auditoría final de seguridad + hardening GCS + soft-delete + export-my-data + SECURITY_AUDIT.md

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
Este es el sprint de cierre. Tu trabajo cubre los últimos ítems de seguridad antes del deploy
a producción real. Todo lo que detectes aquí bloquea el release si no se resuelve.

**Principio de esta instrucción:** Si existe alguna duda entre seguridad y funcionalidad, gana seguridad.

---

## TAREA 1 — Credenciales GCP fuera del repositorio

```bash
# Verificar que las credenciales nunca han sido commiteadas
git log --all --full-history -- "**/*.json" | grep -i "gcp\|credential\|key" && echo "⚠️ REVISAR HISTORIA" || echo "✅ Sin credenciales en git"

# Verificar .gitignore actual
cat .gitignore | grep -E "gcp|credential|\.env"
```

**Acción requerida — actualizar `.gitignore`:**

```gitignore
# Credenciales GCP — NUNCA en el repositorio
backend/credentials/
backend/credentials/*.json
*.serviceaccount.json
gcp-key*.json

# Variables de entorno
.env
.env.*
!.env.example

# Archivos de modelo ML (pueden ser grandes — usar GCS)
backend/app/ml/models/*.pkl

# Cobertura de tests
backend/coverage.xml
backend/coverage_html/
frontend/coverage/

# Build artifacts
frontend/dist/
backend/__pycache__/
**/__pycache__/
**/*.pyc
```

**Verificar que `GOOGLE_APPLICATION_CREDENTIALS` apunta a la ruta correcta en cada entorno:**
```bash
# Desarrollo local: archivo físico en /backend/credentials/ (en .gitignore)
# Cloud Run: usar Workload Identity (sin archivo físico)
# Staging/CI: usar secret de GitHub Actions
grep -rn "GOOGLE_APPLICATION_CREDENTIALS" app/core/config.py .github/
```

---

## TAREA 2 — URLs firmadas GCS: expiración máxima 60 minutos

```bash
grep -rn "generate_signed_url\|expiration" app/services/storage.py
```

**Verificar que se respeta:**
```python
# En app/services/storage.py — ya implementado en Sprint 4:
MAX_URL_EXPIRATION_MINUTES = 60

# Buscar cualquier llamada que pase un valor mayor:
grep -rn "expiration_minutes\s*=\s*[7-9][0-9]\|expiration_minutes\s*=\s*[1-9][0-9][0-9]" app/
```

Si se encuentran valores > 60 → corregir a 60.

**Agregar test:**

```python
# tests/unit/test_storage_security.py
def test_signed_url_max_expiration():
    """Las URLs firmadas nunca deben superar 60 minutos."""
    from app.services.storage import MAX_URL_EXPIRATION_MINUTES
    assert MAX_URL_EXPIRATION_MINUTES <= 60

def test_signed_url_capped_at_60():
    """Pasar 120 min debe resultar en URL con 60 min máximo."""
    from app.services.storage import generate_signed_url
    # Mock del cliente GCS
    with patch('app.services.storage._get_storage_client') as mock_client:
        mock_blob = MagicMock()
        mock_client.return_value.bucket.return_value.blob.return_value = mock_blob
        generate_signed_url("path/to/file.pdf", expiration_minutes=120)
        call_kwargs = mock_blob.generate_signed_url.call_args[1]
        assert call_kwargs['expiration'].seconds // 60 <= 60
```

---

## TAREA 3 — Soft-delete para encuestas económicas

```bash
grep -rn "economic_survey\|EconomicSurvey" app/models/ app/api/
```

**Acción requerida:** Las encuestas económicas contienen datos sensibles de ingresos.
El borrado debe ser lógico (soft-delete), nunca físico. Implementar si no existe:

```python
# En app/models/economic_survey.py — agregar campos:
class EconomicSurvey(Base):
    ...
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    deleted_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

# Migración:
# alembic revision --autogenerate -m "soft_delete_economic_surveys"
```

```python
# En el endpoint de eliminación (si existe):
@router.delete("/api/v1/surveys/economic/{survey_id}")
async def soft_delete_survey(survey_id: UUID, ...):
    survey.deleted_at = datetime.now(timezone.utc)
    survey.deleted_by = current_user.id
    # NO: db.delete(survey)
    # SÍ: solo marcar como eliminado
```

Asegurarse que **todos los SELECT** de surveys filtren `deleted_at IS NULL`.

---

## TAREA 4 — Export-my-data (Ley 29733 — derecho de acceso)

La Ley 29733 garantiza a los usuarios el derecho a acceder y exportar sus datos personales.
Implementar el endpoint de exportación:

Crea `app/api/v1/privacy.py`:

```python
# app/api/v1/privacy.py
"""
Derecho de acceso y portabilidad de datos (Ley N° 29733).
RF implícito en RNF de seguridad — cumplimiento normativo.
"""
import json
from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import get_db
from app.core.security import require_role, UserRole
from app.models import User, Worker, WizardProgress, PortfolioEntry, GeneratedCV
from app.core.encryption import decrypt_field

router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


@router.get("/export-my-data")
async def export_my_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """
    Exportar todos los datos personales del usuario.
    Derecho de acceso y portabilidad — Ley N° 29733.
    Retorna JSON con todos los datos (descifrados en memoria, nunca en logs).
    """
    # Cargar worker
    res = await db.execute(select(Worker).where(Worker.user_id == current_user.id))
    worker = res.scalar_one_or_none()

    export_data = {
        "user": {
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
            "role": current_user.role,
        },
        "worker": None,
        "wizard_progress": None,
        "portfolio_entries": [],
        "generated_cvs": [],
        "export_generated_at": __import__('datetime').datetime.utcnow().isoformat(),
        "data_controller": "DRTPE-Junín — Dirección Regional de Trabajo y Promoción del Empleo",
        "legal_basis": "Ley N° 29733 — Ley de Protección de Datos Personales del Perú",
    }

    if worker:
        export_data["worker"] = {
            "worker_type": worker.worker_type,
            "full_name": decrypt_field(worker.full_name),   # descifrar solo para exportar
            "phone": decrypt_field(worker.phone) if worker.phone else None,
            "district": worker.district,
            "trade_category": worker.trade_category,
            "years_experience": worker.years_experience,
            "profile_completeness": worker.profile_completeness,
        }

        # Wizard progress (PRIMER_EMPLEO)
        if worker.worker_type == "primer_empleo":
            res = await db.execute(
                select(WizardProgress).where(WizardProgress.worker_id == worker.id)
            )
            progress = res.scalar_one_or_none()
            if progress:
                export_data["wizard_progress"] = {
                    "current_step": progress.current_step,
                    "answers": progress.answers,
                    "extracted_skills": progress.extracted_skills,
                }

        # Portfolio (OFICIO)
        if worker.worker_type == "oficio":
            res = await db.execute(
                select(PortfolioEntry).where(PortfolioEntry.worker_id == worker.id)
            )
            entries = res.scalars().all()
            export_data["portfolio_entries"] = [
                {
                    "title": e.title,
                    "description": e.description,
                    "extracted_skills": e.extracted_skills,
                    "period_start": e.period_start.isoformat() if e.period_start else None,
                    "period_end": e.period_end.isoformat() if e.period_end else None,
                    "client_rating": float(e.client_rating) if e.client_rating else None,
                }
                for e in entries
            ]

        # CVs generados
        res = await db.execute(
            select(GeneratedCV).where(GeneratedCV.worker_id == worker.id)
        )
        cvs = res.scalars().all()
        export_data["generated_cvs"] = [
            {"cv_type": c.cv_type, "generated_at": c.generated_at.isoformat()}
            for c in cvs
        ]

    return JSONResponse(content=export_data)


@router.delete("/delete-my-account")
async def request_account_deletion(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """
    Solicitud de eliminación de cuenta (Ley 29733 — derecho al olvido).
    Soft-delete: marca cuenta como pendiente de eliminación.
    El equipo DRTPE confirma la eliminación en 15 días hábiles.
    """
    current_user.deletion_requested_at = __import__('datetime').datetime.utcnow()
    await db.commit()
    return {
        "message": "Tu solicitud de eliminación ha sido registrada.",
        "expected_completion_days": 15,
        "legal_basis": "Ley N° 29733, Art. 22",
    }
```

---

## TAREA 5 — Checklist de pen testing (manual)

Crea `SECURITY_PENTEST_CHECKLIST.md`:

```markdown
# Checklist de Pen Testing — DRTPE Sistema de Intermediación Laboral

## Autenticación y Autorización
- [ ] Intentar acceder a /api/v1/match/{otro_worker_id} con JWT de otro usuario → debe retornar 403
- [ ] Intentar acceder a /api/v1/admin/* sin rol ADMIN → debe retornar 403
- [ ] JWT expirado → debe retornar 401 (no 500)
- [ ] JWT manipulado (cambiar payload, mantener firma) → debe retornar 401
- [ ] Refresh token de otro usuario → debe retornar 401
- [ ] WebSocket con token inválido → debe cerrar con código 4001

## Rate Limiting
- [ ] 11+ intentos de login desde misma IP en 1 minuto → debe retornar 429
- [ ] 1001+ requests desde misma IP en 1 minuto → debe retornar 429
- [ ] 31+ requests de matching por usuario en 1 minuto → debe retornar 429

## Inyección
- [ ] SQL: ' OR 1=1-- en campos de búsqueda → debe retornar 422 (validación Pydantic)
- [ ] XSS: <script>alert(1)</script> en descripción de portfolio → debe escaparse en respuesta
- [ ] SSRF: URL externa en campo de foto → debe rechazarse (solo archivos directos)

## Datos Sensibles
- [ ] Respuesta de /api/v1/workers/{id} NO contiene DNI ni teléfono en texto plano
- [ ] Logs del servidor NO contienen DNI, teléfono ni email
- [ ] URL pública /p/{slug} NO expone worker_id interno
- [ ] monthly_income en BD está cifrado (verificar con psql directamente)

## Archivos
- [ ] Subir archivo .php como foto de portfolio → debe rechazarse (magic number check)
- [ ] Subir archivo SVG → debe rechazarse (potencial XSS)
- [ ] Subir archivo > 5 MB → debe rechazarse con 400
- [ ] URL firmada de GCS expirada → debe retornar 403 (no 200)

## Headers de Seguridad
- [ ] X-Content-Type-Options: nosniff presente en todas las respuestas
- [ ] X-Frame-Options: DENY presente en todas las respuestas
- [ ] Strict-Transport-Security presente en producción (HTTPS)
- [ ] No hay server version disclosure (sin "uvicorn/X.X.X" en headers)

## WebSocket
- [ ] Cuarta conexión WS simultánea desde mismo usuario → código 4029
- [ ] Mensaje no-JSON al WS → no crashea el servidor

## Datos Económicos
- [ ] POST /api/v1/surveys/economic sin consent_given=true → debe retornar 400
- [ ] GET /api/v1/privacy/export-my-data → datos descifrados del usuario correcto
- [ ] GET /api/v1/privacy/export-my-data de otro usuario → 403
```

---

## TAREA 6 — SECURITY_AUDIT.md (documento final)

Crea `SECURITY_AUDIT.md` en la raíz del repositorio:

```markdown
# SECURITY_AUDIT.md — Auditoría de Seguridad Final
# Sistema de Intermediación Laboral DRTPE-Junín
# Sprint 5 — Cierre del sistema

## Resumen de RNF de Seguridad implementados

### RNF001–RNF006 (ISO 27001)

| RNF | Descripción | Implementación | Estado |
|-----|-------------|----------------|--------|
| RNF001 | Autenticación JWT RS256 | app/core/security.py — JWT RS256, access 24h, refresh 7d | ✅ |
| RNF002 | Cifrado de datos sensibles AES-256 | app/core/encryption.py — AES-256-GCM con nonce aleatorio | ✅ |
| RNF003 | Control de acceso RBAC | require_role() en todos los endpoints protegidos | ✅ |
| RNF004 | Validación de entrada | Pydantic v2 en todos los schemas, magic number en fotos | ✅ |
| RNF005 | Auditoría de acciones | structlog JSON en todos los servicios, match_events table | ✅ |
| RNF006 | Protección contra ataques comunes | Rate limiting, CORS, security headers, OWASP ZAP en CI | ✅ |

### Ley N° 29733 (Protección de Datos Personales)

| Derecho | Implementación | Estado |
|---------|----------------|--------|
| Consentimiento informado | consent_records table, ConsentGuard() | ✅ |
| Acceso a mis datos | GET /api/v1/privacy/export-my-data | ✅ |
| Derecho al olvido | DELETE /api/v1/privacy/delete-my-account (soft-delete) | ✅ |
| Datos económicos cifrados | monthly_income AES-256-GCM | ✅ |
| No compartir sin consentimiento | consentimiento requerido en cada endpoint | ✅ |

## Hallazgos y resoluciones por sprint

### Sprint 1–2 (deuda resuelta en Sprint 3)
- [x] CORS wildcard → variables de entorno con lista explícita
- [x] Magic number validation para fotos de portfolio
- [x] UUID internos expuestos en URLs públicas → slugs

### Sprint 3–4 (deuda resuelta en Sprint 4)
- [x] WebSocket sin límite de conexiones → máx 3 por usuario, código 4029
- [x] Rate limiting ausente → RateLimitMiddleware Redis
- [x] Datos económicos sin cifrar → AES-256-GCM + consent_records

### Sprint 5 (cierre final)
- [x] URLs firmadas GCS máx 60 minutos
- [x] Credenciales GCP en .gitignore
- [x] Soft-delete para encuestas económicas
- [x] Export-my-data implementado

## Herramientas de seguridad activas
- **OWASP ZAP**: DAST semanal en staging (.github/workflows/security.yml)
- **ruff**: Linting estático (sin SQL crudo, sin print())
- **pytest-security**: Tests de seguridad en cada PR
- **GitHub Actions**: Sin deploy a producción sin tests verdes + cobertura ≥ 80%
- **Prometheus alerts**: Alerta automática si error rate > 10%

## Pentest manual
Realizado según SECURITY_PENTEST_CHECKLIST.md
Fecha: [completar antes del deploy a producción]
Responsable: Rojas Peña W. / Tovar Sanchez C.
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

```bash
# Verificar tests nuevos
pytest tests/unit/test_storage_security.py -v

# Verificar que .gitignore es correcto
git check-ignore backend/credentials/gcp-key.json && echo "✅ Ignorado"
git check-ignore .env && echo "✅ Ignorado"

# Verificar que SECURITY_AUDIT.md existe
cat SECURITY_AUDIT.md | wc -l  # debe ser > 50 líneas

# Verificar que el endpoint de privacidad funciona
# (requiere server corriendo)
curl -H "Authorization: Bearer {TOKEN}" http://localhost:8000/api/v1/privacy/export-my-data
```

**Archivos creados:**
- `.gitignore` — actualizado
- `app/api/v1/privacy.py` — export-my-data + soft-delete cuenta
- `tests/unit/test_storage_security.py`
- `SECURITY_PENTEST_CHECKLIST.md`
- `SECURITY_AUDIT.md`

---

**Cuando termines, el agente `python-pro` con skill `senior-backend` recibirá la instrucción 2
para implementar moderación de marketplace, RF faltantes, seed de datos realistas y cierre de RF.**
