Lee el archivo CLAUDE.md que está en la raíz del repositorio antes de escribir cualquier línea de código. Es la fuente de verdad de arquitectura, convenciones y prohibiciones del proyecto. Si algo de este prompt contradice el CLAUDE.md, el CLAUDE.md tiene prioridad.

Para todo el trabajo de backend usa la herramienta Bash. Con ella ejecuta comandos de shell, crea directorios, escribe archivos Python, corre migraciones de Alembic, instala dependencias con pip y lanza los tests con pytest. No uses ninguna otra herramienta para el backend.

---

Estás en el Sprint 1 del sistema de intermediación laboral con Machine Learning y NLP desarrollado en articulación con la DRTPE-Junín, Huancayo, Perú. El proyecto atiende a tres tipos de usuario que se detectan en el onboarding: PRIMER_EMPLEO (jóvenes sin historial laboral), EXPERIENCIA (trabajadores con historial documentado) y OFICIO (trabajadores de oficios manuales con competencias no certificadas). Todo el código que escribas debe trazarse a un requerimiento funcional del subcapítulo 4.3.2 del plan de tesis, que documenta 165 RF y 23 RNF. Al final de cada archivo que crees, agrega un comentario indicando qué RF implementa.

El objetivo de este sprint es construir la base funcional del sistema: infraestructura Docker, configuración central del backend, esquema completo de base de datos, autenticación JWT y el flujo de onboarding de detección de tipo de usuario. Al terminar debe ser posible registrar un usuario, clasificarlo en uno de los tres tipos y persistir su perfil base. Los RF cubiertos son RF001 al RF035, correspondientes a los módulos M01 (Identidad y Autenticación) y M02 (Perfil del Trabajador), más los 23 RNF de infraestructura y seguridad.

---

TAREA 1 — ESTRUCTURA DEL REPOSITORIO Y DOCKER

Crea la estructura completa de carpetas usando mkdir -p. No omitas ninguna aunque esté vacía: coloca __init__.py en todas las carpetas Python y .gitkeep en las de frontend.

backend/app/api/v1/
backend/app/core/
backend/app/models/
backend/app/schemas/
backend/app/services/onboarding/
backend/app/services/cv_builder/
backend/app/services/portfolio/
backend/app/services/job_board/
backend/app/services/marketplace/
backend/app/services/matching/
backend/app/nlp/skill_extractor/
backend/app/nlp/embeddings/
backend/app/nlp/cv_parser/
backend/app/nlp/skill_suggester/
backend/app/nlp/portfolio_nlp/
backend/app/ml/matching_engine/
backend/app/ml/equity_ranker/
backend/app/ml/cold_start/
backend/app/ml/explainer/
backend/app/integrations/drtpe/
backend/app/tasks/
backend/app/utils/local_dict/
backend/app/utils/cv_templates/
backend/migrations/
backend/tests/unit/
backend/tests/integration/
frontend/src/onboarding/
frontend/src/modules/primer-empleo/
frontend/src/modules/experiencia/
frontend/src/modules/oficio/
frontend/src/shared/
frontend/src/matching/
frontend/src/employer/
frontend/src/admin/

Crea docker-compose.yml en la raíz con cinco servicios:

El servicio db usa postgres:15-alpine, expone el puerto 5432, monta un volumen postgres_data y ejecuta un init.sql que habilita la extensión pgvector con CREATE EXTENSION IF NOT EXISTS vector;. Las variables de entorno son POSTGRES_DB=intermediacion_laboral, POSTGRES_USER=postgres, POSTGRES_PASSWORD=postgres.

El servicio redis usa redis:7-alpine, expone el puerto 6379.

El servicio backend usa una imagen construida desde backend/Dockerfile, expone el puerto 8000, monta el código fuente como volumen para hot-reload, depende de db y redis, y arranca con uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload. Carga las variables desde backend/.env.

El servicio celery_worker comparte la misma imagen del backend, arranca con celery -A app.tasks worker --loglevel=info y depende de db y redis.

El servicio frontend usa node:20-alpine, expone el puerto 5173, monta frontend/ como volumen y arranca con npm run dev -- --host.

Crea backend/Dockerfile con Python 3.11-slim, copia requirements.txt, instala dependencias con pip install --no-cache-dir -r requirements.txt, descarga el modelo de spaCy con python -m spacy download es_core_news_md y establece el WORKDIR en /app.

