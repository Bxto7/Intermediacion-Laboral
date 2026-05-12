# SPRINT 5 — INSTRUCCIÓN 5 de 6
# Agente: `api-documenter`
# Tarea: Documentación OpenAPI ≥ 50 endpoints + FastAPI metadata + colección Postman + diagramas Mermaid

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
Este es el sprint de cierre. La documentación debe cubrir todos los módulos implementados
en los Sprints 1–5 y servir tanto para el informe de tesis como para uso de la DRTPE-Junín.

---

## PARTE A — FastAPI: Metadata global de la API

Actualiza `app/main.py` con la metadata completa:

```python
# app/main.py — sección de configuración FastAPI

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

description = """
## Sistema de Intermediación Laboral ML/NLP — DRTPE-Junín

### Descripción
API para el sistema de intermediación laboral con inteligencia artificial articulado
con la Dirección Regional de Trabajo y Promoción del Empleo de Junín (DRTPE-Junín).

Implementado como parte de la investigación:
**"Implementación de un Sistema de Intermediación Laboral mediante Machine Learning
y NLP para la Reducción de Brechas de Acceso al Empleo en Articulación con la
Dirección Regional de Trabajo y Promoción del Empleo Junín"**

**Investigadores:** Rojas Peña, William Mikeiel | Tovar Sanchez, Carlos Alberto

### Tipos de usuario

| Tipo | Descripción |
|------|-------------|
| `primer_empleo` | Personas sin experiencia laboral previa |
| `experiencia` | Trabajadores con historial laboral |
| `oficio` | Trabajadores en oficios (electricista, gasfitero, carpintero, etc.) |

### Autenticación
Todos los endpoints protegidos requieren un JWT Bearer token.
Obtener token en: `POST /api/v1/auth/login`

### Módulos implementados
- **M01**: Identidad y Autenticación (RF001–RF015)
- **M02**: Perfil del Trabajador (RF016–RF035)
- **M03**: Empleadores y Ofertas (RF036–RF055)
- **M04**: NLP de Competencias (RF056–RF075)
- **M05**: Motor ML de Emparejamiento (RF076–RF095)
- **M06**: Asistente de Identidad Laboral (RF096–RF110)
- **M07**: Búsqueda y Recomendación (RF111–RF125)
- **M08**: Notificaciones (RF126–RF135)
- **M09**: Reportes DRTPE (RF136–RF145)
- **M10**: Equidad y Explicabilidad (RF146–RF155)
- **M11**: Administración (RF156–RF160)
- **M12**: Integración Institucional (RF161–RF165)

### Contacto institucional
- DRTPE-Junín: https://www.trabajo.gob.pe/junin
"""

tags_metadata = [
    {"name": "auth",          "description": "Autenticación y gestión de sesiones (M01/RF001–RF015)"},
    {"name": "onboarding",    "description": "Detección de tipo de usuario — primer paso obligatorio (M02/RF016–RF020)"},
    {"name": "workers",       "description": "Perfil del trabajador — CRUD y cambio de tipo (M02/RF021–RF035)"},
    {"name": "wizard",        "description": "Wizard guiado de CV para PRIMER_EMPLEO (M06/RF096–RF110)"},
    {"name": "employers",     "description": "Empleadores y publicación de ofertas (M03/RF036–RF055)"},
    {"name": "nlp",           "description": "Extracción de habilidades NLP (M04/RF056–RF075)"},
    {"name": "matching",      "description": "Motor de emparejamiento ML diferenciado (M05/RF076–RF095)"},
    {"name": "portfolio",     "description": "Portfolio visual para OFICIO (M06 parcial + M02)"},
    {"name": "marketplace",   "description": "Marketplace de servicios de oficio — EXCLUSIVO OFICIO (M07/RF118–RF125)"},
    {"name": "cv",            "description": "Generación de CVs PDF con WeasyPrint (M06/RF096–RF110)"},
    {"name": "alerts",        "description": "Alertas configurables de empleo (M07/RF111–RF117)"},
    {"name": "notifications", "description": "Notificaciones en tiempo real WebSocket (M08/RF126–RF135)"},
    {"name": "admin",         "description": "Panel DRTPE — KPIs de la tesis — solo ADMIN (M09/RF136–RF145)"},
    {"name": "moderation",    "description": "Moderación de contenido del marketplace"},
    {"name": "surveys",       "description": "Encuestas económicas — datos cifrados AES-256"},
    {"name": "privacy",       "description": "Privacidad y Ley 29733 — export y eliminación de datos"},
    {"name": "health",        "description": "Health checks para Cloud Run"},
]

app = FastAPI(
    title="DRTPE-Junín — Sistema de Intermediación Laboral ML/NLP",
    description=description,
    version="5.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "Equipo de Investigación DRTPE-Junín",
        "email": "investigacion@drtpe-junin.gob.pe",
    },
    license_info={
        "name": "Uso institucional — DRTPE-Junín",
    },
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
```

