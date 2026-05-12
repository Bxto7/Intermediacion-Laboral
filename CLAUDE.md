# CLAUDE.md — Sistema de Intermediación Laboral ML/NLP
# DRTPE-Junín | Huancayo, Perú | 2026
# Última actualización: Sprint 1 — Rojas Peña W. / Tovar Sanchez C.

---

## 🎯 VISIÓN DEL PRODUCTO

**Título:** IMPLEMENTACIÓN DE UN SISTEMA DE INTERMEDIACIÓN LABORAL MEDIANTE MACHINE LEARNING Y NLP PARA LA REDUCCIÓN DE BRECHAS DE ACCESO AL EMPLEO EN ARTICULACIÓN CON LA DIRECCIÓN REGIONAL DE TRABAJO Y PROMOCIÓN DEL EMPLEO JUNÍN

**Investigadores:** Rojas Peña, William Mikeiel | Tovar Sanchez, Carlos Alberto
**Stack:** FastAPI + PostgreSQL/pgvector + React + Celery/Redis + Docker + GCP/AWS
**Metodología:** Scrum (sprints de 2 semanas) | Investigación aplicada cuantitativa explicativa
**Institución socia:** DRTPE-Junín — integración con la Bolsa de Trabajo oficial
**Documento normativo de RF/RNF:** Subcap. 4.3.2 (165 RF + 23 RNF) — toda implementación debe trazarse a un RF.

### Problema central que resuelve

La plataforma atiende a **tres grupos poblacionales** con brechas distintas de acceso al empleo formal en la región Junín (informalidad superior al 75% de la PEA). El onboarding clasifica al usuario en uno de estos tipos y todo el resto del producto se diferencia a partir de allí.

| Grupo | Problema específico | Solución en la plataforma |
|-------|---------------------|--------------------------|
| **PRIMER_EMPLEO** | Sin historial laboral; no saben describir habilidades ni armar CV | Onboarding guiado paso a paso + generación asistida de CV con NLP |
| **EXPERIENCIA** | Perfil disperso o solo físico; difícil visibilidad digital | Creación/importación rápida de perfil + bolsa de empleo formal |
| **OFICIO** | Competencias prácticas no certificadas, invisibles digitalmente | Portfolio visual de trabajos + CV automático + marketplace de servicios |

### Trazabilidad RF → módulo del código

Cada módulo del backend implementa un rango concreto de RF del subcapítulo 4.3.2. Al abrir un PR siempre debe declararse qué RF cubre.

| Módulo del subcap. 4.3.2 | Rango RF | Carpeta backend principal |
|---|---|---|
| M01 Identidad y Autenticación | RF001–RF015 | `app/api/auth`, `app/core/security` |
| M02 Perfil del Trabajador | RF016–RF035 | `app/services/onboarding`, `app/services/cv_builder` |
| M03 Empleadores y Ofertas | RF036–RF055 | `app/services/job_board` |
| M04 NLP de Competencias | RF056–RF075 | `app/nlp/` |
| M05 Motor ML de Emparejamiento | RF076–RF095 | `app/ml/matching_engine` |
| M06 Asistente de Identidad Laboral | RF096–RF110 | `app/services/cv_builder` (wizard) |
| M07 Búsqueda y Recomendación | RF111–RF125 | `app/services/matching`, `app/services/marketplace` |
| M08 Notificaciones | RF126–RF135 | `app/tasks/notifications` |
| M09 Reportes DRTPE | RF136–RF145 | `app/api/admin`, `app/tasks/reports` |
| M10 Equidad y Explicabilidad | RF146–RF155 | `app/ml/equity_ranker`, `app/ml/explainer` |
| M11 Administración | RF156–RF160 | `app/api/admin` |
| M12 Integración Institucional | RF161–RF165 | `app/integrations/drtpe` |

---

## 🏗️ ARQUITECTURA DEL SISTEMA

```
frontend/
  src/
    onboarding/        → Detección de tipo de usuario (3 rutas)
    modules/
      primer-empleo/   → Wizard guiado CV + orientación laboral
      experiencia/     → Dashboard tipo bolsa profesional
      oficio/          → Portfolio visual + marketplace de servicios
    shared/            → Componentes comunes, i18n, hooks
    matching/          → Vista de recomendaciones explicables
    employer/          → Dashboard de empleadores (publicar, buscar)
    admin/             → Panel DRTPE-Junín

backend/
  app/
    api/               → Routers FastAPI por módulo (v1)
    core/              → Config, seguridad JWT, DB, Redis
    models/            → SQLAlchemy ORM models
    schemas/           → Pydantic v2 schemas
    services/
      onboarding/      → Lógica de detección y enrutamiento por tipo
      cv_builder/      → Wizard + generación asistida de CV
      portfolio/       → Gestión del portfolio visual (oficio)
      job_board/       → Bolsa formal + integración DRTPE
      marketplace/     → Publicación y búsqueda de servicios de oficio
      matching/        → Motor de emparejamiento diferenciado
    nlp/
      skill_extractor/ → NER de habilidades (spaCy)
      embeddings/      → Vectorización de perfiles y ofertas
      cv_parser/       → Parser de CVs subidos (PDF/DOCX)
      skill_suggester/ → Sugerencia de habilidades (primer empleo)
      portfolio_nlp/   → Extracción semántica desde descripciones de trabajos
    ml/
      matching_engine/ → Emparejamiento supervisado
      equity_ranker/   → Re-ranking equitativo por género/zona
      cold_start/      → Resolución de arranque en frío
      explainer/       → Razones de recomendación (RF146–RF150)
    integrations/
      drtpe/           → Conector con la Bolsa de Trabajo DRTPE-Junín
    tasks/             → Celery: embeddings, reportes, notificaciones, emails
    utils/
      local_dict/      → Diccionario de equivalencias Huancayo
      cv_templates/    → Plantillas de CV por tipo de usuario
  migrations/          → Alembic
  tests/               → pytest (cobertura ≥ 80%)

docker-compose.yml
CLAUDE.md              → Este archivo
```

