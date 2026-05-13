# CLAUDE.md — Sistema de Intermediación Laboral ML/NLP
# DRTPE-Junín | Huancayo, Perú | 2026
# Última actualización: Sprint 5 — Rojas Peña W. / Tovar Sanchez C.

---

## 🎯 VISIÓN DEL PRODUCTO

**Título:** IMPLEMENTACIÓN DE UN SISTEMA DE INTERMEDIACIÓN LABORAL MEDIANTE MACHINE LEARNING Y NLP PARA LA REDUCCIÓN DE BRECHAS DE ACCESO AL EMPLEO EN ARTICULACIÓN CON LA DIRECCIÓN REGIONAL DE TRABAJO Y PROMOCIÓN DEL EMPLEO JUNÍN

**Nombre comercial:** Linku
**Investigadores:** Rojas Peña, William Mikeiel | Tovar Sanchez, Carlos Alberto
**Stack:** FastAPI + PostgreSQL/pgvector + React 18 + Celery/Redis + Docker + GCP/AWS
**Metodología:** Scrum (sprints de 2 semanas) | Investigación aplicada cuantitativa explicativa
**Institución socia:** DRTPE-Junín — integración con la Bolsa de Trabajo oficial
**Estado actual:** Sprint 5 completado. Backend en producción. Frontend funcional.
**Documento normativo de RF/RNF:** Subcap. 4.3.2 (165 RF + 23 RNF) — toda implementación debe trazarse a un RF.

---

## 🗺️ ESTADO DEL PROYECTO POR SPRINT

| Sprint | Estado | Qué se entregó |
|--------|--------|----------------|
| Sprint 1 | ✅ Completo | Auth JWT, onboarding, modelos BD, migraciones, Docker |
| Sprint 2 | ✅ Completo | NLP real, empleadores, wizard PRIMER_EMPLEO, portfolio OFICIO, marketplace |
| Sprint 3 | ✅ Completo | Motor ML matching, embeddings reales, equity ranker, cold-start |
| Sprint 4 | ✅ Completo | Contratos, consentimiento Ley 29733, notificaciones WebSocket, admin DRTPE |
| Sprint 5 | ✅ Completo | KPIs, reportes, encuestas económicas, integración DRTPE, tests finales |
| Bugfix pendiente | ⚠️ En curso | 7 bugs de flujo público/marketplace frontend (ver sección BUGS CONOCIDOS) |

---

## 👤 TIPOS DE USUARIO Y FLUJOS

La plataforma atiende a **tres grupos poblacionales**. El onboarding clasifica al usuario y todo el producto se diferencia desde ese punto.

| Grupo | Problema | Solución |
|-------|----------|----------|
| **PRIMER_EMPLEO** | Sin historial laboral, no saben describir habilidades ni armar CV | Wizard guiado 6 pasos + generación asistida de CV con NLP |
| **EXPERIENCIA** | Perfil disperso o solo físico, difícil visibilidad digital | Bolsa formal tipo LinkedIn + matching ML |
| **OFICIO** | Competencias prácticas no certificadas, invisibles digitalmente | Portfolio visual + marketplace de servicios + CV automático |

### Reglas de flujo por tipo — CRÍTICAS

```
PRIMER_EMPLEO puede:
  ✅ Usar el wizard de 6 pasos
  ✅ Generar CV desde el wizard
  ✅ Ver ofertas de empleo (bolsa formal)
  ✅ Ver el marketplace público (/servicios y /marketplace) como visitante
  ✅ Postular a ofertas de trabajo
  ❌ No puede crear portfolio (usa el wizard)
  ❌ No puede publicar en el marketplace

EXPERIENCIA puede:
  ✅ Subir CV existente (PDF/DOCX) o crear perfil manual
  ✅ Ver y postular a la bolsa formal de empleo
  ✅ Ver el marketplace público (/servicios y /marketplace)
  ✅ Contactar trabajadores de oficio
  ❌ No puede crear portfolio (solo OFICIO)
  ❌ No puede publicar en el marketplace

OFICIO puede:
  ✅ Crear portfolio visual de trabajos
  ✅ Publicar en el marketplace de servicios
  ✅ Generar CV automático desde el portfolio
  ✅ Ver la bolsa formal de empleo
  ✅ Ver y administrar sus listings del marketplace

VISITANTE (sin cuenta) puede:
  ✅ Ver la landing page (/)
  ✅ Ver el marketplace público (/servicios)
  ✅ Ver perfiles públicos de portfolios (/p/{slug})
  ✅ Ver el feed de empleos (/jobs/feed)
  ⚠️ Al intentar contactar → modal de "Inicia sesión para contactar"
  ⚠️ El modal redirige a /login guardando la URL de retorno en sessionStorage
```