---

## PARTE B — Documentar todos los endpoints con Field descriptions

Para cada endpoint, agregar docstrings detallados y schemas con ejemplos:

**Patrón obligatorio para cada endpoint:**

```python
# ✅ Patrón de documentación completa
@router.post(
    "/api/v1/onboarding/detect-type",
    response_model=OnboardingResponse,
    summary="Detectar tipo de trabajador",
    description="""
    Clasifica al usuario en uno de los 3 tipos según sus respuestas:
    - **PRIMER_EMPLEO**: `is_first_job=true`
    - **OFICIO**: `is_first_job=false, is_trade_worker=true`
    - **EXPERIENCIA**: `is_first_job=false, is_trade_worker=false`
    
    El tipo se persiste en `workers.worker_type` y no puede cambiarse
    sin solicitud explícita (RF023).
    """,
    responses={
        200: {"description": "Tipo detectado exitosamente"},
        400: {"description": "Datos de entrada inválidos"},
        401: {"description": "Token JWT inválido o expirado"},
    },
)
```

**Schemas con ejemplos (Pydantic v2):**

```python
# app/schemas/onboarding.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class OnboardingAnswers(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "is_first_job": False,
            "is_trade_worker": True,
            "trade_category": "Electricidad",
        }
    })
    
    is_first_job: bool = Field(
        ...,
        description="True si el usuario busca su primer empleo",
        examples=[True, False],
    )
    is_trade_worker: bool = Field(
        default=False,
        description="True si trabaja en un oficio (solo aplica si is_first_job=False)",
    )
    trade_category: str | None = Field(
        default=None,
        description="Categoría del oficio. Requerido si is_trade_worker=True",
        examples=["Electricidad", "Gasfitería", "Carpintería"],
    )


class OnboardingResponse(BaseModel):
    worker_type: Literal["primer_empleo", "experiencia", "oficio"] = Field(
        ...,
        description="Tipo de trabajador detectado. Determina toda la experiencia en la plataforma.",
    )
    redirect_to: str = Field(
        ...,
        description="URL a la que el frontend debe redirigir al usuario",
        examples=["/wizard/step/1", "/oficio/portfolio", "/dashboard"],
    )
    message: str = Field(
        ...,
        description="Mensaje de bienvenida personalizado por tipo",
    )
```

**Hacer lo mismo para los schemas de TODOS los módulos:**
- `app/schemas/matching.py` — JobMatchResult, MatchResponse, MatchExplanation
- `app/schemas/portfolio.py` — PortfolioEntryCreate, PortfolioEntryResponse
- `app/schemas/admin.py` — DashboardResponse con descripción de cada KPI
- `app/schemas/workers.py` — WorkerProfileCreate, WorkerProfileResponse
- `app/schemas/cv.py` — GeneratedCVResponse
- `app/schemas/marketplace.py` — ServiceListingCreate, ServiceListingResponse

---

## PARTE C — Inventario de endpoints (≥ 50)

Verificar que todos estos endpoints están documentados en OpenAPI:

```bash
# Listar todos los endpoints registrados en FastAPI
python3 -c "
from app.main import app
routes = [(r.methods, r.path) for r in app.routes if hasattr(r, 'methods')]
for methods, path in sorted(routes, key=lambda x: x[1]):
    for method in sorted(methods):
        print(f'{method:6} {path}')
" | sort | uniq | wc -l
# Debe ser ≥ 50
```

**Endpoints esperados (lista de referencia):**

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout

POST   /api/v1/onboarding/detect-type

GET    /api/v1/workers/{worker_id}
PUT    /api/v1/workers/{worker_id}
DELETE /api/v1/workers/{worker_id}/account
POST   /api/v1/workers/{worker_id}/change-type
POST   /api/v1/workers/change-type/confirm/{request_id}

POST   /api/v1/wizard/step/{step_number}
GET    /api/v1/wizard/progress
POST   /api/v1/wizard/extract-skills

GET    /api/v1/jobs/feed
GET    /api/v1/jobs/{job_id}
POST   /api/v1/employers/register
POST   /api/v1/employers/{employer_id}/offers
GET    /api/v1/employers/{employer_id}/offers

