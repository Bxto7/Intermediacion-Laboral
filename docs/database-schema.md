# Database Schema — Sistema de Intermediación Laboral
# PostgreSQL 15 + pgvector | Última actualización: Sprint 1

## Extensiones requeridas
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

---

## Tablas principales

### users
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    phone_encrypted BYTEA,                          -- AES-256 cifrado
    hashed_password VARCHAR(255) NOT NULL,          -- bcrypt cost=12
    role            VARCHAR(20) NOT NULL,           -- WORKER | EMPLOYER | ADMIN | DRTPE_VIEWER | RESEARCHER
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,
    two_fa_secret   VARCHAR(100),                   -- TOTP secret cifrado
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### workers
```sql
CREATE TABLE workers (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name            VARCHAR(100) NOT NULL,
    dni_encrypted        BYTEA,                     -- AES-256 cifrado
    office               VARCHAR(100) NOT NULL,     -- oficio principal
    secondary_offices    TEXT[],                    -- hasta 3 oficios
    years_experience     SMALLINT NOT NULL CHECK (years_experience >= 0),
    bio                  TEXT,                      -- descripción libre máx 2000 chars
    zone                 VARCHAR(50) NOT NULL,      -- Huancayo | El Tambo | Chilca
    hourly_rate          NUMERIC(8,2),              -- tarifa S/. por hora
    project_rate         NUMERIC(8,2),              -- tarifa S/. por proyecto
    is_available         BOOLEAN DEFAULT TRUE,
    availability_schedule JSONB,                   -- {lunes: [{start: "08:00", end: "17:00"}]}
    profile_completeness SMALLINT DEFAULT 0,        -- 0-100%
    avg_rating           NUMERIC(3,2) DEFAULT 0.00,
    total_contracts      INTEGER DEFAULT 0,
    identity_verified    BOOLEAN DEFAULT FALSE,
    referral_code        VARCHAR(10) UNIQUE,
    referred_by          UUID REFERENCES workers(id),
    embedding            vector(384),               -- paraphrase-multilingual-MiniLM-L12-v2
    embedding_updated_at TIMESTAMPTZ,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Índice HNSW para búsqueda vectorial (CRÍTICO)
CREATE INDEX workers_embedding_hnsw_idx
ON workers USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Índices adicionales
CREATE INDEX workers_zone_idx ON workers(zone);
CREATE INDEX workers_office_idx ON workers(office);
CREATE INDEX workers_available_idx ON workers(is_available) WHERE is_available = TRUE;
CREATE INDEX workers_completeness_idx ON workers(profile_completeness) WHERE profile_completeness >= 60;
```

### employers
```sql
CREATE TABLE employers (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name         VARCHAR(200) NOT NULL,
    dni_encrypted     BYTEA,
    ruc_encrypted     BYTEA,
    employer_type     VARCHAR(20) NOT NULL,         -- PERSON | COMPANY
    sector            VARCHAR(50),                  -- hogar | empresa | construcción | industria
    zone              VARCHAR(50) NOT NULL,
    avg_budget        NUMERIC(8,2),
    is_verified       BOOLEAN DEFAULT FALSE,
    total_hires       INTEGER DEFAULT 0,
    avg_rating        NUMERIC(3,2) DEFAULT 0.00,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);
```

### job_requests
```sql
CREATE TABLE job_requests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employer_id     UUID NOT NULL REFERENCES employers(id),
    title           VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,                  -- máx 300 palabras
    office_required VARCHAR(100) NOT NULL,
    zone            VARCHAR(50) NOT NULL,
    required_date   DATE,
    duration_days   SMALLINT,
    max_budget      NUMERIC(8,2),
    status          VARCHAR(20) DEFAULT 'PUBLISHED', -- DRAFT|PUBLISHED|IN_PROGRESS|COMPLETED|CANCELLED
    sector          VARCHAR(50),                    -- clasificado automáticamente por NLP
    is_recurring    BOOLEAN DEFAULT FALSE,
    recurrence_config JSONB,                        -- {frequency: "monthly", count: 12}
    embedding       vector(384),                    -- embedding de la descripción
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Índice HNSW para matching de solicitudes
CREATE INDEX job_requests_embedding_hnsw_idx
ON job_requests USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX job_requests_status_idx ON job_requests(status) WHERE status = 'PUBLISHED';
CREATE INDEX job_requests_zone_idx ON job_requests(zone);
```