---

## 🏗️ ARQUITECTURA REAL DEL SISTEMA

### Backend — estructura actual de archivos

```
backend/app/
  api/v1/
    admin/dashboard.py       → Panel DRTPE-Junín (RF156–RF160)
    alerts.py                → Alertas de empleo configurables
    applications.py          → Postulaciones (RF051–RF055)
    auth.py                  → Autenticación JWT (RF001–RF015)
    contracts.py             → Contratos formales (RF161–RF165)
    cv.py                    → Generación de CVs PDF
    employers.py             → Empleadores y ofertas (RF036–RF050)
    jobs.py                  → Feed público de ofertas (RF055)
    marketplace.py           → Marketplace de servicios OFICIO (RF118–RF125)
    matching.py              → Motor de emparejamiento (RF076–RF095)
    nlp.py                   → Endpoints NLP (RF056–RF079)
    onboarding.py            → Detección de tipo (RF016–RF025)
    portfolio.py             → Portfolio OFICIO (RF056–RF065)
    router.py                → Router principal que agrupa todos
    surveys.py               → Encuestas económicas (KPIs)
    wizard.py                → Wizard PRIMER_EMPLEO (RF096–RF110)
    workers.py               → Perfil base trabajadores (RF026–RF035)
    ws_notifications.py      → WebSocket notificaciones en tiempo real

  core/
    config.py                → Settings Pydantic (lee .env)
    consent.py               → Consentimiento Ley N°29733
    database.py              → AsyncEngine SQLAlchemy + get_db()
    logging.py               → structlog JSON
    rate_limit.py            → Sliding window Redis, X-Forwarded-For en prod
    rate_limiter.py          → Decoradores de rate limit por endpoint
    redis_client.py          → Cliente Redis async singleton
    security.py              → JWT RS256, AES-256, bcrypt, RBAC
    security_headers.py      → Middleware headers de seguridad

  models/
    application.py           → Postulaciones
    audit_log.py             → Logs inmutables de auditoría
    base.py                  → Base declarativa SQLAlchemy
    consent_record.py        → Registros de consentimiento
    contract.py              → Contratos formalizados
    economic_survey.py       → Encuestas económicas KPI
    employer.py              → Empleadores
    equity_audit_log.py      → Log de auditoría de equidad ML
    generated_cv.py          → CVs generados
    job.py                   → Trabajos/empleos
    job_alert.py             → Alertas configuradas
    job_offer.py             → Ofertas de empleo
    match_event.py           → Eventos de matching (KPI)
    model_version.py         → Versiones del modelo ML
    notification.py          → Notificaciones persistentes
    portfolio.py             → Portfolio entries OFICIO
    search_log.py            → Logs de búsqueda (KPI IVP)
    service_listing.py       → Listings marketplace OFICIO
    tracking.py              → Tracking de acciones
    user.py                  → Usuarios del sistema
    wizard.py                → Progreso wizard PRIMER_EMPLEO
    worker.py                → Perfil trabajador (todos los tipos)

  nlp/
    cv_parser/parser.py      → PyPDF2 + python-docx + spaCy NER
    embeddings/generator.py  → sentence-transformers MiniLM-L12-v2 (384 dims)
    portfolio_nlp/trade_extractor.py → Extracción skills desde descripciones oficio
    skill_extractor/first_job_extractor.py → Extracción coloquial PRIMER_EMPLEO

  ml/
    cold_start/resolver.py   → Cold-start PRIMER_EMPLEO y OFICIO sin historial
    equity_ranker/ranker.py  → Re-ranking equitativo (disparate impact ≥ 0.80)
    explainer/explainer.py   → Explicaciones de recomendaciones
    matching_engine/
      dataset_builder.py     → Construcción dataset de entrenamiento
      drift_detector.py      → Detección de drift PSI
      features.py            → Feature engineering
      model_loader.py        → Carga de modelo entrenado
      scorer.py              → Scoring combinado por worker_type
      trainer.py             → Entrenamiento del modelo

  integrations/drtpe/connector.py → Conector Bolsa de Trabajo DRTPE-Junín

  services/
    cv_builder/
      pdf_generator.py       → WeasyPrint, plantillas por tipo
      wizard_service.py      → Lógica del wizard 6 pasos
    marketplace/marketplace_service.py → CRUD listings + búsqueda semántica
    matching/job_alerts.py   → Alertas de empleo
    onboarding/detector.py   → Detección de tipo + creación de perfil
    reports/kpi_calculator.py → Cálculo de los 8 KPIs de investigación

  tasks/
    celery_app.py            → Instancia Celery + broker Redis
    cv_generator.py          → Generación asíncrona de CVs PDF
    emails.py                → Envío de emails (stub en dev)
    embeddings.py            → generate_worker/job/portfolio/listing_embedding
    ml_tasks.py              → Reentrenamiento del modelo ML
    notifications.py         → Notificaciones push + WebSocket
    reports.py               → Reportes DRTPE asíncronos

  utils/
    file_validator.py        → Validación MIME + tamaño archivos
    local_dict/              → huancayo_trades.json
    seed_jobs.py             → Seed de datos de prueba

migrations/versions/
  0001_initial_schema.py
  0002_job_offers.py
  0003_worker_profile_fields.py
  0004_add_match_events.py
  0005_ml_matching_tables.py
  466614a36609_sprint4_consent_records.py
  7d5a80f3517d_add_job_requests_and_contracts.py
```