---

## 👤 FLUJOS DE USUARIO — NÚCLEO DEL SISTEMA

### Flujo 0 — Onboarding de detección de tipo (obligatorio)

Antes de cualquier funcionalidad, el sistema clasifica al usuario en uno de los tres tipos. La detección se hace con dos preguntas conversacionales y el resultado se persiste en `workers.worker_type`. Cambiar el tipo después solo es posible con solicitud explícita del usuario y confirmación.

```
Registro → Pantalla de detección →
  Pregunta 1: "¿Estás buscando tu primer empleo?"
    SI → tipo = PRIMER_EMPLEO
    NO → Pregunta 2: "¿Trabajas en un oficio? (electricista, gasfitero, carpintero, etc.)"
      SI → tipo = OFICIO
      NO → tipo = EXPERIENCIA
```

```python
# ✅ Schema de onboarding — punto de entrada (M02 / RF016–RF020)
class OnboardingAnswers(BaseModel):
    is_first_job: bool
    is_trade_worker: bool                # solo relevante si is_first_job = False
    trade_category: TradeCategory | None = None  # solo si is_trade_worker = True

class WorkerType(str, Enum):
    PRIMER_EMPLEO = "primer_empleo"
    EXPERIENCIA   = "experiencia"
    OFICIO        = "oficio"

# ✅ Reglas:
#   - El tipo NO cambia sin solicitud explícita del usuario + confirmación
#   - Siempre pasar WorkerType en queries de matching, recomendación y reportes
#   - Mezclar lógica de tipos en un mismo servicio está prohibido
```

---

### Flujo A — PRIMER_EMPLEO

**Objetivo:** Reducir la barrera de entrada al mercado laboral para personas sin CV ni experiencia documentada. Cubre M06 (RF096–RF110) y parte de M02.

#### Wizard de construcción de CV guiado (6 pasos)

```
Paso 1 — Datos personales (DNI, nombre, zona, foto)
Paso 2 — Educación (colegio, instituto, universidad — cualquiera sirve)
Paso 3 — Habilidades blandas: pregunta conversacional NLP-asistida
          "¿Eres puntual? ¿Trabajas bien en equipo? ¿Qué haces bien?"
          → NLP extrae skills y los mapea a taxonomía estándar
Paso 4 — Actividades previas (voluntariado, proyectos escolares, ayuda familiar)
          → NLP convierte experiencias informales en competencias transferibles
Paso 5 — Intereses laborales: el sistema sugiere sectores compatibles
Paso 6 — Vista previa del CV generado + edición + descarga PDF
```

```python
# ✅ NLP para primer empleo — extracción de habilidades desde texto libre
async def extract_skills_from_conversation(
    user_text: str,
    context: FirstJobContext,
    db: AsyncSession,
) -> SkillExtractionResult:
    """
    Usa spaCy NER + diccionario de habilidades blandas/duras para
    mapear lenguaje coloquial a competencias estandarizadas.
    Ej: "ayudo a mi papá en su carpintería" →
        skills: ["trabajo manual", "trabajo en madera", "colaboración familiar"]
        suggested_trades: ["Carpintería", "Ebanistería"]
    """
    ...

# ✅ Cold-start: generar embedding inicial desde respuestas del wizard
async def generate_cold_start_profile(
    answers: WizardAnswers,
    db: AsyncSession,
) -> WorkerEmbedding:
    """
    Sin historial: construir texto de perfil sintético desde el wizard
    y generar embedding inicial. Cubre RF096–RF105.
    """
    profile_text = build_first_job_profile_text(answers)
    return await generate_embedding_async(profile_text)
```

```tsx
// ✅ Frontend Wizard — Ruta: /onboarding/primer-empleo
// - Lenguaje simple y motivador (evitar términos técnicos de RRHH)
// - Tooltips en cada campo
// - Barra de progreso (paso X de 6)
// - Autoguardado por paso (no perder progreso)
// - Preview de CV en tiempo real en panel derecho
```

#### Dashboard PRIMER_EMPLEO

```
Panel principal:
  ├── Mi CV (editable, descargable en PDF)
  ├── Recomendaciones de empleo (entrada, prácticas, part-time)
  ├── Orientación laboral:
  │     ├── "¿Cómo ir a una entrevista?"
  │     ├── "¿Qué ropa usar?" (contextual por sector)
  │     ├── "¿Cómo negociar mi primer sueldo?"
  │     └── Tips semanales personalizados por NLP
  ├── Empleos del DRTPE-Junín compatibles (entrada)
  └── Progreso del perfil (% completado + sugerencias)
```

