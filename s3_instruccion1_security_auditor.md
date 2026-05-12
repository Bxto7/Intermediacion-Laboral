# SPRINT 3 — INSTRUCCIÓN 1 de 5
# Agente: `security-auditor`
# Tarea: Auditoría de seguridad + hardening antes del motor de matching

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
Es la fuente de verdad de arquitectura, convenciones y prohibiciones. Si algo de este prompt
contradice el `CLAUDE.md`, el `CLAUDE.md` tiene prioridad absoluta.

**Sprint actual:** Sprint 3 — Motor de Matching ML + Marketplace + Notificaciones
**Lo que entregó el Sprint 2:** Motor NLP real (embeddings semánticos diferenciados por tipo,
extracción de habilidades para los 3 flujos A/B/C, diccionario local Huancayo), módulo completo
de empleadores y ofertas (M03/RF036–RF055), portfolio visual (Flujo C1) y marketplace base (Flujo C2).

**Tu trabajo en esta instrucción:** Cerrar la deuda de seguridad del Sprint 2 antes de
que el Sprint 3 construya sobre ella. El motor de matching (M05) procesará datos sensibles
de trabajadores; cualquier vulnerabilidad abierta debe cerrarse ahora.

---

## TAREAS DE SEGURIDAD — EJECUTAR EN ORDEN

Usa la herramienta **Bash** para todo. Con ella lees código, creas archivos, corres tests y
aplicas fixes. No uses otra herramienta para el backend.

### 1. Auditoría de embeddings — sanitización de datos sensibles

Los embeddings se construyen a partir del texto del perfil del trabajador. Verificar que
**ningún embedding incluya datos PII** (DNI, teléfono, email, nombre completo).

```bash
# Buscar en todo el código NLP si algún campo PII se incluye en el texto de embedding
grep -rn "full_name\|dni\|phone\|email" app/nlp/embeddings.py app/services/
```

**Acción requerida:**
- En `app/nlp/embeddings.py` confirmar que `build_profile_text()` para cada `WorkerType`
  usa **únicamente**: `district`, `trade_category`, `years_experience`, `avg_rating`,
  `skills[]`, `job_interests`, `wizard_skills[]`, `portfolio_count`.
- Si hay cualquier campo PII en el texto → eliminar y agregar test de regresión.
- Crear `tests/unit/test_embedding_no_pii.py` que confirme que el texto generado
  no contiene patrones de DNI (8 dígitos), teléfono (+51...) ni email.

### 2. Portfolio público — no exponer UUID interno

Las URLs públicas del portfolio son `/p/{slug}` (campo `workers.slug`). Verificar que:

```bash
grep -rn "worker_id\|\.id" app/api/v1/portfolio_public.py app/schemas/portfolio.py
```

**Acción requerida:**
- El endpoint `GET /api/v1/public/portfolio/{slug}` **NO** debe retornar `worker_id` ni
  ningún UUID interno en el response schema.
- Si el schema `PublicPortfolioResponse` expone `worker_id` → reemplazarlo con
  `slug: str` únicamente para la identificación pública.
- Agregar test: `tests/integration/test_portfolio_public_no_uuid.py`

### 3. Validación de archivos de portfolio — magic numbers + antivirus stub

El endpoint `POST /api/v1/portfolio/entries` acepta fotos. Verificar la validación:

```bash
grep -rn "content_type\|mime\|file_size\|magic" app/api/v1/portfolio.py app/utils/
```

**Acción requerida — implementar `app/utils/file_validator.py`** si no existe:

```python
# app/utils/file_validator.py
import magic  # python-magic
from fastapi import UploadFile, HTTPException

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

async def validate_portfolio_photo(file: UploadFile) -> bytes:
    """
    1. Leer primeros 2048 bytes para magic number check
    2. Verificar MIME real con python-magic (no confiar en Content-Type del cliente)
    3. Verificar tamaño total ≤ 5 MB
    4. Stub de antivirus: log de auditoría + placeholder para ClamAV futuro
    Raises HTTPException 400 si falla cualquier validación.
    """
    content = await file.read()
    
    # Magic number check
    mime = magic.from_buffer(content[:2048], mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido: {mime}. Solo JPEG, PNG o WEBP."
        )
    
    # Tamaño
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="El archivo supera el límite de 5 MB."
        )
    
    # Stub antivirus — log de auditoría
    import structlog
    logger = structlog.get_logger()
    logger.info(
        "portfolio_photo_validated",
        mime_type=mime,
        size_bytes=len(content),
        antivirus_scan="pending_clamav_integration",
    )
    
    return content
```

Actualizar `requirements.txt` con `python-magic>=0.4.27`.

### 4. CORS — validar que no esté en modo wildcard en producción