POST   /api/v1/portfolio/entries
GET    /api/v1/portfolio/entries
GET    /api/v1/portfolio/entries/{entry_id}
PUT    /api/v1/portfolio/entries/{entry_id}
DELETE /api/v1/portfolio/entries/{entry_id}
GET    /api/v1/public/portfolio/{slug}

POST   /api/v1/marketplace/listings
GET    /api/v1/marketplace/search
GET    /api/v1/marketplace/listings/{listing_id}
PUT    /api/v1/marketplace/listings/{listing_id}
DELETE /api/v1/marketplace/listings/{listing_id}

GET    /api/v1/match/{worker_id}
GET    /api/v1/match/{worker_id}/equity-status

POST   /api/v1/cv/generate/{worker_id}
GET    /api/v1/cv/download/{cv_id}
POST   /api/v1/cv/parse-upload

POST   /api/v1/alerts
GET    /api/v1/alerts
DELETE /api/v1/alerts/{alert_id}

GET    /api/v1/notifications
PATCH  /api/v1/notifications/{notification_id}/read

POST   /api/v1/surveys/economic
GET    /api/v1/surveys/economic

GET    /api/v1/privacy/export-my-data
DELETE /api/v1/privacy/delete-my-account

POST   /api/v1/moderation/listings/{listing_id}/flag
GET    /api/v1/moderation/queue
POST   /api/v1/moderation/listings/{listing_id}/ban
POST   /api/v1/moderation/listings/{listing_id}/unban

GET    /api/v1/admin/dashboard
GET    /api/v1/admin/workers/stats
GET    /api/v1/admin/model/metrics
GET    /api/v1/admin/model/drift

POST   /api/v1/contracts
GET    /api/v1/contracts/worker/{worker_id}

GET    /api/v1/health
GET    /api/v1/ready

WS     /ws/notifications/{user_id}
```

---

## PARTE D — Exportar OpenAPI JSON

```bash
# Exportar el schema OpenAPI a un archivo estático
python3 -c "
import json
from app.main import app

openapi_schema = app.openapi()
with open('docs/openapi.json', 'w', encoding='utf-8') as f:
    json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

endpoint_count = sum(
    1 for path_data in openapi_schema.get('paths', {}).values()
    for method in ['get', 'post', 'put', 'patch', 'delete']
    if method in path_data
)
print(f'Total de endpoints documentados: {endpoint_count}')
assert endpoint_count >= 50, f'Se necesitan ≥ 50 endpoints, hay {endpoint_count}'
print('✅ Requisito cumplido: ≥ 50 endpoints')
"