---

### Flujo B — EXPERIENCIA

**Objetivo:** Visibilidad digital rápida y conexión con empleo formal. Cubre M02, M03 y M07.

#### Creación de perfil — dos rutas

```
Ruta B1 — Subir CV existente (PDF/DOCX):
  → NLP parser extrae nombre, educación, experiencias y skills
  → El usuario revisa y edita lo extraído
  → Se genera embedding semántico del perfil
  → Tiempo estimado: 3 minutos

Ruta B2 — Crear perfil manual (formulario estructurado):
  → Formulario simplificado tipo bolsa profesional
  → NLP sugiere habilidades adicionales mientras escribe
  → Validación en tiempo real de completitud
  → Tiempo estimado: 8 minutos
```

```python
# ✅ Parser de CV — solo para EXPERIENCIA (RF066–RF070)
async def parse_uploaded_cv(
    file_content: bytes,
    file_type: Literal["pdf", "docx"],
    db: AsyncSession,
) -> ParsedCVResult:
    """
    Extrae entidades del CV subido:
    - Nombre completo, contacto
    - Educación (institución, carrera, año)
    - Experiencias laborales (empresa, cargo, fechas, tareas)
    - Habilidades explícitas
    - Certificaciones

    Confianza mínima para prellenar: 0.75.
    Si confianza < 0.75 → campo vacío con sugerencia al usuario.
    """
    ...
```

#### Dashboard EXPERIENCIA

```
Panel principal:
  ├── Perfil profesional (foto, titular, resumen, experiencias)
  ├── Bolsa formal (DRTPE-Junín + empleadores registrados):
  │     ├── Feed de ofertas ordenado por score de compatibilidad
  │     ├── Filtros: sector, distrito, modalidad, rango salarial
  │     ├── Cada oferta muestra el % de compatibilidad y el porqué
  │     └── Botón "Postular" → envía perfil al empleador
  ├── Conexiones: otros trabajadores del sector (red profesional básica)
  ├── Alertas configurables (keyword, sector, salario)
  └── Estado de postulaciones (en revisión / entrevista / descartado)
```

```python
# ✅ Matching para EXPERIENCIA (M05 / RF076–RF090)
async def match_experienced_worker(
    worker_id: UUID,
    db: AsyncSession,
    top_k: int = 20,
) -> list[JobMatchResult]:
    """
    1. Recuperar embedding del perfil del trabajador
    2. Buscar top-K vacantes por cosine similarity (pgvector)
    3. Re-ranking con modelo supervisado (historial de postulaciones)
    4. Aplicar filtro equitativo (disparate impact ≥ 0.80)
    5. Retornar con explicación: skills que coinciden y skills faltantes
    """
    ...
```

---

### Flujo C — OFICIO

**Objetivo:** Convertir la experiencia práctica no documentada en visibilidad digital real. Cubre M02, M04, M07 y partes específicas de M06 (CV automático desde portfolio).

OFICIO tiene **dos superficies diferenciadas** que conviven:

```
Superficie C1 — PORTFOLIO VISUAL (identidad laboral digital):
  Propósito: mostrar "qué sé hacer y qué he hecho"

Superficie C2 — MARKETPLACE DE SERVICIOS (conseguir trabajo ahora):
  Propósito: publicitar disponibilidad y ser encontrado por clientes/empleadores
```

#### C1 — Portfolio Visual

```
Estructura:
  ├── Header: foto, nombre, oficio principal, zona, disponibilidad (on/off)
  ├── Tarjetas de trabajos realizados:
  │     ├── Foto(s) del trabajo (antes/después si aplica)
  │     ├── Descripción breve en lenguaje propio del trabajador
  │     ├── NLP convierte la descripción en etiquetas técnicas
  │     ├── Año/período, cliente (opcional, anónimo)
  │     └── Calificación del cliente si la hay
  ├── Habilidades extraídas automáticamente desde los trabajos
  ├── "CV Automático": botón que genera PDF a partir del portfolio
  └── Enlace público compartible (URL: /p/{slug})
```

```python
# ✅ NLP para portfolio de oficio (RF071–RF075)
async def extract_skills_from_job_entry(
    job_description: str,
    trade_category: TradeCategory,
    db: AsyncSession,
) -> JobSkillExtraction:
    """
    Transforma descripción informal en habilidades estructuradas.
    Ej: "instalé el cableado de una casa de 2 pisos en El Tambo,
         puse los tomacorrientes y el tablero"
    → habilidades: ["instalación eléctrica residencial", "cableado estructurado",
                    "tableros eléctricos", "tomacorrientes", "trabajo en altura"]
    → nivel estimado: intermedio-avanzado
    """
    normalized = apply_local_dictionary(job_description)        # 1. Diccionario Huancayo
    entities = nlp_oficio_pipeline(normalized)                  # 2. NER spaCy ajustado
    skills = map_to_standard_taxonomy(entities, trade_category) # 3. Taxonomía estándar
    return JobSkillExtraction(skills=skills, confidence_scores=...)

# ✅ Generación de CV automático desde portfolio (RF106–RF110)
async def generate_cv_from_portfolio(
    worker_id: UUID,
    template: CVTemplate,
    db: AsyncSession,
) -> bytes:  # PDF bytes
    """
    Compila los trabajos del portfolio en un CV estructurado:
    - Experiencia: lista ordenada por fecha
    - Habilidades: skills consolidadas
    - Calificaciones: promedio de ratings
    Usa plantillas diferenciadas por oficio.
    """
    ...

# ✅ Embedding para OFICIO — incluir habilidades del portfolio (M04 / RF056–RF065)
def build_trade_profile_text(worker: Worker, portfolio_entries: list[PortfolioEntry]) -> str:
    all_skills = consolidate_skills_from_portfolio(portfolio_entries)
    return (
        f"{worker.trade_category} | {worker.years_experience} años | "
        f"{worker.district} | {worker.avg_rating:.1f}/5.0 | "
        f"habilidades: {', '.join(all_skills)} | "
        f"trabajos realizados: {len(portfolio_entries)}"
    )
```

