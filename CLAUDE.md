# CLAUDE.md — Linku · Sistema de Intermediación Laboral ML/NLP
# DRTPE-Junín | Huancayo, Perú | 2026
# Última actualización: 2026-05-31 — Sprint 5

---

## 🎯 MISIÓN DE ESTE ARCHIVO

Fuente única de verdad para Claude Code en este proyecto. **Antes de escribir código, lee este archivo completo.**

Este documento describe el **estado REAL del código** (verificado contra el repositorio), no aspiraciones. Cuando encuentres una discrepancia entre este archivo y el código, **el código manda** — y debes actualizar este archivo.

---

## 🏗️ VISIÓN DEL PRODUCTO

**Marca comercial:** **Linku** (componente `LinkuLogo` en frontend).
**Título oficial:** "Sistema de Intermediación Laboral DRTPE-Junín" (título de la app FastAPI).
**Título académico:** IMPLEMENTACIÓN DE UN SISTEMA DE INTERMEDIACIÓN LABORAL MEDIANTE MACHINE LEARNING Y NLP PARA LA REDUCCIÓN DE BRECHAS DE ACCESO AL EMPLEO — DRTPE Junín.

**Propósito:** Plataforma de intermediación laboral inteligente que conecta trabajadores (incluidos oficios informales sin perfil digital) con empleadores, usando NLP (embeddings) y ML para construir, representar y emparejar perfiles. Opera en articulación con la DRTPE-Junín.

### Roles del sistema (enum real `UserRole` en `core/security.py`)
- `WORKER` (trabajador, valor por defecto)
- `EMPLOYER` (empleador)
- `ADMIN` (administrador DRTPE)
- `MODERATOR` (moderador)

### ⭐ CONCEPTO CENTRAL: 3 tipos de trabajador (`worker_type`)
Esto es el corazón del producto y NO existía en versiones previas de este doc. El campo `Worker.worker_type` determina el flujo, el template de CV y los pesos de matching:

| `worker_type`  | Quién es | Flujo de perfil | Template CV |
|----------------|----------|-----------------|-------------|
| `primer_empleo` | Joven sin experiencia formal | Wizard de 6 pasos (NLP-asistido) | `primer_empleo.html` |
| `oficio`        | Trabajador de oficio informal (carpintero, electricista…) | Portafolio de trabajos | `oficio.html` |
| `experiencia`   | Profesional con CV/experiencia formal | Parseo de CV (PDF/DOCX) | `experiencia.html` |

El tipo se determina en onboarding: `POST /api/v1/onboarding/detect-type`.

---

## 📁 ESTRUCTURA REAL DEL PROYECTO

