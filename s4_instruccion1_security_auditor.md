# SPRINT 4 — INSTRUCCIÓN 1 de 5
# Agente: `security-auditor`
# Tarea: Auditoría de seguridad para Panel Admin DRTPE + datos económicos + rate limiting global

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
El Sprint 3 entregó el motor de matching, CVs PDF, WebSocket y el stack Celery+Prometheus.

**Sprint actual:** Sprint 4 — Panel Admin DRTPE + ML avanzado + Frontend completo + CI/CD
**Tu trabajo:** Auditar y hardening de seguridad ANTES de implementar el panel admin (M09/RF136–RF145)
y los endpoints de datos económicos. El panel admin tiene acceso a datos sensibles de investigación.

---

## TAREA 1 — WebSocket: Límite de conexiones por usuario

El Sprint 3 implementó WebSocket en `app/api/v1/ws_notifications.py`. Auditar:

```bash
grep -rn "websocket\|WebSocket" app/api/v1/ws_notifications.py
```

**Acción requerida:** Implementar límite de 3 conexiones WebSocket simultáneas por usuario
usando Redis INCR/DECR:

```python
# En app/api/v1/ws_notifications.py — agregar antes de accept():

WS_MAX_CONNECTIONS_PER_USER = 3
WS_CONNECTION_KEY = "ws_connections:{user_id}"

async def _check_ws_connection_limit(user_id: UUID, redis: Redis) -> bool:
    """
    Incrementa el contador de conexiones activas.
    Retorna True si está dentro del límite, False si se debe rechazar.
    """
    key = WS_CONNECTION_KEY.format(user_id=user_id)
    count = await redis.incr(key)
    await redis.expire(key, 3600)  # TTL 1h por si no se decrementa
    
    if count > WS_MAX_CONNECTIONS_PER_USER:
        await redis.decr(key)
        return False
    return True


async def _release_ws_connection(user_id: UUID, redis: Redis):
    """Decrementar al desconectar."""
    key = WS_CONNECTION_KEY.format(user_id=user_id)
    await redis.decr(key)


# En el handler WebSocket — integrar:
# if not await _check_ws_connection_limit(user_id, redis):
#     await websocket.close(code=4029)  # Too Many Requests
#     return
# try:
#     ...
# finally:
#     await _release_ws_connection(user_id, redis)
```

Test: `tests/unit/test_ws_connection_limit.py` — verificar que el 4to intento se rechaza con 4029.

---

## TAREA 2 — Cifrado AES para datos económicos (Ley 29733)

La tabla `economic_surveys` del Sprint 3 define `monthly_income BYTEA`. Verificar que la
implementación cifra correctamente:

```bash
grep -rn "economic_survey\|monthly_income" app/api/ app/services/ app/models/
```

**Acción requerida:** Confirmar que `app/core/encryption.py` implementa AES-256 y que
`monthly_income` NUNCA se almacena en texto plano:

```python
# app/core/encryption.py — verificar que existe y funciona:
from cryptography.fernet import Fernet  # O usar AES-GCM directo
import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_field(plaintext: str) -> bytes:
    """Cifrar campo sensible con AES-256-GCM."""
    key = bytes.fromhex(os.environ["FIELD_ENCRYPTION_KEY"])  # 32 bytes hex
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext)


def decrypt_field(ciphertext: bytes) -> str:
    """Descifrar campo sensible."""
    key = bytes.fromhex(os.environ["FIELD_ENCRYPTION_KEY"])
    data = base64.b64decode(ciphertext)
    nonce, ct = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()
```

Verificar que `FIELD_ENCRYPTION_KEY` está en `.env.example` y en `.gitignore`.

**Agregar en el servicio de encuestas:**
```python
# Al crear economic_survey:
survey = EconomicSurvey(
    monthly_income=encrypt_field(str(monthly_income_plaintext)),
    consent_given=True,  # Ley 29733 — obligatorio
)
```

**Agregar test:** `tests/unit/test_encryption.py`
- Cifrar → descifrar retorna el mismo valor
- Datos cifrados distintos en dos llamadas (por el nonce aleatorio)
- `encrypt_field("")` no lanza excepción

---

## TAREA 3 — consent_given obligatorio (Ley N° 29733)

```bash
grep -rn "consent_given" app/
```

**Acción requerida:** En TODOS los endpoints que recolectan datos personales, verificar que
`consent_given=True` antes de persistir. Implementar `ConsentGuard`:

```python
# app/core/consent.py
from fastapi import HTTPException

def require_consent(consent_given: bool, data_purpose: str):
    """
    Verificar consentimiento informado (Ley 29733).
    Llamar antes de cualquier operación de recolección de datos personales.
    """
    if not consent_given:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Se requiere consentimiento informado para {data_purpose}. "
                "Ley N° 29733 — Ley de Protección de Datos Personales."
            ),
        )
```