```tsx
// ✅ Frontend Portfolio — Ruta: /oficio/portfolio
// - Tarjetas visuales (imagen principal + descripción)
// - "Agregar trabajo" → formulario simple con cámara/galería
// - Tags de habilidades autogenerados (editables)
// - Vista pública compartible (/p/{slug})
// - "Generar mi CV" → PDF descargable
// - Toggle de disponibilidad en el header
// - Lenguaje de oficio, no de RRHH
```

#### C2 — Marketplace de Servicios de Oficio

Plataforma institucional respaldada por la DRTPE-Junín, con verificación de identidad por DNI, calificaciones verificadas y posibilidad de formalización contractual desde la propia plataforma. Cubre RF118–RF125.

```
Publicación de servicio:
  ├── Foto profesional del trabajador
  ├── Categoría del oficio (desplegable con íconos)
  ├── Título: "Instalación eléctrica residencial en Huancayo"
  ├── Descripción: lenguaje propio + NLP enriquece con keywords técnicas
  ├── Zona de cobertura: Huancayo / El Tambo / Chilca / región
  ├── Precio referencial: S/. por hora o por proyecto (opcional)
  ├── Disponibilidad: inmediata / esta semana / este mes
  ├── Botones: "Contactar" → chat interno | "Ver portfolio"
  └── Badge DRTPE: ✅ Identidad verificada | ⭐ X trabajos realizados

Feed del marketplace:
  ├── Categorías con íconos (Electricidad, Gasfitería, Carpintería, etc.)
  ├── Búsqueda por texto libre (NLP interpreta intención)
  ├── Filtro por distrito (Huancayo / El Tambo / Chilca)
  ├── Ordenamiento: más calificado / más cercano / disponible ahora
  └── Mapa de disponibilidad opcional (marcadores por distrito)
```

```python
# ✅ NLP para búsqueda en marketplace (RF118–RF122)
async def search_marketplace(
    query: str,
    district_filter: list[District] | None,
    db: AsyncSession,
) -> list[ServiceListing]:
    """
    Usuario: "necesito alguien que me arregle las cañerías del baño"
    → categoría: GASFITERIA
    → keywords: ["cañería", "baño", "plomería"]
    → similitud semántica + filtro de distrito
    → orden: 0.5×similitud + 0.3×rating + 0.2×disponibilidad
    """
    normalized_query = apply_local_dictionary(query)
    query_embedding = await generate_embedding_async(normalized_query)
    # pgvector cosine search sobre embeddings de listings
    ...
```

---

## ⚙️ STACK TECNOLÓGICO EXACTO

### Backend
- **Python 3.11** — sin excepciones, no usar 3.10 ni 3.12
- **FastAPI** — routers por módulo, prefijo `/api/v1/`
- **Pydantic v2** — validación de todos los schemas, no usar v1
- **SQLAlchemy 2.x** — ORM async, no escribir SQL crudo
- **Alembic** — todas las migraciones, nunca modificar tablas manualmente
- **PostgreSQL 15+** con extensión **pgvector** — columnas `vector(384)`
- **Redis** — caché, blacklist de tokens y broker de Celery
- **Celery** — todas las tareas pesadas son asíncronas (embeddings, generación CV, reportes, emails)
- **sentence-transformers** — modelo `paraphrase-multilingual-MiniLM-L12-v2` (384 dims)
- **spaCy** — modelo `es_core_news_md` para NER en español + pipeline custom para oficios
- **NLTK** — stopwords en español
- **scikit-learn** — modelos supervisados, métricas, re-ranking equitativo
- **WeasyPrint** — generación de CVs en PDF desde plantillas HTML/CSS
- **PyPDF2 + python-docx** — parsing de CVs subidos (flujo EXPERIENCIA)
- **structlog** — logging estructurado en JSON, nunca usar print()
- **bcrypt** — cost factor mínimo 12 para contraseñas
- **JWT RS256** — access token 24h, refresh token 7d

### Frontend
- **React 18** + **Vite**
- **Tailwind CSS** — sin CSS personalizado salvo variables
- **react-hook-form** + **zod** — validación de formularios
- **react-intl** — i18n español peruano (es-PE)
- **Axios** — cliente HTTP con interceptores JWT
- **Recharts** — gráficos del dashboard
- **react-dropzone** — upload de fotos para portfolio y CVs
- **WebSocket** — notificaciones en tiempo real (chat, postulaciones)
- **react-pdf** — preview de CVs sin descargar