### Frontend — estructura actual de archivos

```
frontend/src/
  pages/
    LandingPage.tsx          → Landing pública (/) — DEBE ser la ruta raíz
    LoginPage.tsx            → Login con modal integrado
    RegisterPage.tsx         → Registro + onboarding
    PublicPortfolioPage.tsx  → /p/{slug} — perfil público OFICIO
    ServiceSearchPage.tsx    → /servicios — marketplace público sin auth
    ApplicationsPage.tsx     → Postulaciones del trabajador
    EconomicSurveyPage.tsx   → Encuesta económica KPI
    SettingsPage.tsx         → Configuración de cuenta
    employer/
      EmployerPublishPage.tsx
      EmployerCandidatesPage.tsx
      EmployerMessagesPage.tsx
    landing/
      LandingNav.tsx         → Nav de la landing (tiene link a /servicios)
      LoginModal.tsx         → Modal de login con return_url
      data.ts                → Datos estáticos de la landing

  modules/
    primer-empleo/
      PrimerEmpleoDashboard.tsx
      wizard/
        WizardLayout.tsx     → Contenedor del wizard 6 pasos
        WizardProgressBar.tsx
        WizardNavigation.tsx
        CVLivePreview.tsx    → Preview en tiempo real
        steps/
          Step1PersonalData.tsx
          Step2Education.tsx
          Step3Skills.tsx
          Step4Activities.tsx
          Step5Interests.tsx
          Step6Preview.tsx
    experiencia/
      ExperienciaDashboard.tsx
    oficio/
      OficioDashboard.tsx
      portfolio/
        PortfolioPage.tsx
        PortfolioCard.tsx
        AddEntryModal.tsx
      marketplace/
        MarketplacePage.tsx  → Vista autenticada del marketplace
                               Tab "mis-servicios" solo para OFICIO
                               Tab "buscar" para todos los autenticados
                               Botón "Publicar" solo visible para OFICIO

  shared/
    AppShell.tsx             → Shell con NavBar para rutas autenticadas
    NavBar.tsx               → Nav autenticado
                               "Buscar servicios" → /marketplace (TODOS los auth)
                               "Portfolio" → /oficio/portfolio (solo OFICIO)
    ContactModal.tsx         → Modal de contacto
                               Verifica auth antes de mostrar formulario
                               Sin auth → panel "Inicia sesión para contactar"
    WorkerDashboard.tsx      → Enrutador por worker_type
    LoadingSpinner.tsx
    LinkuLogo.tsx
    NotificationBell.tsx

  context/
    AuthContext.tsx          → Estado de autenticación global
    WorkerContext.tsx        → Estado del perfil del trabajador

  guards/
    AuthGuard.tsx            → Redirige a /login si no autenticado
    WorkerTypeGuard.tsx      → Redirige a /dashboard si tipo incorrecto
    AdminGuard.tsx           → Redirige a /dashboard si no es admin

  hooks/
    useMarketplace.ts        → useMarketplaceSearch + useMyListings
    useMatches.ts            → Motor de matching
    usePortfolio.ts          → Portfolio OFICIO
    useApplications.ts       → Postulaciones
    useEmployer.ts           → Dashboard empleador
    useNotifications.ts      → WebSocket notificaciones
    useAdminKPIs.ts          → KPIs panel admin

  api/client.ts              → Axios con interceptores JWT

  App.tsx                    → Rutas principales (ver sección RUTAS)
```