### contracts
```sql
CREATE TABLE contracts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_request_id  UUID NOT NULL REFERENCES job_requests(id),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    employer_id     UUID NOT NULL REFERENCES employers(id),
    status          VARCHAR(20) DEFAULT 'CONFIRMED', -- CONFIRMED|IN_PROGRESS|COMPLETED|CANCELLED|DISPUTED
    agreed_rate     NUMERIC(8,2),
    rate_type       VARCHAR(10),                    -- HOURLY | PROJECT | DAILY
    start_date      DATE,
    end_date        DATE,
    final_amount    NUMERIC(8,2),
    payment_method  VARCHAR(30),                    -- YAPE | PLIN | TRANSFER | CASH
    payment_confirmed BOOLEAN DEFAULT FALSE,
    work_evidence   TEXT[],                         -- URLs de fotos del trabajo realizado
    description_done TEXT,
    cancelled_reason VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX contracts_worker_idx ON contracts(worker_id);
CREATE INDEX contracts_employer_idx ON contracts(employer_id);
CREATE INDEX contracts_status_idx ON contracts(status);
```

### ratings
```sql
CREATE TABLE ratings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id     UUID NOT NULL REFERENCES contracts(id),
    rater_id        UUID NOT NULL REFERENCES users(id),
    rated_id        UUID NOT NULL REFERENCES users(id),
    rater_role      VARCHAR(10) NOT NULL,           -- WORKER | EMPLOYER
    overall_score   NUMERIC(2,1) NOT NULL CHECK (overall_score BETWEEN 1 AND 5),
    quality_score   NUMERIC(2,1),
    punctuality_score NUMERIC(2,1),
    communication_score NUMERIC(2,1),
    fairness_score  NUMERIC(2,1),
    comment         VARCHAR(300),
    sentiment       VARCHAR(10),                    -- POSITIVE | NEUTRAL | NEGATIVE (NLP)
    is_reported     BOOLEAN DEFAULT FALSE,
    is_removed      BOOLEAN DEFAULT FALSE,
    worker_response VARCHAR(200),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(contract_id, rater_id)
);
```

### recommendation_log
```sql
-- Tabla central para re-entrenamiento ML y análisis de tesis
CREATE TABLE recommendation_log (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_request_id    UUID NOT NULL REFERENCES job_requests(id),
    worker_id         UUID NOT NULL REFERENCES workers(id),
    cosine_similarity NUMERIC(6,4) NOT NULL,
    ml_score          NUMERIC(6,4),
    reputation_score  NUMERIC(6,4),
    combined_score    NUMERIC(6,4) NOT NULL,
    shap_top_features JSONB,                        -- top 3 features SHAP
    rank_position     SMALLINT,
    was_selected      BOOLEAN DEFAULT FALSE,        -- feedback loop
    resulted_in_contract BOOLEAN DEFAULT FALSE,
    alpha_used        NUMERIC(3,2) DEFAULT 0.50,
    beta_used         NUMERIC(3,2) DEFAULT 0.30,
    gamma_used        NUMERIC(3,2) DEFAULT 0.20,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX rec_log_job_idx ON recommendation_log(job_request_id);
CREATE INDEX rec_log_worker_idx ON recommendation_log(worker_id);
CREATE INDEX rec_log_contract_idx ON recommendation_log(resulted_in_contract);
CREATE INDEX rec_log_date_idx ON recommendation_log(created_at);
```

### applications (postulaciones)
```sql
CREATE TABLE applications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_request_id  UUID NOT NULL REFERENCES job_requests(id),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    message         TEXT,                           -- máx 200 palabras
    proposed_rate   NUMERIC(8,2),
    status          VARCHAR(20) DEFAULT 'PENDING',  -- PENDING|ACCEPTED|REJECTED
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_request_id, worker_id)
);
```