### Infraestructura
- **Docker** + **docker-compose** — entorno completo reproducible
- **GitHub Actions** — CI/CD: lint → tests → build → staging → prod
- **GCP Cloud Run / AWS ECS** — despliegue en producción
- **GCS / S3** — almacenamiento de fotos de portfolio, CVs generados y subidos
- **Prometheus + Grafana** — monitoreo de métricas
- **OWASP ZAP** — DAST en pipeline CI/CD

---

## 🗄️ BASE DE DATOS — MODELO DE DATOS CLAVE

```sql
-- ✅ Tabla principal de trabajadores — incluye tipo obligatorio
CREATE TABLE workers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    worker_type     VARCHAR(20) NOT NULL CHECK (worker_type IN ('primer_empleo','experiencia','oficio')),
    full_name       BYTEA NOT NULL,       -- AES-256 cifrado
    dni             BYTEA NOT NULL,       -- AES-256 cifrado
    phone           BYTEA,                -- AES-256 cifrado
    district        VARCHAR(50),
    trade_category  VARCHAR(50),          -- solo para OFICIO
    years_experience INTEGER DEFAULT 0,
    avg_rating      DECIMAL(3,2) DEFAULT 0.00,
    is_available    BOOLEAN DEFAULT true,
    profile_completeness INTEGER DEFAULT 0, -- 0-100
    embedding       vector(384),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ✅ Portfolio de trabajos — solo para OFICIO
CREATE TABLE portfolio_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    title           VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,          -- descripción original del trabajador
    extracted_skills JSONB DEFAULT '[]',    -- habilidades extraídas por NLP
    photos          JSONB DEFAULT '[]',     -- URLs en GCS/S3
    period_start    DATE,
    period_end      DATE,
    client_rating   DECIMAL(3,2),
    is_public       BOOLEAN DEFAULT true,
    embedding       vector(384),            -- búsqueda semántica
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ✅ Publicaciones de marketplace — solo para OFICIO
CREATE TABLE service_listings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    trade_category  VARCHAR(50) NOT NULL,
    title           VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,
    enriched_keywords JSONB DEFAULT '[]',  -- keywords añadidas por NLP
    districts       JSONB DEFAULT '[]',    -- zonas de cobertura
    price_reference DECIMAL(10,2),
    price_unit      VARCHAR(20),           -- 'hora', 'proyecto', 'día'
    availability    VARCHAR(20),           -- 'inmediata','semana','mes'
    is_active       BOOLEAN DEFAULT true,
    embedding       vector(384),
    views_count     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ✅ Wizard progress — para PRIMER_EMPLEO (persistencia entre sesiones)
CREATE TABLE wizard_progress (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID NOT NULL REFERENCES workers(id) UNIQUE,
    current_step    INTEGER DEFAULT 1,     -- 1 a 6
    answers         JSONB DEFAULT '{}',
    extracted_skills JSONB DEFAULT '[]',
    last_saved_at   TIMESTAMPTZ DEFAULT now()
);

-- ✅ CVs generados — para PRIMER_EMPLEO y OFICIO
CREATE TABLE generated_cvs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    cv_type         VARCHAR(20) NOT NULL,  -- 'wizard_based', 'portfolio_based', 'parsed'
    template_used   VARCHAR(50),
    file_url        TEXT,                  -- URL en GCS/S3
    generated_at    TIMESTAMPTZ DEFAULT now()
);

-- ✅ Índices HNSW obligatorios
CREATE INDEX ON workers           USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX ON portfolio_entries USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX ON service_listings  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

**Convenciones generales:**
- **UUID** para todas las PKs, nunca integers autoincrement
- **timestamp with time zone** para todas las fechas (UTC siempre)
- Datos sensibles en columnas `bytea` con cifrado AES-256 a nivel aplicación
- Toda migración debe ser reversible (down migration obligatoria)
- Nombres de tablas: snake_case, plural

---

## 🤖 MOTOR ML/NLP — REGLAS CRÍTICAS

### Pipelines NLP diferenciados por tipo de usuario

```python
# ✅ PRIMER_EMPLEO — extracción desde lenguaje coloquial
NLP_PIPELINE_FIRST_JOB = {
    "model": "es_core_news_md",
    "components": ["tok2vec", "ner", "skill_matcher"],
    "custom_patterns": "data/patterns/soft_skills_es.jsonl",
    "output": "SkillList + ProfileText para embedding cold-start",
}

# ✅ EXPERIENCIA — parsing de CV estructurado
NLP_PIPELINE_EXPERIENCE = {
    "parser": "PyPDF2/python-docx",
    "extractor": "es_core_news_md + regex patterns",
    "confidence_threshold": 0.75,
    "entities": ["PERSON", "ORG", "DATE", "SKILL", "DEGREE"],
    "output": "ParsedCVResult con campos de confianza",
}

# ✅ OFICIO — extracción semántica desde descripciones de trabajos
NLP_PIPELINE_TRADE = {
    "model": "es_core_news_md",
    "custom_dict": "utils/local_dict/huancayo_trades.json",
    "components": ["tok2vec", "ner", "trade_skill_matcher"],
    "custom_patterns": "data/patterns/trade_skills_es.jsonl",
    "output": "TechnicalSkillList + TradeTaxonomyMapping",
}
```

### Pipeline NLP — pasos obligatorios (todos los tipos)

```
1. Normalización:
   minúsculas → ftfy (corregir acentos) → eliminar caracteres especiales
   → eliminar stopwords ES (NLTK) → lematizar (spaCy)