```
App-Intermediacion-Laboral/
├── backend/
│   ├── app/
│   │   ├── main.py                 # Entry FastAPI (lifespan, CORS, health, router mount /api/v1)
│   │   ├── api/v1/                 # Routers (cada uno define su propio prefix)
│   │   │   ├── router.py           # Agregador: incluye todos los routers
│   │   │   ├── auth.py             # /auth   (register, login, refresh, logout, verify-email, me…)
│   │   │   ├── onboarding.py       # /onboarding (detect-type)
│   │   │   ├── workers.py          # /workers (profile, completeness)
│   │   │   ├── employers.py        # /employers
│   │   │   ├── jobs.py             # /jobs (feed, view)
│   │   │   ├── nlp.py              # /nlp (extract-skills/wizard, parse-cv, extract-skills/portfolio…)
│   │   │   ├── wizard.py           # /wizard (primer_empleo)
│   │   │   ├── portfolio.py        # /portfolio (oficio)
│   │   │   ├── cv.py               # /cv (generate/{id}, download/{id})  ← GENERACIÓN PDF
│   │   │   ├── alerts.py           # /alerts
│   │   │   ├── matching.py         # /match (top-K ofertas con score)
│   │   │   ├── marketplace.py      # /marketplace (servicios de oficio)
│   │   │   ├── applications.py     # /applications
│   │   │   ├── contracts.py        # /contracts
│   │   │   ├── surveys.py          # /surveys (encuesta económica)
│   │   │   ├── ws_notifications.py # /ws (WebSocket notificaciones)
│   │   │   └── admin/dashboard.py  # /admin (dashboard, stats)
│   │   ├── core/
│   │   │   ├── config.py           # Settings (Pydantic v2) — TODAS las env vars
│   │   │   ├── database.py         # AsyncSession, engine, init_db
│   │   │   ├── security.py         # JWT RS256, AES-256-GCM PII, require_role, UserRole
│   │   │   ├── security_headers.py # Middleware de headers
│   │   │   ├── rate_limit.py       # Rate limiting (Redis)
│   │   │   ├── redis_client.py     # Cliente Redis
│   │   │   └── logging.py          # structlog
│   │   ├── models/                 # SQLAlchemy 2 async (ver tabla más abajo)
│   │   ├── schemas/                # Pydantic v2 (common.py tiene enums UserRole/WorkerType/District…)
│   │   ├── services/
│   │   │   ├── cv_builder/pdf_generator.py   # ← generate_cv_pdf() WeasyPrint+Jinja2
│   │   │   ├── cv_builder/wizard_service.py
│   │   │   ├── matching/job_alerts.py
│   │   │   ├── onboarding/detector.py
│   │   │   ├── marketplace/marketplace_service.py
│   │   │   ├── reports/kpi_calculator.py
│   │   │   └── storage.py
│   │   ├── nlp/
│   │   │   ├── embeddings/generator.py        # sentence-transformers, normalize_text, fallback hash
│   │   │   ├── cv_parser/parser.py            # parse_pdf, parse_docx, extract_cv_fields
│   │   │   ├── skill_extractor/first_job_extractor.py
│   │   │   └── portfolio_nlp/trade_extractor.py
│   │   ├── ml/
│   │   │   ├── matching_engine/scorer.py      # combined_score (pesos por worker_type)
│   │   │   ├── equity_ranker/ranker.py        # disparate impact, re-ranking de equidad
│   │   │   ├── explainer/explainer.py         # explain_match
│   │   │   └── cold_start/resolver.py
│   │   ├── tasks/                  # Celery (ver colas más abajo)
│   │   │   ├── __init__.py         # App Celery (broker/backend Redis) — USAR ESTE
│   │   │   ├── cv_generator.py     # generate_cv_task (cola cv_generation)
│   │   │   ├── embeddings.py       # generate_*_embedding (cola embeddings)
│   │   │   ├── notifications.py    # STUBS (solo loguean)
│   │   │   └── reports.py
│   │   ├── utils/cv_templates/     # ← PLANTILLAS PDF: primer_empleo.html, oficio.html, experiencia.html
│   │   ├── utils/local_dict/huancayo_trades.json  # diccionario de oficios locales
│   │   └── integrations/drtpe/     # conector DRTPE
│   ├── migrations/                 # Alembic
│   ├── tests/                      # pytest (unit/ + integration/)
│   ├── keys/                       # RSA private.pem/public.pem (auto-generadas, NO commitear)
│   ├── scripts/init.sql            # init de BD (montado en el contenedor db)
│   ├── requirements.txt
│   ├── Dockerfile                  # python:3.11-slim-bookworm + libs WeasyPrint
│   └── .dockerignore
├── frontend/                       # Vite 6 + React 18 + TypeScript 5
│   ├── src/
│   │   ├── main.tsx                # Entry (IntlProvider es-PE, providers)
│   │   ├── App.tsx                 # Router raíz (rutas + guards)
│   │   ├── api/client.ts           # Axios: baseURL ${VITE_API_URL}/api/v1, interceptores JWT/401
│   │   ├── context/AuthContext.tsx # login/register/logout/user
│   │   ├── context/WorkerContext.tsx
│   │   ├── guards/                 # AuthGuard, WorkerTypeGuard, AdminGuard
│   │   ├── pages/                  # LoginPage, RegisterPage, LandingPage, PublicPortfolioPage…
│   │   ├── onboarding/OnboardingPage.tsx
│   │   ├── modules/
│   │   │   ├── primer-empleo/wizard/   # WizardLayout + 6 steps (Step6 = generar PDF)
│   │   │   ├── oficio/portfolio/ + marketplace/
│   │   │   └── experiencia/
│   │   ├── employer/ + pages/employer/  # dashboard, publish, candidates, messages
│   │   ├── admin/                  # AdminDashboard, KPIGlobe.tsx (Three.js), WorkersAdmin…
│   │   ├── matching/MatchesPage.tsx
│   │   ├── store/wizardStore.ts    # Zustand (persist localStorage)
│   │   ├── shared/                 # AppShell, NavBar, LinkuLogo, NotificationBell…
│   │   └── i18n/es-PE.json         # único idioma
│   ├── package.json
│   └── vite.config.ts              # dev port 5173, proxy /api → http://api:8000
├── docker-compose.yml              # stack completo de desarrollo
├── docker-compose.staging.yml
├── nginx/  infra/  monitoring/  docs/
├── sonar-project.properties        # config SonarQube (ver sección Calidad)
└── CLAUDE.md                       # este archivo
```