Crea backend/requirements.txt con estas versiones exactas:

fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.1
pydantic-settings==2.2.1
sqlalchemy==2.0.30
alembic==1.13.1
asyncpg==0.29.0
pgvector==0.2.5
redis==5.0.4
celery==5.4.0
sentence-transformers==2.7.0
spacy==3.7.4
nltk==3.8.1
scikit-learn==1.4.2
numpy==1.26.4
pandas==2.2.2
weasyprint==62.3
pypdf2==3.0.1
python-docx==1.1.2
structlog==24.1.0
bcrypt==4.1.3
python-jose[cryptography]==3.3.0
python-multipart==0.0.9
httpx==0.27.0
cryptography==42.0.7
pytest==8.2.0
pytest-asyncio==0.23.6
pytest-cov==5.0.0
ruff==0.4.4
ftfy==6.2.0

Crea backend/.env.example con este contenido:

DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/intermediacion_laboral
REDIS_URL=redis://redis:6379/0
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=keys/private.pem
JWT_PUBLIC_KEY_PATH=keys/public.pem
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
AES_KEY=cambia-esto-exactamente-32-bytes!!
BCRYPT_COST=12
GCS_BUCKET_NAME=intermediacion-laboral-dev
ENVIRONMENT=development
LOG_LEVEL=INFO

Agrega al final del docker-compose.yml un bloque volumes: con postgres_data.

---

TAREA 2 — CONFIGURACIÓN CENTRAL DEL BACKEND (app/core/)

Implementa estos cuatro módulos. Nunca uses print(); usa structlog en todos.

app/core/config.py: Clase Settings heredando de pydantic_settings.BaseSettings. Campos: DATABASE_URL, REDIS_URL, JWT_ALGORITHM (literal "RS256"), JWT_PRIVATE_KEY_PATH, JWT_PUBLIC_KEY_PATH, ACCESS_TOKEN_EXPIRE_MINUTES (int), REFRESH_TOKEN_EXPIRE_DAYS (int), AES_KEY (str), BCRYPT_COST (int default 12), ENVIRONMENT (literal "development" | "production"), LOG_LEVEL. Agrega un validator de modelo que verifique que AES_KEY tiene exactamente 32 bytes al codificarse en UTF-8; si no, lanza ValueError. Expón una instancia singleton settings = Settings(). Cubre RNF001, RNF018.

app/core/database.py: Crea AsyncEngine con create_async_engine usando settings.DATABASE_URL y pool_pre_ping=True. Crea AsyncSessionLocal con async_sessionmaker(engine, expire_on_commit=False). Implementa get_db() como dependency FastAPI que abre una sesión, la cede con yield y la cierra en el finally. Implementa init_db() async que ejecuta CREATE EXTENSION IF NOT EXISTS vector; usando text() de SQLAlchemy y registra el resultado en structlog. Cubre RNF011, RNF021.

app/core/redis_client.py: Crea un cliente Redis async usando redis.asyncio.from_url(settings.REDIS_URL, decode_responses=True). Expón get_redis() como función que devuelve el cliente singleton. Agrega reconexión automática con retry_on_error=[ConnectionError]. Cubre RNF007.

app/core/logging.py: Configura structlog con ProcessorFormatter de structlog.stdlib, salida en JSON con campos timestamp (ISO 8601), level, event, module. Expón configure_logging() que debe llamarse en el startup de FastAPI. Cubre RNF018.

app/core/security.py: Implementa las siguientes funciones.

hash_password(plain: str) -> str: usa bcrypt con el cost factor de settings.BCRYPT_COST.

verify_password(plain: str, hashed: str) -> bool: verifica contra el hash.

encrypt_field(value: str) -> bytes: cifra con AES-256-GCM usando settings.AES_KEY. El resultado debe incluir el nonce (12 bytes) concatenado con el ciphertext para poder descifrar después sin almacenar el nonce por separado.

decrypt_field(value: bytes) -> str: extrae el nonce de los primeros 12 bytes y descifra el resto.

Genera un par de claves RS256 al iniciar si no existen los archivos indicados en JWT_PRIVATE_KEY_PATH y JWT_PUBLIC_KEY_PATH. Usa cryptography.hazmat para generarlas.