2. Aplicar diccionario local Huancayo (ANTES del embedding)
3. Extraer entidades nombradas con spaCy
4. Mapear a taxonomía estándar de habilidades
5. Generar embedding con sentence-transformers (MiniLM-L12-v2, 384 dims)
6. Almacenar en pgvector de forma asíncrona (Celery)
```

### Motor de Matching diferenciado

```python
# ✅ Score combinado — fórmula fija del proyecto (M05 / RF076–RF085)
def combined_score(
    cosine_sim: float,
    ml_score: float,
    reputation: float,
    worker_type: WorkerType,
) -> float:
    """
    Pesos por tipo de usuario:
    - PRIMER_EMPLEO: sin reputación, mayor peso a similitud
    - EXPERIENCIA:   balance estándar
    - OFICIO:        peso adicional a reputación (incluye portfolio)
    """
    weights = {
        WorkerType.PRIMER_EMPLEO: (0.65, 0.35, 0.00),  # cosine, ml, reputation
        WorkerType.EXPERIENCIA:   (0.50, 0.30, 0.20),
        WorkerType.OFICIO:        (0.45, 0.25, 0.30),
    }
    alpha, beta, gamma = weights[worker_type]
    return alpha * cosine_sim + beta * ml_score + gamma * (reputation / 5.0)

# ✅ Cold-start (RF096–RF105):
#   Estrategia: embedding desde respuestas del wizard / descripciones del portfolio
#   No usar historial de clicks inexistente — solo contenido del perfil
```

### Métricas de calidad del modelo

- F1-score mínimo aceptable en producción: **≥ 0.75**
- Si F1 < 0.70 → alerta automática al equipo (M10 / RF146–RF150)
- Disparate impact ratio mínimo: **≥ 0.80** por género y zona geográfica
- Si ratio < 0.80 → activar re-ranking equitativo automáticamente
- NER F1 para extracción de habilidades: **≥ 0.80** por pipeline
- CV parser accuracy: **≥ 0.75** en campos extraídos correctamente

---

## 📐 CONVENCIONES DE CÓDIGO

### Python / Backend

```python
# ✅ CORRECTO — async everywhere
async def get_worker_profile(worker_id: UUID, db: AsyncSession) -> WorkerProfile:
    ...

# ✅ CORRECTO — Pydantic v2 con worker_type obligatorio
class WorkerProfileCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    full_name: str    = Field(..., min_length=2, max_length=100)
    worker_type: WorkerType
    trade_category: TradeCategory | None = None  # requerido si worker_type == OFICIO
    district: District

# ✅ CORRECTO — SQLAlchemy 2.x async
result = await db.execute(select(Worker).where(Worker.id == worker_id))
worker = result.scalar_one_or_none()

# ❌ INCORRECTO — nunca SQL crudo
db.execute("SELECT * FROM workers WHERE id = %s", worker_id)

# ✅ CORRECTO — logging estructurado
import structlog
logger = structlog.get_logger()
logger.info(
    "embedding_generated",
    worker_id=str(worker_id),
    worker_type=worker.worker_type,
    duration_ms=elapsed,
)

# ❌ INCORRECTO
print(f"Embedding generado para {worker_id}")
```

### Embeddings NLP (CRÍTICO)

```python
# ✅ SIEMPRE usar el modelo correcto
MODEL_NAME    = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

# ✅ Construcción de texto de perfil diferenciada por tipo
def build_profile_text(worker: Worker, extra: dict) -> str:
    if worker.worker_type == WorkerType.PRIMER_EMPLEO:
        # Sin experiencia → énfasis en habilidades del wizard
        return (
            f"primer empleo | {worker.district} | "
            f"habilidades: {', '.join(extra.get('wizard_skills', []))} | "
            f"intereses: {extra.get('job_interests', '')}"
        )
    elif worker.worker_type == WorkerType.OFICIO:
        # Énfasis en trabajos realizados y skills del portfolio
        return (
            f"{worker.trade_category} | {worker.years_experience} años | "
            f"{worker.district} | {worker.avg_rating:.1f}/5.0 | "
            f"trabajos: {extra.get('portfolio_count', 0)} | "
            f"habilidades: {', '.join(extra.get('portfolio_skills', []))}"
        )
    else:  # EXPERIENCIA
        return (
            f"{extra.get('job_title', '')} | {worker.years_experience} años | "
            f"{worker.district} | {worker.avg_rating:.1f}/5.0 | "
            f"{extra.get('bio', '')}"
        )