---

## 🗺️ RUTAS DEL FRONTEND — DISEÑO CORRECTO

```tsx
// Rutas PÚBLICAS (sin AuthGuard, sin WorkerTypeGuard)
/ → LandingPage                    // primera página para cualquier visitante
/servicios → ServiceSearchPage     // marketplace público, sin auth
/p/:slug → PublicPortfolioPage     // portfolio público de trabajador OFICIO
/login → LoginPage
/register → RegisterPage

// Rutas con AuthGuard pero sin WorkerTypeGuard (cualquier usuario autenticado)
/dashboard → WorkerDashboard       // enruta según worker_type
/marketplace → MarketplacePage     // marketplace para todos los autenticados
                                   // internamente: tab mis-servicios solo si OFICIO
                                   // internamente: botón publicar solo si OFICIO
/applications → ApplicationsPage
/matches → MatchesPage             // no aplica a PRIMER_EMPLEO
/settings → SettingsPage
/survey/economic → EconomicSurveyPage

// Rutas con WorkerTypeGuard específico
/wizard/* → WizardLayout           // solo PRIMER_EMPLEO
/oficio/portfolio → PortfolioPage  // solo OFICIO

// Rutas de empleador
/employer/dashboard → EmployerDashboard
/employer/publish → EmployerPublishPage
/employer/candidates → EmployerCandidatesPage
/employer/messages → EmployerMessagesPage

// Admin
/admin/* → AdminLayout             // solo role=admin
```

---

## 🐛 BUGS CONOCIDOS — PENDIENTES DE CORRECCIÓN

Estos bugs fueron identificados revisando el código del repo. Están documentados en `docs/sprints/bugfix_frontend_completo.md`.

| # | Archivo | Bug | Estado |
|---|---------|-----|--------|
| 1 | App.tsx | Ruta `/` redirige a dashboard en lugar de mostrar LandingPage | ⚠️ Pendiente |
| 2 | App.tsx | `/marketplace` bloqueado con WorkerTypeGuard solo para OFICIO | ⚠️ Pendiente |
| 3 | MarketplacePage.tsx | Botón "Publicar servicio" visible para todos los tipos | ⚠️ Pendiente |
| 4 | ContactModal.tsx | Abre sin verificar auth, devuelve error 401 crudo | ⚠️ Pendiente |
| 5 | PublicPortfolioPage + ServiceSearchPage | CTA sin auth manda a /register en vez de /login con return_url | ⚠️ Pendiente |
| 6 | LoginModal.tsx | Después del login siempre redirige a /dashboard, ignora return_url | ⚠️ Pendiente |
| 7 | NavBar.tsx | Link a marketplace solo visible para OFICIO | ⚠️ Pendiente |

---

## ⚙️ STACK TECNOLÓGICO

### Backend
- **Python 3.11** — sin excepciones, no usar 3.10 ni 3.12
- **FastAPI** — routers por módulo, prefijo `/api/v1/`
- **Pydantic v2** — validación de todos los schemas
- **SQLAlchemy 2.x** — ORM async, sin SQL crudo nunca
- **Alembic** — todas las migraciones, nunca modificar tablas manualmente
- **PostgreSQL 15+** con **pgvector** — columnas `vector(384)`
- **Redis** — caché, blacklist de tokens y broker Celery
- **Celery** — tareas pesadas asíncronas (embeddings, CVs, reportes, emails)
- **sentence-transformers** — `paraphrase-multilingual-MiniLM-L12-v2` (384 dims)
- **spaCy** — `es_core_news_md` + pipeline custom para oficios
- **NLTK** — stopwords español
- **scikit-learn** — modelos supervisados, métricas, re-ranking equitativo
- **WeasyPrint** — generación de CVs en PDF
- **PyPDF2 + python-docx** — parsing de CVs subidos
- **structlog** — logging JSON, nunca usar print()
- **bcrypt** — cost factor mínimo 12
- **JWT RS256** — access token 24h, refresh token 7d, blacklist en Redis
- **AES-256-GCM** — cifrado de campos sensibles (DNI, teléfono, nombre). La clave se almacena en base64 en .env y decodifica a 32 bytes exactos.