create_access_token(data: dict) -> str: crea JWT RS256 con los datos, agrega exp (ACCESS_TOKEN_EXPIRE_MINUTES) y un jti (UUID4 como string).

create_refresh_token(data: dict) -> str: igual pero con REFRESH_TOKEN_EXPIRE_DAYS.

verify_token(token: str) -> dict: decodifica con la clave pública RS256. Si el token está en la blacklist de Redis lanza HTTPException 401 con detail "Token revocado". Si está expirado o es inválido lanza HTTPException 401.

invalidate_token(jti: str, expires_in_seconds: int) -> None: guarda la clave "blacklist:{jti}" en Redis con TTL igual a expires_in_seconds.

is_token_blacklisted(jti: str) -> bool: verifica si la clave existe en Redis.

Enum UserRole(str, Enum) con admin, employer, worker, moderator.

require_role(*roles: UserRole): dependency FastAPI que llama a verify_token con el Bearer token del header Authorization, verifica que el campo role del payload esté en roles, lanza HTTPException 403 si no. Devuelve el payload completo.

Cubre RF001–RF012, RNF001–RNF006.

---

TAREA 3 — MODELOS SQLALCHEMY 2.x (app/models/)

Usa Mapped y mapped_column de sqlalchemy.orm. UUID siempre como tipo de columna con server_default=text("gen_random_uuid()") y primary_key=True. BYTEA para campos cifrados. TIMESTAMPTZ para fechas. Nunca uses Integer como PK.

app/models/user.py — tabla users:
id UUID PK, email VARCHAR(255) UNIQUE NOT NULL, hashed_password VARCHAR(255) NOT NULL, role VARCHAR(20) NOT NULL con CHECK IN ('admin','employer','worker','moderator'), is_active BOOLEAN DEFAULT true, email_verified BOOLEAN DEFAULT false, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now(). Cubre RF001–RF003.

app/models/worker.py — tabla workers exactamente como en CLAUDE.md:
id UUID PK, user_id UUID FK→users.id NOT NULL, worker_type VARCHAR(20) NOT NULL CHECK IN ('primer_empleo','experiencia','oficio'), full_name BYTEA NOT NULL, dni BYTEA NOT NULL, phone BYTEA, district VARCHAR(50), trade_category VARCHAR(50), years_experience INTEGER DEFAULT 0, avg_rating DECIMAL(3,2) DEFAULT 0.00, is_available BOOLEAN DEFAULT true, profile_completeness INTEGER DEFAULT 0, embedding vector(384), created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now(). Importa Vector de pgvector.sqlalchemy para el tipo de la columna embedding. Cubre RF016–RF025.

app/models/employer.py — tabla employers:
id UUID PK, user_id UUID FK→users.id NOT NULL, company_name VARCHAR(255) NOT NULL, ruc BYTEA NOT NULL, contact_name BYTEA NOT NULL, phone BYTEA, district VARCHAR(50), sector VARCHAR(100), is_verified BOOLEAN DEFAULT false, created_at TIMESTAMPTZ DEFAULT now(). Cubre RF036–RF040.

app/models/portfolio.py — tabla portfolio_entries:
id UUID PK, worker_id UUID FK→workers.id NOT NULL, title VARCHAR(200) NOT NULL, description TEXT NOT NULL (descripción original del trabajador, sin cifrar), extracted_skills JSONB DEFAULT '[]' (habilidades extraídas por NLP), photos JSONB DEFAULT '[]' (URLs en GCS/S3, nunca base64), period_start DATE, period_end DATE, client_rating DECIMAL(3,2), is_public BOOLEAN DEFAULT true, embedding vector(384), created_at TIMESTAMPTZ DEFAULT now(). Importa Vector de pgvector.sqlalchemy. Cubre RF056–RF065.

app/models/wizard.py — tabla wizard_progress:
id UUID PK, worker_id UUID FK→workers.id NOT NULL UNIQUE (un solo registro por trabajador), current_step INTEGER DEFAULT 1 (rango 1 a 6), answers JSONB DEFAULT '{}' (respuestas acumuladas por paso), extracted_skills JSONB DEFAULT '[]', last_saved_at TIMESTAMPTZ DEFAULT now(). No tiene updated_at; usar last_saved_at para control de versión. Cubre RF096–RF105.