# ✅ pgvector: usar cosine_distance
# SELECT id, 1 - (embedding <=> $1::vector) AS similarity
# FROM workers ORDER BY embedding <=> $1::vector LIMIT 10
```

### Estructura de endpoints

```python
# ✅ Endpoints diferenciados por tipo donde corresponda
@router.post("/api/v1/onboarding/detect-type",   response_model=OnboardingResponse)
@router.post("/api/v1/wizard/step/{step_number}", response_model=WizardStepResponse)
@router.post("/api/v1/cv/parse-upload",           response_model=ParsedCVResult)
@router.post("/api/v1/portfolio/entries",         response_model=PortfolioEntryResponse)
@router.post("/api/v1/marketplace/listings",      response_model=ServiceListingResponse)
@router.get ("/api/v1/marketplace/search",        response_model=list[ServiceListingResponse])
@router.post("/api/v1/cv/generate/{worker_id}",   response_model=GeneratedCVResponse)
@router.get ("/api/v1/match/{worker_id}",         response_model=MatchResponse)
@router.get ("/api/v1/jobs/feed",                 response_model=list[JobOfferResponse])

# ✅ Manejo de errores HTTP
raise HTTPException(status_code=404, detail="Trabajador no encontrado")
raise HTTPException(status_code=400, detail="Tipo de trabajador inválido para esta operación")
```

### React / Frontend

```tsx
// ✅ Enrutamiento condicional por tipo de usuario
const WorkerDashboard = () => {
  const { workerType } = useWorkerContext();
  return match(workerType)
    .with('primer_empleo', () => <PrimerEmpleoDashboard />)
    .with('experiencia',   () => <ExperienciaDashboard />)
    .with('oficio',        () => <OficioDashboard />)
    .exhaustive();
};

// ✅ i18n siempre, con claves específicas por tipo
const intl = useIntl();
<p>{intl.formatMessage({ id: `worker.${workerType}.profile.title` })}</p>

// ✅ Validación con zod + campos condicionales
const workerSchema = z.discriminatedUnion('workerType', [
  z.object({ workerType: z.literal('oficio'), tradeCategory: z.string().min(1) }),
  z.object({ workerType: z.literal('primer_empleo'), wizardStep: z.number().min(1).max(6) }),
  z.object({ workerType: z.literal('experiencia'), yearsExperience: z.number().min(0) }),
]);

// ❌ INCORRECTO — no hardcodear strings en español
<p>Perfil del trabajador</p>  // ❌
```

---

## 🔒 SEGURIDAD — REGLAS OBLIGATORIAS

Todas estas reglas instrumentan los RNF001–RNF006 (Seguridad ISO 27001) del subcapítulo 4.3.2.

- **NUNCA** exponer DNI, teléfono o email en logs ni en respuestas del cliente
- **NUNCA** escribir SQL con f-strings o concatenación — siempre ORM o parámetros
- **NUNCA** almacenar contraseñas en texto plano ni en logs
- **NUNCA** retornar stack traces en respuestas de producción
- **SIEMPRE** validar roles con el middleware RBAC antes de cada endpoint protegido
- **SIEMPRE** cifrar datos sensibles con AES-256 (DNI, teléfono)
- **SIEMPRE** agregar rate limiting en endpoints de auth, matching y marketplace
- Los tokens JWT **deben** invalidarse en Redis al hacer logout
- Fotos de portfolio: validar MIME (solo JPEG/PNG/WEBP), tamaño máx 5 MB, escaneo antivirus antes de almacenar
- URLs públicas de portfolio (`/p/{slug}`): no exponer UUID interno
- Cumplir **Ley N° 29733** (Perú): consentimiento informado antes de recolectar datos

```python
# ✅ Middleware de autorización RBAC
from app.core.security import require_role, UserRole

class UserRole(str, Enum):
    ADMIN     = "admin"      # personal DRTPE-Junín
    EMPLOYER  = "employer"   # empresas/personas que contratan
    WORKER    = "worker"     # cualquiera de los 3 tipos
    MODERATOR = "moderator"  # revisión de contenido marketplace