---

## 🔧 STACK TECNOLÓGICO REAL

### Backend (`requirements.txt`)
- **Python 3.11** · **FastAPI 0.115** · **Uvicorn 0.32**
- **SQLAlchemy 2.0 async** + **asyncpg** (PostgreSQL) · **Alembic 1.14**
- **PostgreSQL 15 con pgvector** (imagen `pgvector/pgvector:pg15`) — embeddings `Vector(384)`
- **Pydantic v2** (2.10) + pydantic-settings
- **Redis 7** (broker + cache) · **Celery 5.4** (tareas async)
- **Auth:** python-jose (JWT **RS256**) · passlib + **bcrypt** (cost 12) · AES-256-GCM para PII
- **NLP/ML:** sentence-transformers 3.3 (`paraphrase-multilingual-MiniLM-L12-v2`, dim 384) · spaCy 3.8 · scikit-learn 1.6 · nltk · shap · ftfy
- **PDF:** **WeasyPrint ≥62.3 + Jinja2** (requiere libs del sistema: libpango, libcairo, libgdk-pixbuf — ver Dockerfile)
- **Obs:** structlog · prometheus-fastapi-instrumentator · mlflow-skinny · slowapi (rate limit)
- **No hay OCR** (pytesseract NO está en dependencias — el CLAUDE anterior lo mencionaba; es incorrecto).

### Frontend (`package.json`)
- **Vite 6.0** · **React 18.3** · **TypeScript 5.7** · **puerto dev 5173**
- **react-router-dom 7** · **Zustand 5** (persist localStorage) · **Axios 1.7** (interceptores)
- **Tailwind 3.4** + **shadcn/ui** + Radix + **lucide-react** · **Framer Motion**
- **react-hook-form + Zod** (formularios) · **react-intl** (i18n, solo `es-PE`)
- **Three.js + @react-three/fiber** (componente `KPIGlobe` en admin) · **Recharts** · react-dropzone

### Infra
- Docker + Docker Compose · Prometheus + Grafana · Nginx · Flower (monitoreo Celery)

---

## 🚀 COMANDOS DE DESARROLLO (verificados contra docker-compose.yml)

```bash
cd "d:/App-Intermediacion Laboral"

# Levantar todo (build la primera vez)
docker-compose up -d --build

# Logs
docker-compose logs -f api
docker-compose logs -f frontend

# Detener
docker-compose down

# Migraciones Alembic
docker-compose exec api alembic upgrade head
docker-compose exec api alembic revision --autogenerate -m "descripcion"

# Tests + cobertura
docker-compose exec api pytest tests/ -v
docker-compose exec api pytest --cov=app --cov-report=xml   # genera backend/coverage.xml

# Shell
docker-compose exec api bash
```

### Puertos expuestos
| Servicio   | Host  | Notas |
|------------|-------|-------|
| API        | 8000  | docs en `http://localhost:8000/api/docs` (solo dev) |
| Frontend   | 5173  | Vite dev server |
| PostgreSQL | 5433 → 5432 | usuario/clave `postgres/postgres`, BD `intermediacion_laboral` |
| Redis      | 6379  | |
| Flower     | 5555  | monitoreo Celery |
| Prometheus | 9090  | |
| Grafana    | 3001 → 3000 | admin/changeme |
| SonarQube  | 9000  | contenedor aparte (no en compose) — ver sección Calidad |

> ⚠️ **NOTA build:** el Dockerfile fija `python:3.11-slim-bookworm` y conmuta los repos apt a **HTTPS** (`sed ... debian.sources`) porque en algunas redes el puerto 80 de `deb.debian.org` está bloqueado (403 Forbidden). No revertir a `python:3.11-slim` a secas.

---

## 🔐 AUTENTICACIÓN — ESTADO REAL

### Implementación (`core/security.py`, `api/v1/auth.py`)
- **JWT RS256** con par de claves RSA en `backend/keys/private.pem` / `public.pem`.
  - Si no existen, se **auto-generan** al iniciar (`_ensure_rsa_keys()`).