app/models/generated_cv.py — tabla generated_cvs:
id UUID PK, worker_id UUID FK→workers.id NOT NULL, cv_type VARCHAR(20) NOT NULL con CHECK IN ('wizard_based','portfolio_based','parsed'), template_used VARCHAR(50), file_url TEXT (URL en GCS/S3), generated_at TIMESTAMPTZ DEFAULT now(). No tiene updated_at porque el CV es inmutable una vez generado; se crea uno nuevo en cada regeneración. Cubre RF106–RF110.

app/models/service_listing.py — tabla service_listings:
id UUID PK, worker_id UUID FK→workers.id NOT NULL, trade_category VARCHAR(50) NOT NULL, title VARCHAR(200) NOT NULL, description TEXT NOT NULL, enriched_keywords JSONB DEFAULT '[]' (keywords añadidas por NLP), districts JSONB DEFAULT '[]' (zonas de cobertura: Huancayo/El Tambo/Chilca), price_reference DECIMAL(10,2), price_unit VARCHAR(20) con CHECK IN ('hora','proyecto','día'), availability VARCHAR(20) con CHECK IN ('inmediata','semana','mes'), is_active BOOLEAN DEFAULT true, embedding vector(384), views_count INTEGER DEFAULT 0, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now(). Importa Vector de pgvector.sqlalchemy. Cubre RF118–RF125.

app/models/audit_log.py — tabla audit_logs con id UUID PK, user_id UUID FK→users.id nullable, action VARCHAR(100) NOT NULL, entity_type VARCHAR(50), entity_id UUID, ip_address VARCHAR(45), user_agent TEXT, details JSONB DEFAULT '{}', created_at TIMESTAMPTZ DEFAULT now(). Esta tabla es inmutable: no tiene método delete ni updated_at. Cubre RNF001, RNF006.

app/models/__init__.py: importa todos los modelos para que Alembic los detecte.

---

TAREA 4 — SCHEMAS PYDANTIC V2 (app/schemas/)

Todos los schemas usan model_config = ConfigDict(str_strip_whitespace=True).

app/schemas/common.py:
WorkerType(str, Enum) con primer_empleo, experiencia, oficio.
TradeCategory(str, Enum) con estos 13 valores exactos (el valor del enum es el string almacenado en BD): ELECTRICIDAD="Electricidad", GASFITERIA="Gasfitería", CARPINTERIA="Carpintería", ALBANILERIA="Albañilería", PINTURA="Pintura", MECANICA="Mecánica automotriz", TECHADO="Techado", SOLDADURA="Soldadura y metalurgia", JARDINERIA="Jardinería", LIMPIEZA="Limpieza y mantenimiento", COCINA="Cocina y pastelería", COSTURA="Costura y confección", OTROS="Otros oficios".
District(str, Enum) con Huancayo, El_Tambo, Chilca, Otro.
UserRole(str, Enum) con admin, employer, worker, moderator.

app/schemas/auth.py:
RegisterRequest con email (EmailStr), password (str, min_length=8, max_length=128), role (UserRole, default worker).
LoginRequest con email (EmailStr), password (str).
TokenResponse con access_token (str), refresh_token (str), token_type (str, default "bearer").
RefreshRequest con refresh_token (str).
MessageResponse con message (str).

app/schemas/onboarding.py:
OnboardingAnswers con is_first_job (bool), is_trade_worker (bool), trade_category (TradeCategory | None, default None). Agrega un validator de modelo que verifique: si is_first_job es False y is_trade_worker es True entonces trade_category no puede ser None; lanza ValueError con mensaje descriptivo si lo es.
OnboardingResponse con worker_type (WorkerType), worker_id (UUID), next_step (str), message (str).
OnboardingStatus con worker_type (WorkerType | None), profile_completeness (int), is_onboarded (bool).

app/schemas/worker.py:
WorkerProfileCreate con full_name (str, min 2, max 100), dni (str, exactamente 8 dígitos numéricos validado con regex), phone (str | None, formato +51 9XXXXXXXX validado), district (District), trade_category (TradeCategory | None), years_experience (int, ge=0, le=50), worker_type (WorkerType).
WorkerProfileResponse con id (UUID), worker_type (WorkerType), full_name (str), district (District | None), trade_category (TradeCategory | None), years_experience (int), avg_rating (float), is_available (bool), profile_completeness (int), created_at (datetime). Sin dni. Sin phone en la respuesta pública.
WorkerProfileUpdate con todos los campos opcionales excepto worker_type (que no se puede cambiar aquí) y dni (que no se puede cambiar sin flujo especial).
CompletenessResponse con percentage (int), missing_fields (list[str]), next_action (str).