### notifications
```sql
CREATE TABLE notifications (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id),
    type        VARCHAR(50) NOT NULL,               -- NEW_MATCH|NEW_APPLICATION|CONTRACT_CONFIRMED|NEW_RATING
    title       VARCHAR(200) NOT NULL,
    body        TEXT,
    action_url  VARCHAR(500),
    is_read     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX notifications_user_unread_idx ON notifications(user_id, is_read) WHERE is_read = FALSE;
```

### search_logs (para IVP — Índice Visibilidad Perfil)
```sql
CREATE TABLE search_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_request_id  UUID REFERENCES job_requests(id),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    appeared_in_results BOOLEAN DEFAULT TRUE,
    rank_position   SMALLINT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX search_logs_worker_date_idx ON search_logs(worker_id, created_at);
```

### economic_surveys (cuestionario pre/post test de la tesis)
```sql
CREATE TABLE economic_surveys (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id             UUID NOT NULL REFERENCES workers(id),
    survey_type           VARCHAR(10) NOT NULL,     -- PRE | POST
    monthly_income_before NUMERIC(8,2),             -- ingresos antes S/.
    monthly_income_after  NUMERIC(8,2),             -- ingresos después S/.
    formal_contracts_6m   SMALLINT,                 -- contratos formales últimos 6 meses
    informal_contracts_6m SMALLINT,
    days_to_first_job     SMALLINT,                 -- velocidad inserción laboral
    digital_barrier_device VARCHAR(30),             -- smartphone | tablet | laptop | none
    digital_barrier_connectivity VARCHAR(20),       -- good | regular | poor
    sus_score             NUMERIC(5,2),             -- System Usability Scale 0-100
    equity_perception     SMALLINT CHECK (equity_perception BETWEEN 1 AND 5),
    consent_given         BOOLEAN DEFAULT FALSE,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);
```

### audit_logs (inmutables)
```sql
CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id   UUID,
    old_values  JSONB,
    new_values  JSONB,
    ip_address  INET,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
-- NUNCA hacer DELETE ni UPDATE en esta tabla
CREATE INDEX audit_logs_user_idx ON audit_logs(user_id);
CREATE INDEX audit_logs_date_idx ON audit_logs(created_at);
```

### system_config
```sql
CREATE TABLE system_config (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT NOT NULL,
    description TEXT,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Valores iniciales
INSERT INTO system_config VALUES
('matching_alpha', '0.5', 'Peso similitud coseno en score combinado'),
('matching_beta',  '0.3', 'Peso modelo ML en score combinado'),
('matching_gamma', '0.2', 'Peso reputación en score combinado'),
('top_k_default',  '10',  'Número de candidatos por defecto'),
('similarity_threshold', '0.3', 'Similitud coseno mínima para recomendar'),
('min_profile_completeness', '60', 'Completitud mínima para aparecer en matching'),
('max_active_applications', '10', 'Máximo postulaciones activas por trabajador'),
('f1_alert_threshold', '0.70', 'F1-score mínimo antes de alertar'),
('disparate_impact_minimum', '0.80', 'DI ratio mínimo aceptable');
```

---

## Relaciones principales

```
users ──< workers ──< applications >── job_requests >── employers
                  ──< contracts    >── job_requests
                  ──< ratings
                  ──< recommendation_log
                  ──< search_logs
                  ──< economic_surveys
```

---

## Notas críticas

- Todas las PKs son **UUID** — nunca integer autoincrement
- Todas las fechas en **TIMESTAMPTZ** (UTC siempre)
- Datos sensibles (DNI, RUC, teléfono) en columnas **BYTEA** con cifrado AES-256
- El campo `embedding vector(384)` usa el modelo `paraphrase-multilingual-MiniLM-L12-v2`
- Los índices HNSW son **críticos** — sin ellos el matching es lento
- La tabla `audit_logs` es **append-only** — nunca DELETE/UPDATE
- La tabla `recommendation_log` es la fuente de datos para re-entrenamiento ML