- **access_token**: expira en `ACCESS_TOKEN_EXPIRE_MINUTES` (default **1440 = 24h**).
- **refresh_token**: expira en `REFRESH_TOKEN_EXPIRE_DAYS` (default **7 días**).
- Ambos tokens incluyen `sub` (user_id), `role`, `jti`, `type`.
- **Logout** invalida el `jti` en una blacklist Redis.
- **PII** (full_name, dni, phone) se cifra con **AES-256-GCM** y se guarda como `BYTEA`.
- **Rate limiting** (Redis): register 10/h por IP, login 20/h por IP, forgot-password 5/h.

### Endpoints reales (prefijo `/api/v1/auth`)
```
POST /api/v1/auth/register
POST /api/v1/auth/login            Body: { "email", "password" }
                                   200: { "access_token", "refresh_token", "token_type": "bearer", ... }
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/verify-email
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
GET  /api/v1/auth/me
```

### ⚠️ Diferencias con la "regla de negocio" ideal (a tener en cuenta)
- **NO existe** un estado `PENDIENTE_VERIFICACION` que bloquee el login. Hay solo un booleano `User.email_verified`. El login **no** exige email verificado actualmente.
- El envío real de emails (verificación, reset) es un **STUB** en `tasks/notifications.py` (solo loguea). No hay SMTP configurado.

### Frontend del login (`pages/LoginPage.tsx`, `context/AuthContext.tsx`, `api/client.ts`)
- Llama `POST {VITE_API_URL}/api/v1/auth/login`. **Default `VITE_API_URL = http://localhost:8000`**.
- Tiene estado `isSubmitting` (spinner) y `error`.
- Guarda `access_token` y `refresh_token` en **localStorage**.
- **Redirección post-login:** `sessionStorage.login_return_url` si existe, si no → **`/dashboard`** (NO `/dashboard/trabajador`). El reparto por tipo de trabajador se hace en **`/onboarding`** y los guards.
- Interceptor Axios: en **401** limpia tokens y redirige a `/login`. **OJO: no hay refresh automático** del access token; al expirar, el siguiente 401 desloguea. (Mejora pendiente.)

### Mapa de redirección real
```
Login OK → /dashboard
  ↳ Worker sin tipo definido → /onboarding → detect-type:
        primer_empleo → /wizard/step/1
        oficio        → /oficio/portfolio
        experiencia   → /dashboard
  ↳ Employer → /employer/dashboard
  ↳ Admin    → /admin
```

---

## 🗄️ MODELOS DE BD (PostgreSQL + pgvector)

BD real: **`intermediacion_laboral`**. Columnas `embedding Vector(384)` donde se indica.

| Tabla | Campos clave |
|-------|--------------|
| `users` | id (UUID), email (único), hashed_password, role, is_active, email_verified |
| `workers` | id, user_id (FK), **worker_type**, full_name/dni/phone (BYTEA cifrado), district, trade_category, years_experience, avg_rating, is_available, profile_completeness, **embedding**, bio, job_title, username (único) |
| `employers` | id, user_id, company_name, ruc (cifrado), contact_name (cifrado), district, sector, is_verified |
| `job_offers` | id, employer_id, title, description, required_skills/preferred_skills (JSONB), district, modality, salary_min/max, worker_type_target, is_active, expires_at, **embedding**, views_count, applications_count |
| `applications` | id, worker_id, job_offer_id, status (enviada/en_revision/entrevista/descartada/contratada), match_score, cover_note, employer_notes |
| `portfolio_entries` | id, worker_id, title, description, extracted_skills (JSONB), photos (JSONB), period_start/end, client_rating, is_public, **embedding** |
| `wizard_progress` | id, worker_id (único), current_step, answers (JSONB), extracted_skills (JSONB), job_interests (JSONB) |
| `service_listing` | id, worker_id, title, description, trade_category, enriched_keywords (JSONB), **embedding** |
| otras | contracts, audit_log, notification, match_event, job_alert, search_log, tracking, consent_record, economic_survey, equity_audit_log, generated_cv, model_version |

---

## 📄 GENERACIÓN DE PDF / CV — FLUJO CRÍTICO (RF096-RF110)

Esta sección es prioritaria para auditoría. Tecnología: **WeasyPrint + Jinja2**.