---

TAREA 5 — MIGRACIÓN INICIAL CON ALEMBIC

Configura Alembic para trabajo completamente async.

En alembic/env.py reemplaza el contenido por una configuración que use AsyncEngine y run_async_migrations() con asyncio.run(). Importa todos los modelos desde app.models para que autogenerate los detecte. Usa target_metadata = Base.metadata.

En alembic.ini configura script_location = migrations y sqlalchemy.url = ${DATABASE_URL} para que lea de la variable de entorno.

Genera la migración inicial con alembic revision --autogenerate -m "001_initial_schema". Luego edita el archivo generado para agregar manualmente al final del upgrade() las siguientes instrucciones que autogenerate no puede inferir:

op.execute("CREATE EXTENSION IF NOT EXISTS vector")
op.execute("CREATE INDEX IF NOT EXISTS idx_workers_embedding ON workers USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)")
op.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_embedding ON portfolio_entries USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)")
op.execute("CREATE INDEX IF NOT EXISTS idx_listings_embedding ON service_listings USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)")

El downgrade() debe eliminar los índices, las tablas en orden inverso a las FK y la extensión vector.

---

TAREA 6 — ENDPOINTS DE AUTENTICACIÓN (app/api/v1/auth.py)

Router con prefijo /api/v1/auth y tag "Autenticación".

POST /api/v1/auth/register — RF001–RF003
Recibe RegisterRequest. Verifica que el email no exista en users; si existe devuelve 409. Hashea la contraseña con hash_password. Inserta en users. Genera access y refresh token con create_access_token y create_refresh_token incluyendo sub=str(user.id) y role=user.role. Registra en audit_logs con action="user_registered". Devuelve TokenResponse. Rate limit de 10 intentos por hora por IP usando Redis con clave "rl:register:{ip}".

POST /api/v1/auth/login — RF004–RF006
Recibe LoginRequest. Busca el usuario por email. Si no existe o verify_password falla devuelve 401 con mensaje genérico (no revelar cuál campo es incorrecto). Genera tokens. Registra en audit_logs. Devuelve TokenResponse. Rate limit de 20 intentos por hora por IP.

POST /api/v1/auth/refresh — RF007
Recibe RefreshRequest. Llama verify_token sobre el refresh_token. Verifica que el campo type del payload sea "refresh". Invalida el jti del token viejo. Genera nuevo par de tokens. Devuelve TokenResponse.

POST /api/v1/auth/logout — RF008
Requiere Bearer token válido (any role). Extrae jti del access token y lo invalida en Redis con TTL igual al tiempo restante hasta su exp. Si hay refresh_token en el body también lo invalida. Registra en audit_logs. Devuelve MessageResponse con "Sesión cerrada correctamente".

POST /api/v1/auth/verify-email — RF009
Recibe un campo token (str). Busca en Redis la clave "email_verify:{token}". Si no existe devuelve 400. Si existe, actualiza email_verified=true en users y borra la clave de Redis. Devuelve MessageResponse.

POST /api/v1/auth/forgot-password — RF010–RF011
Recibe email (str). Siempre devuelve 200 con el mismo mensaje sin importar si el email existe (evitar enumeración de usuarios). Si el email existe, genera un UUID como token, guarda en Redis "pwd_reset:{token}"=user_id con TTL 3600 segundos, encola tarea Celery send_reset_email (stub en Sprint 1 que solo registra en log). Cubre RNF003.

POST /api/v1/auth/reset-password — RF012
Recibe token (str) y new_password (str, min 8). Busca en Redis "pwd_reset:{token}". Si no existe devuelve 400. Si existe, actualiza hashed_password en users, borra el token de Redis, invalida todos los tokens activos del usuario (guarda "blacklist:user:{user_id}" en Redis). Devuelve MessageResponse.