```bash
grep -rn "allow_origins\|CORSMiddleware" app/main.py app/core/
```

**Acción requerida:**
- `allow_origins` debe leer de `settings.CORS_ORIGINS` (lista de dominios permitidos).
- Si hay `allow_origins=["*"]` → reemplazar con variable de entorno.
- En `.env.example` agregar: `CORS_ORIGINS=https://tudominio.com,https://admin.tudominio.com`
- Test: `tests/unit/test_cors_config.py` — verifica que en `ENV=production` no hay wildcard.

### 5. Validación de UUID en tareas Celery — prevenir task injection

```bash
grep -rn "worker_id\|listing_id" app/tasks/
```

**Acción requerida:**
- Todas las tareas Celery que reciben `worker_id` deben validarlo como UUID v4 válido
  **antes** de hacer cualquier query a la BD.

```python
# Patrón correcto en cualquier task de Celery:
import uuid
from celery import shared_task

@shared_task(name="tasks.generate_embedding")
def generate_embedding_task(worker_id: str, worker_type: str):
    # Validar UUID antes de cualquier operación
    try:
        validated_id = uuid.UUID(worker_id, version=4)
    except ValueError:
        logger.error("invalid_uuid_in_task", worker_id=worker_id)
        return  # no raise — silenciar para no reintentar con input inválido
    ...
```

Verificar esto en: `tasks/embeddings.py`, `tasks/cv_generator.py`, `tasks/notifications.py`.

### 6. Headers de seguridad HTTP

```bash
grep -rn "SecurityHeadersMiddleware\|X-Frame\|X-Content-Type\|Strict-Transport" app/main.py
```

**Acción requerida — agregar middleware si no existe:**

```python
# app/core/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]    = "nosniff"
        response.headers["X-Frame-Options"]           = "DENY"
        response.headers["X-XSS-Protection"]          = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = "geolocation=(), microphone=()"
        # HSTS solo en producción
        if settings.ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
```

Registrar en `app/main.py`: `app.add_middleware(SecurityHeadersMiddleware)`.

### 7. Audit log en matching — preparar para Sprint 3

El motor de matching (M05/RF076–RF095) que se implementa en esta instrucción necesita
una tabla de auditoría. Créala ahora con migración Alembic:

```bash
alembic revision --autogenerate -m "add match_events audit table"
```

**Tabla requerida (agregar manualmente si autogenerate no la detecta):**

```sql
CREATE TABLE match_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    worker_type     VARCHAR(20) NOT NULL,
    matched_job_id  UUID REFERENCES job_offers(id),       -- NULL para marketplace
    matched_listing_id UUID REFERENCES service_listings(id), -- NULL para empleo
    cosine_sim      DECIMAL(5,4),
    ml_score        DECIMAL(5,4),
    reputation_score DECIMAL(5,4),
    combined_score  DECIMAL(5,4),
    rank_position   INTEGER,
    action          VARCHAR(20),  -- 'viewed', 'applied', 'contacted', 'dismissed'
    equity_flag     BOOLEAN DEFAULT false, -- true si activó re-ranking equitativo
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON match_events (worker_id, created_at DESC);
CREATE INDEX ON match_events (worker_type, created_at DESC);
```

Aplicar: `alembic upgrade head`

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

Al terminar, confirma que existen y pasan:

```bash
# Tests de seguridad
pytest tests/unit/test_embedding_no_pii.py -v
pytest tests/unit/test_cors_config.py -v
pytest tests/integration/test_portfolio_public_no_uuid.py -v

# Linting sin errores
ruff check app/utils/file_validator.py app/core/security_headers.py

# Migración aplicada
alembic current  # debe mostrar la revisión de match_events

# Verificar que no hay print() en ningún archivo nuevo/modificado
grep -rn "print(" app/utils/file_validator.py app/core/security_headers.py app/tasks/
```

**Resumen de archivos creados/modificados:**
- `app/utils/file_validator.py` — nuevo
- `app/core/security_headers.py` — nuevo
- `app/main.py` — agregar middleware de headers
- `app/nlp/embeddings.py` — fix si había PII
- `app/api/v1/portfolio_public.py` — fix UUID expuesto
- `app/tasks/embeddings.py` / `cv_generator.py` / `notifications.py` — validación UUID
- `alembic/versions/XXXX_add_match_events_audit_table.py` — nueva migración
- `requirements.txt` — agregar python-magic
- `tests/unit/test_embedding_no_pii.py` — nuevo
- `tests/unit/test_cors_config.py` — nuevo
- `tests/integration/test_portfolio_public_no_uuid.py` — nuevo

---

**Cuando termines esta instrucción, el agente `ml-engineer` recibirá la instrucción 2
para implementar el motor de matching M05.**