@router.post("/api/v1/portfolio/entries")
async def create_portfolio_entry(
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    # Validar adicionalmente que worker.worker_type == 'oficio'
    ...
```

---

## 📊 INDICADORES DE INVESTIGACIÓN (NO TOCAR SIN CONSULTAR)

KPIs de la tesis. El cálculo debe ser exacto y diferenciado cuando aplica.

| Indicador | Fórmula | Tabla BD | Aplica a |
|-----------|---------|----------|----------|
| Velocidad Inserción Laboral (VIL) | `días(registro → primer contrato)` | `contracts` | Los 3 tipos |
| Índice Visibilidad Perfil (IVP) | `(apariciones en búsquedas / total consultas) × 100` | `search_logs` | Los 3 tipos |
| Tasa Formalización | `(trabajadores con ≥1 contrato / total registrados) × 100` | `workers`, `contracts` | Los 3 tipos |
| Reputation Score | `promedio_ponderado(calificaciones, peso×2 últimas 5)` | `ratings` | EXPERIENCIA, OFICIO |
| Reducción Brecha Salarial | `((ingreso_post - ingreso_pre) / ingreso_pre) × 100` | `economic_surveys` | Los 3 tipos |
| Tasa Completitud CV (TCC) | `(perfiles con CV generado / total registrados) × 100` | `generated_cvs`, `workers` | PRIMER_EMPLEO, OFICIO |
| Índice Visibilidad Marketplace (IVM) | `(listados activos / total trabajadores OFICIO) × 100` | `service_listings`, `workers` | OFICIO |
| Tasa Cold-Start Superado | `(usuarios primer_empleo/oficio con ≥1 match / total) × 100` | `match_events` | PRIMER_EMPLEO, OFICIO |

---

## 🧪 TESTING — REGLAS

```bash
# Tests antes de cualquier commit
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80

# Tests obligatorios organizados por módulo
tests/unit/
  test_nlp_first_job.py        # extracción de habilidades del wizard
  test_nlp_cv_parser.py        # parsing de CVs subidos
  test_nlp_trade_portfolio.py  # extracción desde portfolio
  test_matching_engine.py      # motor ML diferenciado por worker_type
  test_cold_start.py           # cold-start primer_empleo y oficio
  test_marketplace_search.py   # búsqueda semántica marketplace
  test_cv_generator.py         # generación de CVs PDF
  test_reputation_score.py     # cálculo reputation
  test_auth_jwt.py             # autenticación y RBAC
tests/integration/
  test_api_onboarding.py       # detección de tipo
  test_api_wizard.py           # wizard 6 pasos
  test_api_portfolio.py        # CRUD portfolio + NLP extracción
  test_api_marketplace.py      # publicaciones + búsqueda
  test_api_matching.py         # emparejamiento por tipo
  test_api_jobs.py             # bolsa formal + DRTPE
```

- Cobertura mínima: **80%** — el CI bloquea merge si baja del umbral
- Los tests de NLP **deben** incluir textos en español coloquial de Huancayo por oficio
- `random_state=42` en todos los modelos ML para reproducibilidad
- Los tests del wizard deben cubrir los 6 pasos con respuestas parciales y completas
- Los tests del marketplace deben incluir búsquedas con términos locales Huancayo

---

## 🚀 COMANDOS FRECUENTES

```bash
# Levantar entorno completo
docker-compose up -d

# Ejecutar migraciones
alembic upgrade head

# Generar nueva migración
alembic revision --autogenerate -m "descripción"

# Worker Celery (embeddings, generación CV, emails)
celery -A app.tasks worker --loglevel=info

# Tests con cobertura
pytest --cov=app --cov-fail-under=80

# Linting
ruff check . && ruff format .

# Generar embeddings — diferenciado por tipo
python -m app.tasks.embeddings regenerate_all --type primer_empleo
python -m app.tasks.embeddings regenerate_all --type oficio
python -m app.tasks.embeddings regenerate_all --type all

# Regenerar CVs de oficio desde portfolios existentes
python -m app.tasks.cv_generator regenerate_trade_cvs

# Reentrenar modelo ML de matching
python -m app.ml.train --validate --deploy-if-better --worker-type all

# Reindexar marketplace (búsqueda semántica)
python -m app.tasks.marketplace reindex_listings

# Seed de datos de prueba diferenciados por tipo
python -m app.utils.seed --type primer_empleo --count 20
python -m app.utils.seed --type oficio --count 20
python -m app.utils.seed --type experiencia --count 20
```

---

## 📁 ARCHIVOS QUE NUNCA SE MODIFICAN SIN REVISIÓN

- `app/ml/train.py` — lógica de entrenamiento del modelo
- `app/nlp/embeddings.py` — generación de vectores
- `app/nlp/skill_taxonomies/` — taxonomías de habilidades
- `app/utils/local_dict/huancayo_trades.json` — diccionario local Huancayo
- `alembic/versions/*.py` — migraciones ya aplicadas
- `app/core/config.py` — configuración de producción
- `CLAUDE.md` — este archivo

---

## 🌍 CONTEXTO LOCAL — HUANCAYO

### Diccionario de equivalencias NLP (aplicar SIEMPRE antes del embedding)

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

### Categorías de oficio disponibles

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

- **Distritos del área urbana:** `Huancayo`, `El Tambo`, `Chilca`
- **Moneda:** `S/.` (Sol peruano, PEN) — formato `S/. 1,000.00`
- **Teléfonos:** formato `+51 9XXXXXXXX` (9 dígitos tras +51)
- **DNI:** 8 dígitos numéricos exactos
- **RUC:** 11 dígitos numéricos exactos

---

## ⛔ PROHIBICIONES ABSOLUTAS

- No usar **Django** ni **Flask** — solo FastAPI
- No usar **MongoDB** — solo PostgreSQL + pgvector
- No usar **NumPy < 1.24** ni **pandas < 2.0**
- No instalar librerías sin actualizar `requirements.txt`
- No hacer commits directos a `main` — siempre vía PR
- No exponer el endpoint `/api/v1/model/metrics` sin autenticación ADMIN
- No eliminar logs de auditoría — son inmutables por diseño
- No modificar el cálculo del `combined_score` sin validar el impacto en F1
- No mezclar lógica entre tipos de usuario — cada flujo (A/B/C) tiene sus propios servicios y componentes
- No omitir `worker_type` en ninguna operación de matching o recomendación
- No mostrar el marketplace a usuarios PRIMER_EMPLEO ni EXPERIENCIA (es exclusivo de OFICIO)
- No generar CVs de portfolio para usuarios PRIMER_EMPLEO (usan el wizard, no el portfolio)
- No almacenar fotos de portfolio en base64 en BD — siempre en GCS/S3 con URL firmada
- No implementar funcionalidad sin trazarla a un RF del subcapítulo 4.3.2

---

*Última actualización: Sprint 1 — Rojas Peña W. / Tovar Sanchez C.*