En todos los endpoints: nunca loguear contraseñas, tokens completos ni DNI. Usar structlog con campos event, user_id (cuando disponible), ip, duration_ms. Nunca devolver stack trace; el handler global de excepciones de main.py lo captura.

---

TAREA 7 — SERVICIO Y ENDPOINTS DE ONBOARDING (app/services/onboarding/ y app/api/v1/onboarding.py)

app/services/onboarding/detector.py:

detect_worker_type(answers: OnboardingAnswers) -> WorkerType: implementa la lógica de tres ramas. Si is_first_job es True devuelve PRIMER_EMPLEO. Si is_first_job es False y is_trade_worker es True devuelve OFICIO. En cualquier otro caso devuelve EXPERIENCIA. Esta función es síncrona y pura (sin efectos secundarios), lo que facilita el testing. Cubre RF016–RF018.

create_worker_profile(user_id: UUID, worker_type: WorkerType, trade_category: TradeCategory | None, db: AsyncSession) -> Worker: crea el registro en workers. Los campos full_name y dni se cifran con encrypt_field usando valores placeholder ("pendiente" y "00000000" respectivamente) que el usuario completará en el paso siguiente. embedding queda en NULL. profile_completeness queda en 0. Registra en audit_logs. Cubre RF019–RF022.

get_next_step_url(worker_type: WorkerType) -> str: devuelve la URL del siguiente paso según el tipo: "/onboarding/primer-empleo/wizard" para PRIMER_EMPLEO, "/perfil/experiencia" para EXPERIENCIA, "/oficio/portfolio" para OFICIO.

app/api/v1/onboarding.py con prefijo /api/v1/onboarding y tag "Onboarding":

POST /api/v1/onboarding/detect-type — RF016–RF019
Requiere role=worker. Verifica que el usuario no tenga ya un registro en workers (si tiene, devuelve 409 con "El perfil ya fue creado"). Llama detect_worker_type y create_worker_profile. Devuelve OnboardingResponse con worker_type, worker_id, next_step y message motivador según el tipo detectado.

GET /api/v1/onboarding/status — RF020
Requiere role=worker. Busca el worker del usuario autenticado. Si no tiene perfil todavía devuelve OnboardingStatus con is_onboarded=False y worker_type=None. Si tiene perfil devuelve is_onboarded=True con el worker_type y profile_completeness actuales.

---

TAREA 8 — ENDPOINTS DE PERFIL BASE (app/api/v1/workers.py)

Router con prefijo /api/v1/workers y tag "Trabajadores". Todos los endpoints requieren role=worker.

GET /api/v1/workers/me — RF026
Busca el worker del usuario autenticado. Descifra full_name y phone con decrypt_field antes de construir la respuesta. NUNCA incluir el campo dni en ninguna respuesta. Devuelve WorkerProfileResponse. Si el usuario no tiene perfil devuelve 404.

PATCH /api/v1/workers/me — RF027–RF030
Recibe WorkerProfileUpdate (todos los campos opcionales). Para cada campo presente en el body, actualiza el registro. Si el campo es full_name o phone lo cifra antes de persistir. Tras la actualización recalcula profile_completeness según la lógica de completitud por tipo (ver abajo). Si worker_type es OFICIO y se cambia trade_category, actualiza también el campo trade_category en todos los service_listings activos del mismo worker. Registra en audit_logs. Devuelve WorkerProfileResponse.

Lógica de profile_completeness:
PRIMER_EMPLEO: +20 si district no es None, +40 si wizard_progress.current_step == 6, +40 si existe al menos un generated_cv. Máximo 100.
EXPERIENCIA: +20 si district, +20 si years_experience > 0, +30 si existe al menos una experiencia laboral (tabla a crear en Sprint 2, por ahora siempre 0), +30 si existe al menos un skill (idem). En Sprint 1 el máximo alcanzable es 40.
OFICIO: +20 si district, +20 si trade_category, +30 si existe al menos un portfolio_entry, +30 si is_available. En Sprint 1 el máximo alcanzable es 70.

GET /api/v1/workers/me/completeness — RF031
Calcula y devuelve CompletenessResponse con percentage (int 0–100), missing_fields (lista de strings descriptivos en español, ej. "Agrega tu distrito de residencia"), y next_action (string con la acción más importante a completar).

---

TAREA 9 — STUBS NLP Y DICCIONARIO LOCAL