mkdir -p docs/
```

---

## PARTE E — Colección Postman

Crea `docs/DRTPE_API.postman_collection.json`:

El archivo debe incluir las siguientes colecciones con variables de entorno:

```json
{
  "info": {
    "name": "DRTPE-Junín — Sistema de Intermediación Laboral",
    "description": "Colección completa de la API para el sistema ML/NLP de intermediación laboral DRTPE-Junín",
    "version": "5.0.0",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {"key": "base_url", "value": "http://localhost:8000", "type": "string"},
    {"key": "token", "value": "", "type": "string"},
    {"key": "worker_id", "value": "", "type": "string"}
  ],
  "item": [
    {
      "name": "1. Autenticación",
      "item": [
        {
          "name": "Register",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/v1/auth/register",
            "body": {
              "mode": "raw",
              "raw": "{\"email\": \"test@example.com\", \"password\": \"Password123!\"}",
              "options": {"raw": {"language": "json"}}
            }
          }
        },
        {
          "name": "Login",
          "event": [{"listen": "test", "script": {"exec": [
            "var resp = pm.response.json();",
            "pm.collectionVariables.set('token', resp.access_token);"
          ]}}],
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/v1/auth/login",
            "body": {
              "mode": "raw",
              "raw": "{\"email\": \"test@example.com\", \"password\": \"Password123!\"}",
              "options": {"raw": {"language": "json"}}
            }
          }
        }
      ]
    },
    {
      "name": "2. Onboarding",
      "item": [
        {
          "name": "Detectar tipo — PRIMER_EMPLEO",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/v1/onboarding/detect-type",
            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
            "body": {
              "mode": "raw",
              "raw": "{\"is_first_job\": true, \"is_trade_worker\": false}",
              "options": {"raw": {"language": "json"}}
            }
          }
        },
        {
          "name": "Detectar tipo — OFICIO",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/v1/onboarding/detect-type",
            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
            "body": {
              "mode": "raw",
              "raw": "{\"is_first_job\": false, \"is_trade_worker\": true, \"trade_category\": \"Electricidad\"}",
              "options": {"raw": {"language": "json"}}
            }
          }
        }
      ]
    },
    {
      "name": "3. Matching ML",
      "item": [
        {
          "name": "Obtener matches del trabajador",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/match/{{worker_id}}",
            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
          }
        },
        {
          "name": "Estado de equidad",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/match/{{worker_id}}/equity-status",
            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
          }
        }
      ]
    },
    {
      "name": "4. Admin — KPIs Tesis",
      "item": [
        {
          "name": "Dashboard con 7 KPIs",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/admin/dashboard",
            "header": [{"key": "Authorization", "value": "Bearer {{admin_token}}"}]
          }
        }
      ]
    }
  ]
}
```

---

## PARTE F — Diagramas Mermaid

Crea `docs/architecture/`:

### F1 — Diagrama de flujos de usuario

```bash
cat > docs/architecture/user_flows.mermaid << 'EOF'
flowchart TD
    START([Nuevo usuario]) --> REG[Registro]
    REG --> ONB{Onboarding\nDetección de tipo}
    
    ONB -->|is_first_job = true| PE[PRIMER_EMPLEO]
    ONB -->|is_trade_worker = true| OF[OFICIO]
    ONB -->|experiencia previa| EXP[EXPERIENCIA]
    
    PE --> WIZ[Wizard 6 pasos\nM06/RF096-110]
    WIZ --> PEDB[Dashboard\nCV + Orientación + Matches]
    
    OF --> PORT[Portfolio Visual\nM06+M02]
    PORT --> MARK[Marketplace\nM07/RF118-125]
    PORT --> OFCV[CV automático\nWeasyPrint]
    
    EXP --> UPLOAD{¿Tiene CV?}
    UPLOAD -->|Sí| PARSE[Parser PDF/DOCX\nM04/RF066-070]
    UPLOAD -->|No| MANUAL[Formulario\nmanual]
    PARSE --> EXPDB[Dashboard\nBolsa formal]
    MANUAL --> EXPDB
    
    PEDB --> MATCH[Motor ML\nM05/RF076-095]
    EXPDB --> MATCH
    MARK --> MATCH
    MATCH --> EXP_OUT[Explicaciones\nM10/RF146-155]
    
    style PE fill:#bee3f8
    style OF fill:#fefcbf
    style EXP fill:#e2e8f0
EOF
```

### F2 — Diagrama de arquitectura del sistema

```bash
cat > docs/architecture/system_architecture.mermaid << 'EOF'
graph TB
    subgraph Frontend["Frontend — React 18 + Vite"]
        ONB[Onboarding]
        WIZ[Wizard 6 pasos]
        PORT[Portfolio]
        MARK[Marketplace]
        DASH[Dashboard]
        ADM[Admin DRTPE]
    end
    
    subgraph API["Backend — FastAPI (Cloud Run)"]
        AUTH[Auth M01]
        WORK[Workers M02]
        JOB[Jobs M03]
        NLP_API[NLP M04]
        ML[Matching ML M05]
        CV[CV Builder M06]
        SEARCH[Search M07]
        NOTIF[Notif M08]
        ADMIN[Admin M09]
        EQ[Equity M10]
        DRTPE_INT[DRTPE M12]
    end
    
    subgraph ML_Stack["ML/NLP Stack"]
        EMB[sentence-transformers\nparaphrase-MiniLM-L12]
        SPA[spaCy es_core_news_md]
        GBM[GradientBoosting\nrandom_state=42]
        PSI[PSI Drift Detector]
    end
    
    subgraph Infra["Infraestructura GCP"]
        PG[(PostgreSQL 15\n+ pgvector\nCloud SQL)]
        REDIS[(Redis\nMemorystore)]
        GCS[GCS\nMedia Files]
        CEL[Celery Workers\n4 colas]
    end
    
    Frontend --> API
    API --> ML_Stack
    API --> Infra
    ML_Stack --> Infra
    CEL --> ML_Stack
    CEL --> Infra
    
    style Frontend fill:#ebf8ff
    style API fill:#e2e8f0
    style ML_Stack fill:#fff5f5
    style Infra fill:#f0fff4