### Frontend
- **React 18** + **Vite**
- **Tailwind CSS** — sin CSS personalizado salvo variables CSS
- **react-hook-form** + **zod** — validación de formularios
- **react-intl** — i18n español peruano (es-PE)
- **Axios** — cliente HTTP con interceptores JWT
- **Recharts** — gráficos del dashboard
- **react-dropzone** — upload de fotos para portfolio y CVs
- **WebSocket** — notificaciones en tiempo real
- **lucide-react** — iconografía

### Infraestructura
- **Docker** + **docker-compose** — imagen base `pgvector/pgvector:pg15` (no postgres:15-alpine)
- **GitHub Actions** — CI/CD: lint → tests → build → staging → prod
- **GCP Cloud Run / AWS ECS** — despliegue en producción
- **GCS / S3** — fotos de portfolio y CVs
- **Prometheus + Grafana** — monitoreo (infra/ y monitoring/)
- **OWASP ZAP** — DAST en pipeline CI/CD
- **Nginx** — reverse proxy (nginx/nginx.conf)

---

## 🗄️ BASE DE DATOS

### Convenciones
- **UUID** para todas las PKs, nunca integer autoincrement
- **TIMESTAMPTZ** para todas las fechas (UTC siempre)
- Datos sensibles en columnas `BYTEA` con AES-256-GCM a nivel aplicación
- Toda migración debe tener `downgrade()` completo
- Nombres de tablas: snake_case, plural
- Nunca modificar migraciones ya aplicadas — crear una nueva

### Índices HNSW (críticos para performance)
```sql
-- Deben existir en producción:
CREATE INDEX ON workers           USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
CREATE INDEX ON portfolio_entries USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
CREATE INDEX ON service_listings  USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
CREATE INDEX ON job_offers        USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
```

### Cifrado de campos sensibles
```python
# ✅ SIEMPRE cifrar antes de persistir
worker.full_name = encrypt_field(full_name_plain)
worker.dni       = encrypt_field(dni_plain)
worker.phone     = encrypt_field(phone_plain)

# ✅ SIEMPRE descifrar antes de devolver al cliente
full_name_plain = decrypt_field(worker.full_name)

# ❌ NUNCA devolver el campo DNI al cliente en ninguna respuesta
# ❌ NUNCA loguear valores descifrados
```

---

## 🤖 MOTOR ML/NLP

### Pipelines NLP por tipo

```python
# PRIMER_EMPLEO — lenguaje coloquial → habilidades estandarizadas
# Archivo: app/nlp/skill_extractor/first_job_extractor.py
# 40 términos coloquiales peruanos en soft_skills_map
# suggest_job_sectors() → top-5 sectores compatibles

# EXPERIENCIA — CV estructurado → campos con umbral de confianza 0.75
# Archivo: app/nlp/cv_parser/parser.py
# parse_pdf() + parse_docx() + extract_cv_fields()
# Si confianza < 0.75 → campo None + warning al usuario

# OFICIO — descripción de trabajo → habilidades técnicas
# Archivo: app/nlp/portfolio_nlp/trade_extractor.py
# TRADE_SKILLS_MAP con 15+ skills por categoría
# Nivel: básico / intermedio / avanzado
```

### Pipeline de normalización (todos los tipos, en orden)
```
1. text.lower()
2. ftfy.fix_text()              → corregir encoding/acentos
3. re.sub caracteres especiales → conservar letras, números, acentos españoles
4. apply_local_dictionary()     → ANTES del embedding, siempre
5. eliminar stopwords ES (NLTK)
6. generar embedding con MiniLM-L12-v2 (384 dims, normalize_embeddings=True)
7. almacenar en pgvector via Celery (asíncrono)
```

### Score combinado — fórmula fija, no modificar sin validar F1
```python
weights = {
    WorkerType.PRIMER_EMPLEO: (0.65, 0.35, 0.00),  # cosine, ml, reputation
    WorkerType.EXPERIENCIA:   (0.50, 0.30, 0.20),
    WorkerType.OFICIO:        (0.45, 0.25, 0.30),
}
score = alpha * cosine_sim + beta * ml_score + gamma * (reputation / 5.0)
```

### Métricas mínimas aceptables
- F1-score en producción: **≥ 0.75** (si < 0.70 → alerta automática)
- Disparate impact ratio: **≥ 0.80** por género y zona (si < 0.80 → re-ranking automático)
- NER F1 extracción de habilidades: **≥ 0.80** por pipeline
- CV parser accuracy: **≥ 0.75**