app/utils/local_dict/huancayo_trades.json: crea el archivo con el diccionario completo del CLAUDE.md:

{
  "gasfitero": ["plomero", "fontanero", "instalador sanitario"],
  "techero": ["techadista", "instalador de techos", "techador"],
  "fierrero": ["soldador", "herrero", "metalurgista"],
  "albañil": ["constructor", "obrero de construcción", "operario civil"],
  "electricista": ["instalador eléctrico", "técnico eléctrico"],
  "pintor": ["aplicador de pintura", "pintor de obras"],
  "carpintero": ["ebanista", "trabajador de madera"],
  "mecánico": ["técnico automotriz", "mecánico automotriz"],
  "plomero": ["gasfitero"],
  "instalador": ["técnico de instalaciones"]
}

app/nlp/embeddings/generator.py: define MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2" y EMBEDDING_DIM = 384. Implementa apply_local_dictionary(text: str) -> str que carga el JSON, itera las claves y reemplaza apariciones en el texto (case-insensitive, palabras completas con regex \b). Implementa generate_embedding_async(text: str) -> list[float] como stub que devuelve [0.0] * EMBEDDING_DIM con un log estructurado que diga "embedding_stub_sprint1". Cubre RF056 parcialmente.

app/tasks/__init__.py: crea la instancia de Celery con app = Celery("intermediacion_laboral", broker=settings.REDIS_URL, backend=settings.REDIS_URL).

app/tasks/embeddings.py: tarea Celery generate_worker_embedding(worker_id: str) -> None que registra en structlog "embedding_task_queued" con worker_id y sprint="stub". No hace nada más. Cubre RF076 parcialmente.

app/tasks/notifications.py: tarea Celery send_reset_email(user_id: str, token: str) -> None que registra en structlog "reset_email_queued" con user_id. Stub para Sprint 1.

---

TAREA 10 — APLICACIÓN FASTAPI PRINCIPAL (app/main.py)

Crea la aplicación FastAPI con title="Sistema de Intermediación Laboral DRTPE-Junín", version="0.1.0", docs_url="/api/docs", redoc_url="/api/redoc".

Registra los tres routers: auth_router, onboarding_router, workers_router, todos con prefijo /api/v1.

Evento on startup: llama configure_logging() primero, luego init_db(), luego precarga el diccionario local Huancayo con apply_local_dictionary("") para que el JSON quede en memoria, y registra en structlog "app_started" con version y environment.

Evento on shutdown: cierra el engine de SQLAlchemy y registra "app_shutdown".

Middleware CORS con allow_origins=["http://localhost:5173"] en development o ["*"] en production (leer de settings.ENVIRONMENT), allow_credentials=True, allow_methods=["*"], allow_headers=["*"].

Middleware de timing: para cada request mide el tiempo total y agrega el header X-Process-Time con el valor en milisegundos.

Handler global de excepciones para Exception: en production devuelve JSON con status_code=500 y detail="Error interno del servidor" sin stack trace. En development puede incluir str(exc). Siempre registra el error en structlog con nivel error y exc_info=True.

Endpoint GET /api/v1/health sin autenticación que devuelve {"status": "ok", "version": "0.1.0", "sprint": 1, "environment": settings.ENVIRONMENT}.

---

TAREA 11 — TESTS

Configura pyproject.toml con:

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
source = ["app"]
omit = ["migrations/*", "tests/*"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "S"]
ignore = ["S101"]

Crea tests/conftest.py con fixtures async: engine de prueba con SQLite en memoria (para no requerir Postgres en CI), AsyncSession de prueba, AsyncClient de httpx apuntando a la app, y un fixture redis_mock que parchea get_redis() con fakeredis.aioredis.FakeRedis().

tests/unit/test_security.py:
test_hash_and_verify_password: verifica el round-trip bcrypt.
test_wrong_password_fails: verify_password devuelve False con contraseña incorrecta.
test_access_token_contains_sub_and_jti: el payload decodificado tiene sub y jti.
test_expired_token_raises_401: crea token con expires_delta negativo y verifica 401.
test_aes_encrypt_decrypt_roundtrip: encrypt_field seguido de decrypt_field devuelve el valor original.
test_aes_different_plaintexts_produce_different_ciphers: dos cifrados del mismo texto producen resultados distintos por el nonce aleatorio.
test_require_role_allows_correct_role: no lanza excepción.
test_require_role_blocks_wrong_role: lanza HTTPException 403.