Verificar que se aplica en:
- `POST /api/v1/workers/onboarding` — datos del perfil
- `POST /api/v1/surveys/economic` — datos económicos (ingresos)
- `POST /api/v1/portfolio/entries` — fotos e información personal

---

## TAREA 4 — Rate limiting global (1000 req/min)

```bash
grep -rn "RateLimitMiddleware\|slowapi\|rate_limit" app/main.py app/core/
```

**Acción requerida:** Implementar rate limiting global con Redis:

```python
# app/core/rate_limiter.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from redis.asyncio import Redis
import time

RATE_LIMIT_GLOBAL   = 1000   # req/min por IP
RATE_LIMIT_AUTH     = 10     # req/min por IP (login/register)
RATE_LIMIT_MATCHING = 30     # req/min por user (matching es pesado)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis: Redis):
        super().__init__(app)
        self.redis = redis

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        path = request.url.path
        minute = int(time.time() // 60)

        # Seleccionar límite según endpoint
        if "/auth/" in path:
            limit = RATE_LIMIT_AUTH
            key = f"rl:auth:{ip}:{minute}"
        elif "/match/" in path:
            limit = RATE_LIMIT_MATCHING
            user_id = request.headers.get("X-User-ID", ip)
            key = f"rl:match:{user_id}:{minute}"
        else:
            limit = RATE_LIMIT_GLOBAL
            key = f"rl:global:{ip}:{minute}"

        count = await self.redis.incr(key)
        await self.redis.expire(key, 120)  # TTL 2 minutos

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes. Intenta en un minuto."},
            )

        return await call_next(request)
```

Registrar en `app/main.py`:
```python
from app.core.db import get_redis_sync
app.add_middleware(RateLimitMiddleware, redis=get_redis_sync())
```

**Test:** `tests/unit/test_rate_limiter.py`
- Solicitud 1001 desde misma IP → 429
- Auth: solicitud 11 → 429
- Cada IP tiene su propio contador independiente

---

## TAREA 5 — Migración: tabla `consent_records`

Para cumplir Ley 29733 se necesita registro auditable de consentimientos:

```bash
alembic revision --autogenerate -m "add consent_records table sprint4"
alembic upgrade head
```

```sql
CREATE TABLE consent_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    data_purpose    VARCHAR(100) NOT NULL,  -- 'perfil', 'datos_economicos', 'portfolio'
    ip_address      INET,                   -- IP desde donde se dio el consentimiento
    user_agent      TEXT,
    consent_given   BOOLEAN NOT NULL,
    consent_version VARCHAR(20) DEFAULT '1.0',  -- versión de la política de privacidad
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON consent_records (user_id, data_purpose, created_at DESC);
```

---

## TAREA 6 — Endpoint `/api/v1/admin/*` — verificar autenticación ADMIN obligatoria

El Sprint 4 implementará el panel admin. Antes de eso, verificar que el middleware RBAC
bloquea correctamente a no-admins:

```bash
grep -rn "require_role.*ADMIN\|UserRole.ADMIN" app/api/v1/admin*.py 2>/dev/null || echo "Panel admin aún no existe — OK"
```

**Acción requerida:** Crear el router base del panel admin con autenticación obligatoria:

```python
# app/api/v1/admin/__init__.py
from fastapi import APIRouter, Depends
from app.core.security import require_role, UserRole

admin_router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],  # ← TODOS los endpoints requieren ADMIN
)

# El endpoint de métricas del modelo ML es protegido (CLAUDE.md):
# "No exponer el endpoint /api/v1/model/metrics sin autenticación ADMIN"
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

```bash
# Tests de seguridad Sprint 4
pytest tests/unit/test_ws_connection_limit.py -v
pytest tests/unit/test_encryption.py -v
pytest tests/unit/test_rate_limiter.py -v

# Migración aplicada
alembic current

# Sin print() en archivos nuevos
grep -rn "print(" app/core/rate_limiter.py app/core/encryption.py app/core/consent.py

# Linting
ruff check app/core/rate_limiter.py app/core/encryption.py app/core/consent.py
```

**Archivos creados/modificados:**
- `app/core/encryption.py` — AES-256-GCM para campos sensibles
- `app/core/rate_limiter.py` — rate limiting por IP/usuario
- `app/core/consent.py` — guard de consentimiento Ley 29733
- `app/api/v1/ws_notifications.py` — límite 3 conexiones por usuario
- `app/api/v1/admin/__init__.py` — router admin con RBAC obligatorio
- `alembic/versions/XXXX_add_consent_records.py`
- `tests/unit/test_ws_connection_limit.py`
- `tests/unit/test_encryption.py`
- `tests/unit/test_rate_limiter.py`

---

**Cuando termines, el agente `python-pro` con skills `python-fastapi` y `senior-backend`
recibirá la instrucción 2 para implementar el panel admin DRTPE y los KPIs de la tesis.**