---

## 🔒 SEGURIDAD

```python
# ❌ NUNCA hacer esto:
print(f"DNI del usuario: {worker.dni}")          # exponer en logs
db.execute(f"SELECT * FROM workers WHERE id={id}") # SQL con f-string
return JSONResponse({"detail": str(exc)})          # stack trace en producción

# ✅ SIEMPRE hacer esto:
logger.info("worker_loaded", worker_id=str(worker.id))  # structlog, sin PII
result = await db.execute(select(Worker).where(Worker.id == worker_id))  # ORM
raise HTTPException(status_code=500, detail="Error interno del servidor")  # genérico

# Validación de roles en cada endpoint protegido:
@router.post("/portfolio/entries")
async def create_entry(payload: dict = Depends(require_role(UserRole.WORKER))):
    # Verificar además que worker.worker_type == 'oficio'
    ...
```

### Rate limiting (app/core/rate_limit.py)
- Lee `X-Forwarded-For` en `ENVIRONMENT=production` (IP real en Cloud Run/ECS)
- Sliding window con Redis: `INCR` + `EXPIRE`
- Lanza `HTTPException 429` con header `Retry-After`
- Límites: auth/register 10/hora, login 20/hora, forgot-password 5/hora

### Ley N° 29733 (Datos personales Perú)
- Consentimiento registrado en `consent_records` antes de recolectar datos
- `app/core/consent.py` gestiona el flujo de consentimiento
- DNI, teléfono y nombre siempre cifrados con AES-256-GCM

---

## 📊 KPIs DE INVESTIGACIÓN — NO MODIFICAR SIN CONSULTAR

| KPI | Fórmula | Tabla BD | Aplica a |
|-----|---------|----------|----------|
| Velocidad Inserción Laboral (VIL) | `días(registro → primer contrato)` | `contracts` | Los 3 tipos |
| Índice Visibilidad Perfil (IVP) | `(apariciones en búsquedas / total consultas) × 100` | `search_logs` | Los 3 tipos |
| Tasa Formalización | `(trabajadores con ≥1 contrato / total) × 100` | `workers`, `contracts` | Los 3 tipos |
| Reputation Score | `promedio_ponderado(ratings, peso×2 últimas 5)` | `ratings` | EXPERIENCIA, OFICIO |
| Reducción Brecha Salarial | `((ingreso_post - ingreso_pre) / ingreso_pre) × 100` | `economic_surveys` | Los 3 tipos |
| Tasa Completitud CV (TCC) | `(perfiles con CV generado / total) × 100` | `generated_cvs`, `workers` | PRIMER_EMPLEO, OFICIO |
| Índice Visibilidad Marketplace (IVM) | `(listados activos / total OFICIO) × 100` | `service_listings`, `workers` | OFICIO |
| Tasa Cold-Start Superado | `(con ≥1 match / total primer_empleo+oficio) × 100` | `match_events` | PRIMER_EMPLEO, OFICIO |

Calculados en: `app/services/reports/kpi_calculator.py`

---

## 📐 CONVENCIONES DE CÓDIGO

### Python — reglas absolutas
```python
# ✅ async en todos los endpoints y servicios
async def get_worker(worker_id: UUID, db: AsyncSession) -> Worker: ...

# ✅ Pydantic v2 siempre
class WorkerCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    worker_type: WorkerType  # obligatorio en todo schema de worker

# ✅ SQLAlchemy 2.x async
result = await db.execute(select(Worker).where(Worker.id == worker_id))
worker = result.scalar_one_or_none()

# ✅ structlog siempre, nunca print()
logger = structlog.get_logger()
logger.info("evento", campo=valor, otro_campo=otro_valor)

# ✅ random_state=42 en todos los modelos ML para reproducibilidad
```

### Frontend — reglas absolutas
```tsx
// ✅ Verificar auth antes de cualquier acción de contacto
const isAuthenticated = !!localStorage.getItem('access_token')

// ✅ Guardar return_url antes de redirigir a login
sessionStorage.setItem('login_return_url', window.location.pathname + window.location.search)

// ✅ Leer return_url después del login
const returnUrl = sessionStorage.getItem('login_return_url') || '/dashboard'
sessionStorage.removeItem('login_return_url')
navigate(returnUrl)

// ✅ Condicionar publicación solo a OFICIO
{worker?.worker_type === 'oficio' && <BotonPublicar />}

// ✅ Marketplace visible para todos los autenticados
// ❌ NO envolver /marketplace en WorkerTypeGuard
```