### Componentes
- **Plantillas:** `backend/app/utils/cv_templates/{primer_empleo,oficio,experiencia}.html`
- **Generador:** `backend/app/services/cv_builder/pdf_generator.py` → `generate_cv_pdf(worker_id, db) -> bytes`
- **Endpoint API:** `backend/app/api/v1/cv.py`
- **Tarea async:** `backend/app/tasks/cv_generator.py` → `generate_cv_task` (cola `cv_generation`, worker-cv)
- **Frontend:** `frontend/src/modules/primer-empleo/wizard/steps/Step6Preview.tsx`

### Flujo
```
[Wizard Step 6 / dashboard]
   ↓ POST /api/v1/cv/generate/{worker_id}     (async, encola Celery → { task_id, status:"processing" })
   ↓ GET  /api/v1/cv/download/{worker_id}     (SÍNCRONO: genera y devuelve application/pdf en el request)
[Descarga del PDF]
```
- `generate_cv_pdf` selecciona el template por `worker.worker_type` (`TEMPLATE_MAP`, fallback `experiencia.html`).
- Construye el contexto (`_build_template_context`): descifra PII, busca email vía `users`, y según el tipo arma:
  - **primer_empleo:** skills + education/activities/objective desde `wizard_progress.answers`.
  - **oficio:** hasta 6 `portfolio_entries` públicas + trade_category, rating, slug público.
  - **experiencia:** job_title, bio, years_experience desde `Worker`.
- Si WeasyPrint no está disponible (faltan libs del sistema) lanza `RuntimeError` con mensaje claro.
- Autorización: ambos endpoints requieren rol `WORKER` y verifican `worker.user_id == token.sub` (un trabajador solo genera **su** CV).

### ⚠️ Riesgos conocidos del PDF a vigilar en auditoría
1. **`download` es síncrono** y ejecuta WeasyPrint dentro del request → puede bloquear/timeout con carga. Apropiado para dev; en prod debería servirse desde el resultado de la tarea Celery / storage.
2. Las plantillas HTML carecían de `<title>` (3 bugs MAJOR detectados por SonarQube). Verificar si ya están corregidas.
3. WeasyPrint **depende de libs del SO**: el contenedor `api` y `worker-cv` deben tener las libs del Dockerfile. Si el PDF falla con `RuntimeError`, revisar la imagen.
4. Para `oficio`/`experiencia` el contexto depende de datos opcionales (`getattr` con defaults) → un perfil incompleto genera un PDF pobre pero no debe romper.

### Cómo PROBAR la generación de PDF (manual)
```bash
# 1. Login y captura del token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<email>","password":"<pass>"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2. Descargar el CV (síncrono) — debe devolver un PDF válido
curl -s -D - -o /tmp/cv.pdf \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/cv/download/<WORKER_ID>

# 3. Verificar que es un PDF real (cabecera %PDF y tamaño > 0)
head -c 5 /tmp/cv.pdf   # debe imprimir: %PDF-
```
Criterios de aceptación: HTTP 200, `Content-Type: application/pdf`, archivo empieza con `%PDF-`, tamaño > 1 KB, abre sin corrupción.

---

## 🤖 ML / NLP — ESTADO REAL

- **Embeddings (REAL):** `nlp/embeddings/generator.py`, modelo `paraphrase-multilingual-MiniLM-L12-v2` (dim 384). Normalización con ftfy + nltk + diccionario `huancayo_trades.json`. **Fallback hash SHA256** si el modelo no carga (para no romper).
- **Skill extraction (REAL):** `first_job_extractor.py` (wizard), `trade_extractor.py` (portfolio).
- **CV parsing (parcial):** `cv_parser/parser.py` (`parse_pdf`, `parse_docx`, `extract_cv_fields`) para tipo `experiencia`.
- **Matching:** `ml/matching_engine/scorer.py` → `combined_score = α·cosine + β·ml_score + γ·(reputation/5)`.
  - Pesos por tipo: primer_empleo (0.65, 0.35, 0.00) · experiencia (0.50, 0.30, 0.20) · oficio (0.45, 0.25, 0.30).
  - ⚠️ **`ml_score` está fijo en 0.5 (STUB)** en `api/v1/matching.py` — el modelo ML supervisado aún no está entrenado/cargado. La similitud coseno (pgvector) sí es real.