tests/unit/test_onboarding_detector.py:
test_is_first_job_true_returns_primer_empleo.
test_trade_worker_true_returns_oficio.
test_neither_returns_experiencia.
test_oficio_without_trade_category_raises_value_error: verifica que OnboardingAnswers con is_trade_worker=True y trade_category=None lanza ValidationError de Pydantic.
test_worker_type_values_are_lowercase_strings.

tests/unit/test_local_dictionary.py:
test_gasfitero_normalized: apply_local_dictionary("necesito un gasfitero") contiene "plomero".
test_techero_normalized: "techero" se normaliza.
test_unknown_term_unchanged: "desarrollador" no cambia.
test_dictionary_loads_correctly: la función no lanza excepción y devuelve string.
test_case_insensitive: "GASFITERO" también se normaliza.

tests/integration/test_api_auth.py (con AsyncClient):
test_register_returns_tokens: POST /api/v1/auth/register con datos válidos devuelve 200 con access_token y refresh_token.
test_register_duplicate_email_returns_409.
test_login_valid_credentials_returns_tokens.
test_login_wrong_password_returns_401.
test_login_nonexistent_email_returns_401.
test_refresh_returns_new_tokens.
test_logout_returns_200.
test_protected_endpoint_without_token_returns_401: GET /api/v1/workers/me sin token devuelve 401.
test_health_endpoint_returns_ok: GET /api/v1/health devuelve status ok.

tests/integration/test_api_onboarding.py:
test_onboarding_primer_empleo: registrar usuario → login → POST detect-type con is_first_job=True → worker_type es primer_empleo.
test_onboarding_oficio_con_categoria: is_first_job=False, is_trade_worker=True, trade_category=Electricidad → worker_type es oficio.
test_onboarding_experiencia: is_first_job=False, is_trade_worker=False → worker_type es experiencia.
test_onboarding_sin_autenticacion_devuelve_401.
test_onboarding_duplicado_devuelve_409: llamar detect-type dos veces con el mismo usuario devuelve 409 la segunda vez.
test_onboarding_status_antes_de_onboarding: GET /api/v1/onboarding/status devuelve is_onboarded=False.
test_onboarding_status_despues_de_onboarding: is_onboarded=True con el worker_type correcto.

Ejecuta los tests al final con:
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80 -v

Si algún test falla, corrígelo antes de terminar. El sprint no está completo hasta que pytest pase con cobertura ≥ 80% y ruff check . no reporte errores.

---

CRITERIOS DE ACEPTACIÓN — OBLIGATORIOS ANTES DE TERMINAR

Verifica cada uno ejecutando el comando correspondiente y muéstrame la salida:

1. docker-compose config valida el archivo sin errores.
2. alembic upgrade head aplicado contra la BD de desarrollo crea todas las tablas y los índices HNSW.
3. POST /api/v1/auth/register devuelve access_token y refresh_token.
4. POST /api/v1/auth/login autentica y devuelve tokens.
5. POST /api/v1/onboarding/detect-type con los tres escenarios clasifica correctamente.
6. GET /api/v1/workers/me devuelve el perfil sin el campo dni.
7. pytest --cov=app --cov-fail-under=80 pasa.
8. ruff check . no reporta errores.
9. grep -r "print(" backend/app/ no devuelve resultados.
10. Los campos dni, full_name y phone en la tabla workers están almacenados como BYTEA cifrado, no en texto plano.

---

LO QUE NO DEBES IMPLEMENTAR EN ESTE SPRINT

No implementes el motor de matching ni embeddings reales (Sprint 2 y 3). No implementes el wizard de 6 pasos (Sprint 2). No implementes el portfolio ni el marketplace (Sprint 3). No instales Django, Flask ni MongoDB. No uses integers como PK. No escribas SQL con f-strings o concatenación de strings. No almacenes contraseñas, DNI ni tokens en texto plano en logs ni en la base de datos. No devuelvas stack traces en respuestas de producción. No modifiques las columnas embedding en este sprint, deben quedar en NULL.

Al abrir el PR, declara en la descripción qué RF cubre cada archivo nuevo o modificado.