---

## 🧪 TESTING

```bash
# Antes de cualquier commit
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
ruff check . && ruff format --check .

# Tests organizados por área
tests/unit/
  test_auth_jwt.py               test_security.py
  test_cold_start.py             test_cors_config.py
  test_cv_generator.py           test_dataset_builder.py
  test_drtpe_connector.py        test_embedding_no_pii.py
  test_embeddings.py             test_kpi_calculator.py
  test_local_dictionary.py       test_marketplace_search.py
  test_matching_engine.py        test_ml_pipeline.py
  test_nlp_cv_parser.py          test_nlp_first_job.py
  test_nlp_trade_portfolio.py    test_onboarding_detector.py
  test_psi_drift_detector.py     test_reputation_score.py
  test_sprint5_contracts_applications.py
  test_sprint5_drtpe_real.py
  test_sprint5_marketplace_service.py
  test_storage_and_tasks.py      test_ws_connection_limit.py

tests/integration/
  test_api_admin_dashboard.py    test_api_auth.py
  test_api_auth_email.py         test_api_employers.py
  test_api_health.py             test_api_jobs.py
  test_api_marketplace.py        test_api_matching.py
  test_api_nlp.py                test_api_onboarding.py
  test_api_portfolio.py          test_api_wizard.py
  test_api_workers.py            test_job_alerts.py
  test_portfolio_public_no_uuid.py
  test_websocket_notifications.py
```

- Cobertura mínima: **80%** — CI bloquea merge si baja
- `random_state=42` en todos los modelos ML
- Tests NLP deben incluir textos en español coloquial de Huancayo
- Tests de marketplace deben incluir búsquedas con términos locales

---

## 🚀 COMANDOS FRECUENTES

```bash
# Levantar entorno completo
docker-compose up -d

# Ver logs
docker-compose logs api --tail=50
docker-compose logs celery_worker --tail=30

# Migraciones
alembic upgrade head
alembic revision --autogenerate -m "descripcion"
alembic history --verbose

# Tests
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80 -v
pytest tests/unit/test_auth_jwt.py -v  # test específico

# Linting
ruff check . && ruff format .

# Celery worker
celery -A app.tasks worker --loglevel=info

# Embeddings
python -m app.tasks.embeddings regenerate_all --type all
python -m app.tasks.embeddings regenerate_all --type primer_empleo

# Seed de datos
python backend/scripts/seed_data.py

# Reentrenar modelo ML
python -m app.ml.train --validate --deploy-if-better --worker-type all

# Frontend
cd frontend && npm run dev
npx tsc --noEmit  # verificar tipos sin compilar
```

---

## 🌍 CONTEXTO LOCAL — HUANCAYO

### Diccionario de equivalencias NLP
Archivo: `backend/app/utils/local_dict/huancayo_trades.json`
Aplicar SIEMPRE con `apply_local_dictionary()` ANTES de generar embeddings.

```json
{
  "gasfitero":     ["plomero", "fontanero", "instalador sanitario"],
  "techero":       ["techadista", "instalador de techos", "techador"],
  "fierrero":      ["soldador", "herrero", "metalurgista"],
  "albañil":       ["constructor", "obrero de construcción", "operario civil"],
  "electricista":  ["instalador eléctrico", "técnico eléctrico"],
  "pintor":        ["aplicador de pintura", "pintor de obras"],
  "carpintero":    ["ebanista", "trabajador de madera"],
  "mecánico":      ["técnico automotriz", "mecánico automotriz"],
  "plomero":       ["gasfitero"],
  "instalador":    ["técnico de instalaciones"]
}
```

### Categorías de oficio
```python
class TradeCategory(str, Enum):
    ELECTRICIDAD = "Electricidad"
    GASFITERIA   = "Gasfitería"
    CARPINTERIA  = "Carpintería"
    ALBANILERIA  = "Albañilería"
    PINTURA      = "Pintura"
    MECANICA     = "Mecánica automotriz"
    TECHADO      = "Techado"
    SOLDADURA    = "Soldadura y metalurgia"
    JARDINERIA   = "Jardinería"
    LIMPIEZA     = "Limpieza y mantenimiento"
    COCINA       = "Cocina y pastelería"
    COSTURA      = "Costura y confección"
    OTROS        = "Otros oficios"
```