- **Equidad:** `ml/equity_ranker/ranker.py` calcula *disparate impact* (< 0.80 dispara re-ranking) y registra `equity_audit_log`.
- **Explainability:** `ml/explainer/explainer.py` (`explain_match`).
- Endpoints NLP reales: `POST /api/v1/nlp/extract-skills/wizard`, `POST /api/v1/nlp/parse-cv`, `POST /api/v1/nlp/extract-skills/portfolio`.

> ⚠️ **Posible desajuste front/back a verificar:** el frontend (Step3 del wizard) parece llamar `POST /nlp/extract-skills` con body `{user_text, worker_type}`, pero el backend expone `POST /nlp/extract-skills/wizard` con body `{step, text}`. Confirmar en auditoría que la ruta y el payload coinciden; si no, es un bug de integración.

---

## ⚙️ CELERY — colas y tareas reales

App Celery: `app/tasks/__init__.py` (broker y backend en Redis). **No usar** `celery_app.py` (deprecado).

| Cola | Worker (compose) | Tareas |
|------|------------------|--------|
| `embeddings` | worker-embeddings | generate_worker/job/portfolio/listing_embedding, regenerate_all_embeddings |
| `cv_generation` | worker-cv | generate_cv_task |
| `notifications`, `default` | worker-notifications | send_reset_email, send_push_notification, notify_* (**STUBS**) |
| `reports` | worker-reports | generate_research_dataset |

**Celery Beat** (scheduler, TZ America/Lima): regenerar embeddings (02:00), procesar alertas (cada hora), KPIs (06:00), reindexar marketplace (03:00), reentrenar matching (lun 04:00), limpiar tokens (01:00).

---

## 🌐 VARIABLES DE ENTORNO REALES

### Backend (`core/config.py`) — env file: `backend/.env`
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/intermediacion_laboral
REDIS_URL=redis://redis:6379/0
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=keys/private.pem
JWT_PUBLIC_KEY_PATH=keys/public.pem
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
AES_KEY=<base64 de 32 bytes>          # PII; cambiar en prod
BCRYPT_COST=12
ENVIRONMENT=development                # o "production"
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:5173  # usado solo si ENVIRONMENT=production
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIM=384
GCS_BUCKET_NAME=intermediacion-laboral-dev
```
> En `development`, CORS está **hardcodeado** a `http://localhost:5173` en `main.py` (no usa `ALLOWED_ORIGINS`).

### Frontend — `frontend/.env` (NO existe aún; crear si se necesita override)
```env
VITE_API_URL=http://localhost:8000     # default si no se define
```

---

## 📋 CONVENCIONES DE CÓDIGO

### Python / FastAPI
- `snake_case` funciones, `PascalCase` clases. Type hints + docstrings (Google style) en funciones públicas.
- Rutas: cada router define su `prefix` (ej. `APIRouter(prefix="/cv")`); se montan bajo `/api/v1` en `main.py`.
- Errores con `HTTPException`. Logging con `structlog` (`logger.info("evento", clave=valor)`).
- Async en todo el path de I/O (DB con `AsyncSession`, `await db.execute(select(...))`).
- **Nunca** exponer `hashed_password`, claves ni PII en respuestas.
- SQL siempre parametrizado vía SQLAlchemy (no concatenar).

### Frontend (React/TS)
- Componentes `PascalCase`, hooks `useX`. Llamadas HTTP vía `api/client.ts` o hooks/services, no en componentes sueltos.
- Manejar siempre `loading` / `error` / `data`. Textos en **español peruano** (DNI, S/., boleta).
- Estado de wizard en Zustand (`store/wizardStore.ts`, persistido).

### Git
- Commits en español: `feat:`, `fix:`, `chore:`. Branches: `feature/…`, `fix/…`, `hotfix/…`.
- No commitear: `.env`, `keys/`, `settings.local.json`, `__pycache__/`, `*.pyc`.

---

## ✅ CALIDAD — SonarQube (configurado)

Servidor SonarQube en Docker (contenedor `sonarqube`, no en compose), config en `sonar-project.properties`.