EOF
```

### F3 — Diagrama del motor de matching

```bash
cat > docs/architecture/matching_engine.mermaid << 'EOF'
sequenceDiagram
    participant U as Usuario
    participant API as FastAPI
    participant ENG as MatchingEngine
    participant PG as PostgreSQL+pgvector
    participant ML as GradientBoosting
    participant EQ as EquityRanker
    participant EXP as Explainer
    
    U->>API: GET /api/v1/match/{worker_id}
    API->>ENG: match_worker_to_jobs(worker_id)
    
    ENG->>PG: Verificar embedding del worker
    alt Sin embedding (cold-start)
        ENG->>ENG: resolve_cold_start()
        ENG->>PG: Guardar embedding generado
    end
    
    ENG->>PG: Vector search cosine (top-50)
    PG-->>ENG: Candidatos con cosine_sim
    
    loop Para cada candidato
        ENG->>ML: predict_proba(feature_vector)
        ML-->>ENG: ml_score
        ENG->>ENG: combined_score(cosine, ml, reputation)
    end
    
    ENG->>EQ: apply_equity_reranking()
    EQ->>PG: Registrar equity_audit_log
    EQ-->>ENG: Resultados re-rankeados
    
    ENG->>EXP: build_match_explanation()
    EXP-->>ENG: Explicaciones en español coloquial
    
    ENG->>PG: Registrar match_events
    ENG-->>API: top-20 matches con explicaciones
    API-->>U: JSON con matches y explicaciones
EOF
```

---

## PARTE G — README.md final

Actualiza el `README.md` raíz del proyecto:

```markdown
# Sistema de Intermediación Laboral ML/NLP — DRTPE-Junín

**Investigación:** Implementación de un Sistema de Intermediación Laboral mediante
Machine Learning y NLP para la Reducción de Brechas de Acceso al Empleo en
Articulación con la DRTPE-Junín.

**Investigadores:** Rojas Peña, William Mikeiel | Tovar Sanchez, Carlos Alberto

## Documentación

| Documento | Descripción |
|-----------|-------------|
| `CLAUDE.md` | Fuente de verdad de arquitectura y convenciones |
| `docs/openapi.json` | Schema OpenAPI 3.0 (≥ 50 endpoints) |
| `docs/DRTPE_API.postman_collection.json` | Colección Postman para testing |
| `docs/architecture/` | Diagramas Mermaid del sistema |
| `SECURITY_AUDIT.md` | Auditoría de seguridad (ISO 27001 + Ley 29733) |
| `RUNBOOK.md` | Procedimientos de operación y incidentes |
| `SPRINT_3_SUMMARY.md` | Resumen Sprint 3 |

## Levantamiento rápido (desarrollo local)

```bash
cp .env.example .env
# Editar .env con tus valores locales

docker-compose up -d
sleep 15

# Migraciones
docker-compose exec api alembic upgrade head

# Seed de datos de investigación
docker-compose exec api python -m app.utils.seed_research

# Verificar
curl http://localhost:8000/api/v1/health
# → {"status":"ok","service":"drtpe-api"}

# Documentación interactiva
open http://localhost:8000/api/docs
```

## Tests

```bash
# Backend
pytest tests/ --cov=app --cov-fail-under=80

# Frontend
cd frontend && npm run test

# E2E
cd frontend && npx playwright test
```
```

---

## VERIFICACIONES FINALES

```bash
# Verificar que el schema OpenAPI tiene ≥ 50 endpoints
python3 -c "
import json
with open('docs/openapi.json') as f:
    schema = json.load(f)
count = sum(1 for p in schema['paths'].values() for m in ['get','post','put','patch','delete'] if m in p)
print(f'Endpoints: {count}')
assert count >= 50
print('✅ ≥ 50 endpoints documentados')
"

# Verificar diagramas Mermaid (sintaxis)
npx @mermaid-js/mermaid-cli -i docs/architecture/user_flows.mermaid -o /tmp/test.svg

# Verificar que el README existe
cat README.md | wc -l  # debe ser > 50 líneas
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `app/main.py` — metadata OpenAPI completa + tags
- `app/schemas/*.py` — Field descriptions y ejemplos en todos los schemas
- `docs/openapi.json` — Schema exportado (≥ 50 endpoints)
- `docs/DRTPE_API.postman_collection.json` — Colección Postman completa
- `docs/architecture/user_flows.mermaid`
- `docs/architecture/system_architecture.mermaid`
- `docs/architecture/matching_engine.mermaid`
- `README.md` — actualizado con guía completa

---

**Cuando termines, el agente `python-pro` con skill `senior-backend` recibirá la instrucción 6
(la última del sistema) para los tests finales, SPRINT_SUMMARY.md y el git tag v5.0.0.**