### Datos locales
- **Distritos:** `Huancayo`, `El Tambo`, `Chilca`
- **Moneda:** `S/.` (Sol peruano, PEN) — formato `S/. 1,000.00`
- **Teléfonos:** `+51 9XXXXXXXX` (9 dígitos tras +51)
- **DNI:** 8 dígitos numéricos exactos
- **RUC:** 11 dígitos numéricos exactos

---

## ⛔ PROHIBICIONES ABSOLUTAS

### Backend
- No usar **Django** ni **Flask** — solo FastAPI
- No usar **MongoDB** — solo PostgreSQL + pgvector
- No usar **NumPy < 1.24** ni **pandas < 2.0**
- No instalar librerías sin actualizar `requirements.txt`
- No commits directos a `main` — siempre vía PR
- No exponer `/api/v1/model/metrics` sin autenticación ADMIN
- No eliminar logs de auditoría — son inmutables
- No modificar `combined_score` sin validar impacto en F1
- No mezclar lógica de tipos en un mismo servicio
- No omitir `worker_type` en operaciones de matching o recomendación
- No almacenar fotos en base64 en BD — siempre GCS/S3 con URL firmada
- No modificar migraciones ya aplicadas — crear una nueva
- No implementar funcionalidad sin trazarla a un RF del subcap. 4.3.2
- No usar `print()` — solo `structlog`
- No retornar stack traces en producción

### Frontend
- No bloquear el acceso al marketplace (`/marketplace`, `/servicios`) por tipo de usuario — es visible para todos
- Solo OFICIO puede **publicar** en el marketplace — condicionar solo el botón/tab internamente
- No abrir ContactModal sin verificar autenticación primero
- No redirigir a /register cuando el usuario intenta contactar — redirigir a /login
- No navegar a /dashboard hardcodeado después del login — usar sessionStorage return_url
- No usar WorkerTypeGuard en la ruta /marketplace — solo en /oficio/portfolio y /wizard
- La ruta `/` SIEMPRE debe mostrar LandingPage, no redirigir al dashboard

### Ambos
- No exponer DNI en ninguna respuesta del API ni en logs
- No almacenar contraseñas en texto plano

---

## 📁 ARCHIVOS QUE NUNCA SE MODIFICAN SIN REVISIÓN DEL EQUIPO

```
backend/app/ml/train.py                          → entrenamiento del modelo
backend/app/nlp/embeddings/generator.py          → generación de vectores
backend/app/utils/local_dict/huancayo_trades.json → diccionario Huancayo
backend/migrations/versions/*.py                 → migraciones aplicadas
backend/app/core/config.py                       → configuración producción
backend/app/services/reports/kpi_calculator.py   → cálculo KPIs de investigación
CLAUDE.md                                        → este archivo
```

---

## 🔗 TRAZABILIDAD RF → CARPETA

| Módulo | RF | Carpeta |
|--------|----|---------|
| M01 Identidad y Autenticación | RF001–RF015 | `app/api/v1/auth.py`, `app/core/security.py` |
| M02 Perfil del Trabajador | RF016–RF035 | `app/api/v1/workers.py`, `app/services/onboarding/` |
| M03 Empleadores y Ofertas | RF036–RF055 | `app/api/v1/employers.py`, `app/api/v1/jobs.py` |
| M04 NLP de Competencias | RF056–RF075 | `app/nlp/`, `app/api/v1/nlp.py` |
| M05 Motor ML Emparejamiento | RF076–RF095 | `app/ml/`, `app/api/v1/matching.py` |
| M06 Asistente Identidad Laboral | RF096–RF110 | `app/api/v1/wizard.py`, `app/services/cv_builder/` |
| M07 Búsqueda y Recomendación | RF111–RF125 | `app/api/v1/marketplace.py`, `app/services/marketplace/` |
| M08 Notificaciones | RF126–RF135 | `app/api/v1/ws_notifications.py`, `app/tasks/notifications.py` |
| M09 Reportes DRTPE | RF136–RF145 | `app/api/v1/admin/`, `app/tasks/reports.py` |
| M10 Equidad y Explicabilidad | RF146–RF155 | `app/ml/equity_ranker/`, `app/ml/explainer/` |
| M11 Administración | RF156–RF160 | `app/api/v1/admin/dashboard.py` |
| M12 Integración Institucional | RF161–RF165 | `app/integrations/drtpe/`, `app/api/v1/contracts.py` |

---

*Última actualización: Sprint 5 + Bugfix frontend — Rojas Peña W. / Tovar Sanchez C.*