```bash
# Levantar SonarQube (una vez)
docker run -d --name sonarqube -p 9000:9000 \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true sonarqube:lts-community
# Esperar a status UP: curl -s http://localhost:9000/api/system/status

# Analizar (token desde la UI o API)
docker run --rm --network host -v "$PWD:/usr/src" \
  -e SONAR_HOST_URL=http://localhost:9000 -e SONAR_TOKEN=<token> \
  sonarsource/sonar-scanner-cli:latest
```
- Cobertura backend: generar `backend/coverage.xml` con `pytest --cov=app --cov-report=xml` (lo lee `sonar.python.coverage.reportPaths`).
- Cobertura frontend: `frontend/coverage/lcov.info` (`npm run test -- --coverage`, si hay tests).
- Último análisis (2026-05-31): Quality Gate **OK**, 0 vulnerabilidades, Rating Seguridad **A**, Mantenibilidad **A**, Fiabilidad **C** (3 bugs HTML `<title>` en templates de CV), 40 code smells, 1 security hotspot en `portfolio.py:320`.
- Acceso UI: `http://localhost:9000` (admin / `Linku2026!`).

---

## 🩺 PROTOCOLO DE AUDITORÍA TOTAL — SIMULANDO UN USUARIO

Cuando el usuario pida "auditoría", "revisar el flujo completo" o "auditoría de producción", recorre el sistema **como lo haría un usuario real**, end-to-end, y reporta evidencia (status HTTP, capturas de respuesta, logs). Orden de prioridad: **Auth → Onboarding → Perfil/Wizard → PDF → Vacantes → Matching → Postulación → Admin**.

### Paso 0 — Diagnóstico de salud
```bash
docker-compose ps
docker-compose logs --tail=50 api
curl -s http://localhost:8000/api/v1/health        # { status:"ok", ... }
curl -s http://localhost:8000/api/docs > /dev/null  # OpenAPI accesible en dev
```
Verifica que arrancaron `db`, `redis`, `api`, `frontend` y los `worker-*`. Si un worker está `Exited`, los flujos async (CV, embeddings) fallarán.

### Paso 1 — Auth (registro + login + me) como usuario
Para cada rol (worker, employer):
```bash
# Registro
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"audit_worker@test.pe","password":"Audit2026","role":"WORKER", ...}'
# Login → guarda access_token
# GET /me con el token → 200 y datos correctos (sin password_hash)
```
Verifica: status 2xx, token válido (decodifica el JWT y comprueba `role`/`exp`), errores específicos (401 credenciales, 422 validación), rate limiting tras múltiples intentos.

### Paso 2 — Onboarding (detect-type)
```bash
curl -s -X POST http://localhost:8000/api/v1/onboarding/detect-type \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{...respuestas...}'   # debe devolver worker_type ∈ {primer_empleo, oficio, experiencia}
```
Verifica en frontend que la redirección coincide (primer_empleo→/wizard/step/1, oficio→/oficio/portfolio, experiencia→/dashboard).

### Paso 3 — Construcción de perfil (los 3 tipos)
- **primer_empleo:** recorre el wizard de 6 pasos. En Step3 confirma que la **extracción NLP de skills** responde (revisa ruta/payload front vs back — ver advertencia en sección ML/NLP). Verifica que `wizard_progress` persiste.
- **oficio:** crea entradas de portafolio (`/portfolio`), confirma extracción de skills y que `is_public` controla visibilidad.
- **experiencia:** sube un CV (PDF/DOCX) a `/nlp/parse-cv`, valida los campos extraídos.

### Paso 4 — Generación de PDF (CRÍTICO) — para cada worker_type
Sigue "Cómo PROBAR la generación de PDF" (sección PDF). Para los 3 tipos:
- `POST /cv/generate/{id}` → `task_id` y, si hay worker-cv, la tarea termina (revisa Flower :5555).
- `GET /cv/download/{id}` → archivo `%PDF-`, `application/pdf`, abre correctamente, contenido coherente con el tipo (skills, portafolio o bio según corresponda).
- Verifica autorización: con el token de **otro** worker debe dar **403**.
- Verifica que las plantillas tienen `<title>` (bug SonarQube) y que un perfil incompleto no rompe la generación.

### Paso 5 — Vacantes (empleador)
```bash
# Crear oferta como employer → genera embedding (cola embeddings)
# GET /jobs/feed → la oferta aparece
```
Verifica creación, validaciones (descripción mínima), expiración, y que el embedding se generó (worker-embeddings activo).

### Paso 6 — Matching
```bash
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/match/<WORKER_ID>
```
Verifica top-K ordenado por score, que el score es 0-1, y **anota que `ml_score` es stub (0.5)** — el ranking real lo domina la similitud coseno. Revisa que el re-ranking de equidad no rompa el orden.

### Paso 7 — Postulación
`POST /applications` desde worker → aparece en "mis postulaciones" y en candidatos del empleador, con `status` correcto. Verifica notificación (stub: solo log).

### Paso 8 — Admin DRTPE
Login admin → `GET /api/v1/admin/dashboard` y stats. En frontend, `/admin` con `KPIGlobe` (Three.js) renderiza sin errores de consola.

### Paso 9 — Transversal (seguridad/UX)
- CORS: el front en :5173 puede llamar al API :8000 sin error CORS.
- 401: token expirado/invalid → front limpia sesión y va a `/login`.
- Autorización por rol: un worker no accede a endpoints de employer/admin (403).
- No hay PII ni secretos en respuestas ni en `console.log`.
- Estados `loading`/`error` visibles en cada acción del front.

### Entregable de la auditoría
Para cada flujo: ✅/❌, evidencia (status + extracto de respuesta/log), y si ❌: causa raíz + archivo:línea + propuesta de fix. Registrar nuevos hallazgos en la tabla de bugs.

---

## 🚨 BUGS / DEUDA CONOCIDA

| ID | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|
| BUG-001 | Botón "Iniciar Sesión" estático (histórico) | 🔴 | ✅ Resuelto (login funciona: spinner + redirect a `/dashboard`) |
| SONAR-1 | Templates de CV sin `<title>` (3 bugs MAJOR) — `cv_templates/*.html` | 🟡 | ✅ Resuelto (2026-05-31, `<title>` añadido a los 3) |
| SONAR-2 | Security hotspot directorio escribible — `api/v1/portfolio.py:320` | 🟡 | Revisar |
| ML-STUB | `ml_score` fijo 0.5 en `api/v1/matching.py` (modelo no entrenado) | 🟡 | Pendiente (entrenar/cargar) |
| INT-NLP | Posible desajuste ruta/payload `extract-skills` front (`/nlp/extract-skills`) vs back (`/nlp/extract-skills/wizard`) | 🟠 | Verificar en auditoría |
| AUTH-REFRESH | No hay refresh automático de access token; 401 desloguea | 🟡 | Mejora pendiente |
| CV-EXP-VACIO | El CV tipo `experiencia` siempre sale sin experiencia/educación/skills: `_build_template_context` ([pdf_generator.py:152-168](backend/app/services/cv_builder/pdf_generator.py#L152)) no cablea los datos parseados de `/nlp/parse-cv` | 🟠 | Pendiente |
| NOTIF-STUB | Emails/push son stubs (solo log); sin SMTP | 🟢 | Por implementar |

---

## 💡 MODO DE TRABAJO PARA CLAUDE CODE

### Al iniciar sesión de trabajo
1. Leer este `CLAUDE.md` completo.
2. `docker-compose ps` y `docker-compose logs --tail=20 api`.
3. Preguntar al usuario qué flujo/bug trabajar.

### Al auditar
1. Usar modelo **Opus** para análisis complejos.
2. Seguir el Protocolo de Auditoría Total (arriba), simulando usuario, en orden de prioridad.
3. Por flujo: leer código → reproducir como usuario → identificar problema (archivo:línea) → proponer → implementar → verificar.
4. No tocar más de un flujo por sesión sin confirmar.

### Al encontrar un bug
1. Registrarlo en la tabla de bugs.
2. Branch `fix/descripcion`. Corrección + test. Commit en español.

### Al cerrar sesión
1. Actualizar "Última actualización" y Sprint arriba.
2. Actualizar la tabla de bugs.
3. **Si el código cambió de forma que este archivo quedó desfasado, actualizar las secciones afectadas.**

---

## 📞 CONTEXTO INSTITUCIONAL

- **Institución:** Dirección Regional de Trabajo y Promoción del Empleo de Junín (DRTPE-Junín), Huancayo, Perú.
- **Contexto:** alta informalidad laboral; muchos trabajadores sin CV ni perfil digital. UX **extremadamente simple**, asumir baja alfabetización digital.
- **Idioma:** español peruano. Usar "DNI" (no "cédula"), "boleta de pago" (no "nómina"), "S/." para soles.

---

*Versión del documento: 2026-05-31 (reescrito contra el código real). El doc anterior contenía supuestos inexactos (marca SkillBridge, Next.js, HS256, puerto 3000, OCR, BD skillbridge_db) que han sido corregidos.*
