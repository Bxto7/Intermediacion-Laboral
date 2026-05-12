Lee el archivo CLAUDE.md en la raíz del repositorio antes de escribir cualquier línea de código. Es la fuente de verdad de arquitectura, convenciones y prohibiciones. Si algo de este prompt contradice el CLAUDE.md, el CLAUDE.md tiene prioridad.

Para todo el trabajo de backend usa la herramienta Bash. Con ella crea archivos, ejecuta migraciones, instala dependencias y corre los tests. No uses ninguna otra herramienta para el backend.

---

Estás en el Sprint 2 del sistema de intermediación laboral ML/NLP articulado con la DRTPE-Junín. El Sprint 1 entregó la base funcional: estructura de carpetas, Docker, autenticación JWT, onboarding de detección de tipo de usuario y los modelos de base de datos. Este sprint tiene dos ejes: primero cerrar las vulnerabilidades de seguridad identificadas por el security-auditor en el Sprint 1, y segundo implementar el motor NLP real con embeddings semánticos, la extracción de habilidades diferenciada por tipo de usuario y el pipeline completo de construcción de perfil vectorial.

Los RF cubiertos en este sprint son RF036–RF075 (M03 Empleadores y Ofertas, M04 NLP de Competencias) más los RNF pendientes de seguridad.

---

BLOQUE 0 — DEUDA DE SEGURIDAD DEL SPRINT 1 (hacer primero, antes que cualquier feature)

Estos issues fueron identificados por el security-auditor y deben quedar resueltos antes de avanzar al bloque de NLP. Son obligatorios.

ISSUE 1 — CRÍTICO: Rotación de clave AES
El .env tiene el placeholder "cambia-esto-exactamente-32-bytes!!" como AES_KEY. Implementa un script backend/scripts/rotate_aes_key.py que:
- Genera una nueva clave AES-256 aleatoria con os.urandom(32) y la codifica en base64 para almacenamiento seguro.
- Re-cifra todos los registros BYTEA existentes en workers (full_name, dni, phone) y employers (ruc, contact_name, phone) usando la clave vieja y la nueva.
- Opera en una transacción: si falla cualquier re-cifrado, hace rollback completo.
- Registra en audit_logs con action="aes_key_rotated" el conteo de registros migrados.
- Al final imprime con structlog (nunca print) la nueva clave en base64 para que el administrador la copie al .env.
Modifica app/core/security.py para que encrypt_field y decrypt_field lean AES_KEY desde settings y acepten que el valor en .env sea base64 (decode antes de usar). Agrega el validator en Settings que verifique que al decodificar base64 el resultado sea exactamente 32 bytes. Cubre RNF001, RNF002.

ISSUE 2 — ALTO: Reset de contraseña no invalida JTIs activos
En app/api/v1/auth.py, el endpoint POST /api/v1/auth/reset-password actualmente guarda "blacklist:user:{user_id}" en Redis pero verify_token no consulta esa clave. Corrige el flujo completo:
- En verify_token, después de verificar la blacklist por JTI individual, también consulta si existe la clave "blacklist:user:{user_id}" (donde user_id viene del campo sub del payload). Si existe, lanzar HTTPException 401 con detail "Sesión invalidada, vuelve a iniciar sesión".
- El TTL de "blacklist:user:{user_id}" debe ser igual al REFRESH_TOKEN_EXPIRE_DAYS convertido a segundos (el período más largo posible de un token activo).
- Agrega test unitario test_reset_password_invalidates_all_sessions en tests/unit/test_security.py. Cubre RNF001, RNF003.

ISSUE 3 — ALTO: Rate limiting usa IP del proxy en lugar del cliente real
En Cloud Run y ECS la IP real llega en el header X-Forwarded-For. Crea app/core/rate_limit.py con:
- Función get_client_ip(request: Request) -> str que lee X-Forwarded-For si ENVIRONMENT=production, tomando solo el primer IP de la lista (el más a la izquierda es el cliente real). En development usa request.client.host directamente.
- Función check_rate_limit(key: str, limit: int, window_seconds: int, redis) -> None que usa el patrón sliding window con Redis (INCR + EXPIRE). Si supera el límite lanza HTTPException 429 con header Retry-After calculado.
- Reemplaza todos los rate limits hardcodeados en auth.py por llamadas a check_rate_limit usando get_client_ip. Cubre RNF007, RNF008.

ISSUE 4 — MEDIO: Endpoints sin schemas Pydantic explícitos
Los endpoints POST /auth/forgot-password, POST /auth/verify-email y POST /auth/reset-password reciben campos sueltos sin schema. Define en app/schemas/auth.py:
- ForgotPasswordRequest con email (EmailStr).
- VerifyEmailRequest con token (str, min_length=32, max_length=128).
- ResetPasswordRequest con token (str, min_length=32, max_length=128) y new_password (str, min_length=8, max_length=128).
Actualiza los tres endpoints para que reciban estos schemas. Cubre RNF004.

ISSUE 5 — MEDIO: Sin rate limiting en forgot-password
Agrega rate limit de 5 intentos por hora por IP al endpoint POST /auth/forgot-password usando check_rate_limit con clave "rl:forgot:{ip}". Cubre RNF007.

---

BLOQUE 1 — MÓDULO DE EMPLEADORES Y OFERTAS (M03 / RF036–RF055)

Antes de implementar el matching necesitas que existan ofertas de trabajo en el sistema. Este bloque crea el módulo completo de empleadores.

TAREA 1 — Modelos nuevos

Crea una migración Alembic nueva (nunca modifiques 0001_initial_schema.py) llamada 0002_job_offers.py con estas tablas:

Tabla job_offers:
id UUID PK, employer_id UUID FK→employers.id NOT NULL, title VARCHAR(200) NOT NULL, description TEXT NOT NULL, required_skills JSONB DEFAULT '[]' (habilidades requeridas en formato estructurado), preferred_skills JSONB DEFAULT '[]', district VARCHAR(50), modality VARCHAR(20) con CHECK IN ('presencial','remoto','híbrido'), salary_min DECIMAL(10,2), salary_max DECIMAL(10,2), worker_type_target VARCHAR(20) con CHECK IN ('primer_empleo','experiencia','oficio','cualquiera') DEFAULT 'cualquiera', is_active BOOLEAN DEFAULT true, expires_at TIMESTAMPTZ, embedding vector(384), views_count INTEGER DEFAULT 0, applications_count INTEGER DEFAULT 0, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now(). Índice HNSW sobre embedding con los mismos parámetros que las otras tablas (m=16, ef_construction=64). Cubre RF036–RF042.

Tabla applications:
id UUID PK, worker_id UUID FK→workers.id NOT NULL, job_offer_id UUID FK→job_offers.id NOT NULL, status VARCHAR(20) NOT NULL con CHECK IN ('enviada','en_revision','entrevista','descartada','contratada') DEFAULT 'enviada', match_score DECIMAL(5,4), cover_note TEXT, employer_notes TEXT (solo visible para empleadores), applied_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now(). Índice único sobre (worker_id, job_offer_id) para evitar postulaciones duplicadas. Cubre RF043–RF050.

Tabla search_logs (para KPI Índice de Visibilidad de Perfil):
id UUID PK, searcher_id UUID FK→users.id nullable, query_text TEXT, query_embedding vector(384), results_count INTEGER, worker_type_filter VARCHAR(20), district_filter VARCHAR(50), created_at TIMESTAMPTZ DEFAULT now(). Esta tabla es de solo inserción, nunca actualizar ni borrar. Cubre RF111–RF115 (base para reportes).

TAREA 2 — Schemas de empleadores y ofertas

En app/schemas/employer.py:
EmployerProfileCreate con company_name (str, min 2, max 255), ruc (str, exactamente 11 dígitos numéricos validado con regex), contact_name (str, min 2, max 100), phone (str, formato +51 9XXXXXXXX), district (District), sector (str, max 100).
EmployerProfileResponse con id, company_name, district, sector, is_verified, created_at. Sin ruc ni contact_name en respuesta pública.
EmployerProfileUpdate todos los campos opcionales excepto ruc.

En app/schemas/job_offer.py:
JobOfferCreate con title (str, min 5, max 200), description (str, min 50, max 5000), required_skills (list[str], max 20 items), preferred_skills (list[str] default []), district (District | None), modality (Literal['presencial','remoto','híbrido']), salary_min (Decimal | None, ge=0), salary_max (Decimal | None, ge=0), worker_type_target (WorkerType | Literal['cualquiera'] default 'cualquiera'), expires_at (datetime | None). Validator de modelo: si salary_min y salary_max ambos presentes, salary_max debe ser mayor que salary_min.
JobOfferResponse con todos los campos más employer_name (str), applications_count (int), days_until_expiry (int | None).
JobOfferUpdate todos los campos opcionales.
ApplicationCreate con job_offer_id (UUID), cover_note (str | None, max 500).
ApplicationResponse con id, job_offer_id, worker_id, status, match_score, applied_at, job_title (str).

TAREA 3 — Endpoints de empleadores

Crea app/api/v1/employers.py con prefijo /api/v1/employers y tag "Empleadores".

POST /api/v1/employers/profile — RF036–RF038
Requiere role=employer. Verifica que no exista ya un perfil para este user_id (409 si existe). Cifra ruc y contact_name con encrypt_field. Crea registro en employers. Devuelve EmployerProfileResponse.

GET /api/v1/employers/profile — RF039
Requiere role=employer. Descifra contact_name antes de responder. Nunca devolver ruc en ninguna respuesta.

PATCH /api/v1/employers/profile — RF040
Requiere role=employer. Cifra campos sensibles si se actualizan. Registra en audit_logs.

POST /api/v1/employers/jobs — RF041–RF043
Requiere role=employer. Recibe JobOfferCreate. Crea la oferta en job_offers con is_active=True y embedding=NULL (el embedding se genera en background por Celery). Encola tarea Celery generate_job_embedding(job_offer_id). Devuelve JobOfferResponse con 201.

GET /api/v1/employers/jobs — RF044
Requiere role=employer. Lista todas las ofertas del empleador con paginación (limit/offset, default limit=20, max=100). Devuelve list[JobOfferResponse].

PATCH /api/v1/employers/jobs/{job_id} — RF045
Requiere role=employer. Verifica que la oferta pertenezca al empleador autenticado (403 si no). Actualiza campos. Si cambia description o required_skills, re-encola generate_job_embedding. Devuelve JobOfferResponse.

DELETE /api/v1/employers/jobs/{job_id} — RF046
Requiere role=employer. No borrar físicamente: poner is_active=False y expires_at=now(). Registra en audit_logs. Devuelve MessageResponse.

GET /api/v1/employers/jobs/{job_id}/applications — RF047–RF049
Requiere role=employer. Lista postulaciones de una oferta con status, match_score y datos básicos del trabajador (nombre descifrado, district, worker_type). Sin exponer DNI. Paginación igual que la anterior.

PATCH /api/v1/employers/jobs/{job_id}/applications/{app_id}/status — RF050
Requiere role=employer. Actualiza status de la postulación (solo puede avanzar en el flujo: enviada→en_revision→entrevista→(contratada|descartada)). Si status pasa a 'contratada', encola tarea Celery notify_worker_hired(worker_id, job_offer_id). Devuelve ApplicationResponse.

TAREA 4 — Endpoints de postulación (para trabajadores)

En app/api/v1/workers.py agrega:

POST /api/v1/workers/apply — RF051–RF053
Requiere role=worker. Recibe ApplicationCreate. Verifica que la oferta exista y esté activa (404/400 si no). Verifica que el trabajador no haya postulado ya (409 si existe). Verifica que el trabajador tenga profile_completeness >= 40 (400 con mensaje "Completa tu perfil antes de postular"). Crea registro en applications con match_score=NULL (se calculará en el motor ML del Sprint 3). Registra en search_logs. Encola tarea Celery notify_employer_new_application. Devuelve ApplicationResponse.

GET /api/v1/workers/applications — RF054
Requiere role=worker. Lista las postulaciones del trabajador con estado, nombre de la oferta y empleador. Sin exponer datos de otros trabajadores. Paginación estándar.

GET /api/v1/jobs/feed — RF055
Sin autenticación obligatoria (pública, pero si hay token se personaliza). Lista ofertas activas no expiradas ordenadas por created_at DESC. Filtros opcionales por query param: district, modality, worker_type_target, salary_min, salary_max. Paginación estándar. Registra en search_logs. Devuelve list[JobOfferResponse].

---

BLOQUE 2 — MOTOR NLP REAL (M04 / RF056–RF075)

Aquí se reemplazan todos los stubs del Sprint 1 por implementaciones reales. Este es el núcleo técnico del sprint.

TAREA 5 — Pipeline NLP base (todos los tipos)

Implementa app/nlp/embeddings/generator.py con la implementación real. Ya no es stub.

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

Instancia el modelo con SentenceTransformer(MODEL_NAME) en un singleton cargado una sola vez al arrancar la aplicación (en el evento startup de main.py). Nunca reinstanciar por request.

generate_embedding(text: str) -> list[float]: versión síncrona para uso en Celery workers. Llama a model.encode([text], normalize_embeddings=True)[0].tolist().

generate_embedding_async(text: str) -> list[float]: versión async que usa asyncio.get_event_loop().run_in_executor(None, generate_embedding, text) para no bloquear el event loop de FastAPI.

generate_embeddings_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]: para procesamiento masivo con model.encode(texts, batch_size=batch_size, normalize_embeddings=True).tolist(). Usar en tareas de re-indexado.

apply_local_dictionary(text: str) -> str: versión real (ya no stub). Carga huancayo_trades.json una sola vez con un módulo-level cache. Aplica reemplazos con regex \b{term}\b (case-insensitive) para cada entrada del diccionario, reemplazando por el primer sinónimo de la lista. Retorna el texto normalizado.

normalize_text(text: str) -> str: pipeline completo de normalización:
1. text.lower()
2. ftfy.fix_text(text) para corregir encoding
3. re.sub para eliminar caracteres especiales (conservar letras, números, espacios, acentos españoles)
4. apply_local_dictionary(text)
5. Eliminar stopwords en español con NLTK (cargar corpus 'stopwords' si no está descargado)
6. Retornar texto limpio

Cubre RF056–RF058.

TAREA 6 — Pipeline PRIMER_EMPLEO: extracción de habilidades desde lenguaje coloquial

Implementa app/nlp/skill_extractor/first_job_extractor.py:

Carga el modelo spaCy es_core_news_md una sola vez como singleton. Define un conjunto SOFT_SKILLS_KEYWORDS con al menos 40 términos coloquiales peruanos mapeados a habilidades estándar:

soft_skills_map = {
    "puntual": "puntualidad",
    "responsable": "responsabilidad",
    "trabajo en equipo": "trabajo colaborativo",
    "trabajador": "disposición al trabajo",
    "honesto": "integridad",
    "aprendo rápido": "aprendizaje rápido",
    "me adapto": "adaptabilidad",
    "me llevo bien con todos": "habilidades interpersonales",
    "soy ordenado": "organización",
    "tengo iniciativa": "proactividad",
    "ayudo en casa": "gestión doméstica",
    "cuido a mis hermanos": "cuidado de personas",
    "vendo en el mercado": "ventas informales",
    "manejo caja": "manejo de efectivo",
    "atiendo clientes": "atención al cliente",
    "reparto": "logística de entrega",
    "cocino": "preparación de alimentos",
    "computadora": "manejo de computadora",
    "excel": "Microsoft Excel",
    "internet": "navegación web",
    # agrega hasta 40 total
}

extract_skills_from_wizard_answer(text: str, step: int) -> list[str]: recibe la respuesta del usuario en un paso del wizard y retorna lista de habilidades estandarizadas. Aplica normalize_text primero, luego busca coincidencias en soft_skills_map (fuzzy: si el término aparece como subcadena de al menos 4 chars), luego pasa por spaCy NER para detectar MISC y PER que puedan indicar habilidades adicionales. Devuelve lista deduplicada. Cubre RF059–RF062.

suggest_job_sectors(skills: list[str]) -> list[str]: dado un perfil de habilidades, retorna hasta 5 sectores laborales compatibles. Define un diccionario estático sector_skills_map que mapea sectores (Comercio, Gastronomía, Construcción, Tecnología, Cuidado de personas, Manufactura, Transporte, Servicios) a listas de skills relacionadas. Calcula un score de coincidencia por sector y retorna los top-5 ordenados. Cubre RF063.

build_first_job_profile_text(district: str, skills: list[str], interests: list[str], education_level: str) -> str: construye el texto de perfil para embedding:
return f"primer empleo | {district} | educación: {education_level} | habilidades: {', '.join(skills)} | intereses: {', '.join(interests)}"
Cubre RF064.

TAREA 7 — Pipeline EXPERIENCIA: parser de CV subido

Implementa app/nlp/cv_parser/parser.py:

Instancia un pipeline spaCy con es_core_news_md para extracción de entidades.

parse_pdf(file_content: bytes) -> str: extrae texto crudo del PDF con PyPDF2.PdfReader. Si el texto extraído es menor a 100 caracteres (PDF escaneado sin texto), registra en structlog un warning "pdf_no_text_extracted" y retorna string vacío. Nunca lanzar excepción por PDF mal formado: capturar y loguear.

parse_docx(file_content: bytes) -> str: extrae texto con python_docx.Document, concatenando párrafos con saltos de línea.

extract_cv_fields(raw_text: str) -> ParsedCVResult: extrae los siguientes campos usando combinación de regex y spaCy NER. Define umbrales de confianza por campo:

- full_name: buscar entidades PER de spaCy en las primeras 5 líneas. Confianza = 0.85 si hay exactamente una entidad PER, 0.5 si hay varias.
- email: regex estándar de email. Confianza = 0.99 si encuentra exactamente uno.
- phone: regex para formato peruano (+51 9XXXXXXXX o 9XXXXXXXX). Confianza = 0.95.
- education: buscar keywords (universidad, instituto, colegio, bachiller, licenciado, técnico) + nombre de institución con NER ORG. Confianza = 0.80 si encuentra keyword + ORG.
- work_experiences: buscar bloques con años (regex \d{4}) + nombres de empresa (NER ORG). Confianza = 0.70.
- skills: buscar lista después de keywords (habilidades, competencias, skills, manejo de). Confianza = 0.75.

El schema ParsedCVResult en app/schemas/cv.py debe tener: full_name (str|None), full_name_confidence (float), email (str|None), email_confidence (float), phone (str|None), phone_confidence (float), education (list[dict]), education_confidence (float), work_experiences (list[dict]), work_experiences_confidence (float), skills (list[str]), skills_confidence (float), raw_text_length (int), parse_warnings (list[str]).

Regla: solo prellenar un campo en el frontend si su confianza >= 0.75. Para los campos con confianza < 0.75 devolver None y agregar un string descriptivo a parse_warnings. Cubre RF066–RF070.

TAREA 8 — Pipeline OFICIO: extracción desde descripciones de trabajos

Implementa app/nlp/portfolio_nlp/trade_extractor.py:

Carga es_core_news_md como singleton compartido.

Define TRADE_SKILLS_MAP: diccionario que mapea cada TradeCategory a sus habilidades técnicas típicas con al menos 15 skills por categoría. Ejemplo para ELECTRICIDAD: ["instalación eléctrica residencial", "cableado estructurado", "tableros eléctricos", "tomacorrientes", "interruptores", "medición con multímetro", "lectura de planos eléctricos", "instalación de luminarias", "puesta a tierra", "norma EM.010", ...]. Define al menos para ELECTRICIDAD, GASFITERIA, CARPINTERIA, ALBANILERIA y PINTURA. Para el resto usar lista genérica de ["habilidad técnica manual", "trabajo en obra", "herramientas de oficio"].

extract_skills_from_job_description(description: str, trade_category: TradeCategory) -> JobSkillExtraction:
1. Aplica normalize_text y apply_local_dictionary.
2. Pasa por spaCy para extraer tokens y chunks relevantes.
3. Busca coincidencias con el TRADE_SKILLS_MAP de la categoría (fuzzy matching: token overlap >= 0.6).
4. Agrega habilidades genéricas de la categoría que aparezcan en el texto.
5. Deduplica y ordena por frecuencia de aparición.
6. Estima nivel: si description tiene >= 200 palabras y >= 8 skills → "avanzado"; >= 5 skills → "intermedio"; resto → "básico".
Devuelve JobSkillExtraction con skills (list[str]), estimated_level (str), confidence (float calculado como len(skills_found)/max_expected_skills). Cubre RF071–RF074.

build_trade_profile_text(trade_category: str, years_experience: int, district: str, avg_rating: float, portfolio_skills: list[str], portfolio_count: int) -> str:
return f"{trade_category} | {years_experience} años | {district} | {avg_rating:.1f}/5.0 | trabajos: {portfolio_count} | habilidades: {', '.join(portfolio_skills)}"
Cubre RF075.

TAREA 9 — Generación de embeddings para ofertas y perfiles (Celery real)

Reemplaza los stubs de app/tasks/embeddings.py con implementaciones reales:

generate_worker_embedding(worker_id: str) -> None:
- Abre sesión de BD con SQLAlchemy síncrono (los workers Celery no son async).
- Carga el worker por ID.
- Según worker_type construye el texto de perfil llamando a la función build_*_profile_text correspondiente al tipo.
- Para PRIMER_EMPLEO: carga wizard_progress.extracted_skills y wizard_progress.answers para extraer intereses y educación.
- Para OFICIO: carga todas las portfolio_entries activas y consolida sus extracted_skills.
- Para EXPERIENCIA: usa el bio y job_title del perfil (campos a agregar en la migración).
- Genera embedding con generate_embedding(profile_text).
- Actualiza workers.embedding con el vector generado.
- Registra en structlog "worker_embedding_generated" con worker_id, worker_type, profile_text_length. Cubre RF076, RF077.

generate_job_embedding(job_offer_id: str) -> None:
- Carga la oferta por ID.
- Construye texto: f"{offer.title} | {offer.modality} | {offer.district} | skills requeridas: {', '.join(offer.required_skills)} | {offer.description[:500]}"
- Aplica normalize_text y generate_embedding.
- Actualiza job_offers.embedding.
- Registra en structlog "job_embedding_generated". Cubre RF078.

regenerate_all_embeddings(worker_type: str = "all") -> None:
- Tarea masiva para re-indexado. Carga todos los workers del tipo especificado en batches de 50.
- Para cada batch, construye los textos de perfil y llama generate_embeddings_batch.
- Actualiza los embeddings en BD en una sola transacción por batch.
- Registra progreso cada 100 workers. Cubre RF079.

TAREA 10 — Endpoints NLP expuestos al frontend

Crea app/api/v1/nlp.py con prefijo /api/v1/nlp y tag "NLP".

POST /api/v1/nlp/extract-skills/wizard — RF059–RF062
Requiere role=worker con worker_type=primer_empleo (validar en el servicio, no en el decorator). Recibe {"step": int, "text": str}. Llama extract_skills_from_wizard_answer. Devuelve {"skills": list[str], "suggested_sectors": list[str]}. Rate limit: 60 requests/minuto por usuario. Cubre RF060.

POST /api/v1/nlp/parse-cv — RF066–RF070
Requiere role=worker con worker_type=experiencia. Recibe archivo multipart (PDF o DOCX, máximo 10 MB). Valida tipo MIME: solo application/pdf y application/vnd.openxmlformats-officedocument.wordprocessingml.document. Llama al parser correspondiente. Devuelve ParsedCVResult. Si raw_text_length < 100 devuelve 422 con mensaje "No se pudo extraer texto del archivo. Intenta con un PDF que no sea escaneado, o ingresa tu información manualmente." Cubre RF067.

POST /api/v1/nlp/extract-skills/portfolio — RF071–RF074
Requiere role=worker con worker_type=oficio. Recibe {"description": str, "trade_category": str}. Llama extract_skills_from_job_description. Devuelve JobSkillExtraction como dict. Rate limit: 30 requests/minuto por usuario. Cubre RF072.

POST /api/v1/nlp/worker/{worker_id}/regenerate-embedding — RF076–RF078
Requiere role=admin. Encola tarea Celery generate_worker_embedding(worker_id). Devuelve {"queued": true, "worker_id": worker_id}. Para uso del panel DRTPE-Junín.

GET /api/v1/nlp/worker/{worker_id}/embedding-status — RF079
Requiere role=admin o el propio worker. Verifica si el worker tiene embedding != NULL en BD. Devuelve {"has_embedding": bool, "profile_completeness": int, "last_updated": datetime|None}.

---

BLOQUE 3 — WIZARD PRIMER_EMPLEO: PERSISTENCIA DE PASOS (M06 / RF096–RF100)

El wizard de 6 pasos existe en BD (tabla wizard_progress del Sprint 1) pero no tiene endpoints. Impleméntalos ahora que el NLP está listo.

TAREA 11 — Servicio y endpoints del wizard

Crea app/services/cv_builder/wizard_service.py:

get_or_create_wizard(worker_id: UUID, db: AsyncSession) -> WizardProgress: busca el registro en wizard_progress. Si no existe, lo crea con current_step=1 y answers={}.

save_wizard_step(worker_id: UUID, step: int, step_data: dict, db: AsyncSession) -> WizardProgress:
- Valida que step esté entre 1 y 6.
- Valida que step sea <= current_step + 1 (no saltar pasos).
- Si step == 3 (habilidades blandas): llama extract_skills_from_wizard_answer con el texto de step_data["text"] y acumula en wizard_progress.extracted_skills.
- Si step == 4 (actividades previas): igual, acumula más skills.
- Actualiza answers[str(step)] con step_data.
- Actualiza current_step = max(current_step, step).
- Actualiza last_saved_at.
- Si current_step == 6: encola generate_worker_embedding(worker_id) para generar el embedding final.
- Devuelve el wizard_progress actualizado.

get_wizard_summary(worker_id: UUID, db: AsyncSession) -> dict: para el paso 6 (preview). Retorna {"full_name": str, "district": str, "education": dict, "skills": list[str], "interests": list[str], "suggested_sectors": list[str]}.

Define el schema WizardStepRequest en app/schemas/wizard.py con step (int, ge=1, le=6) y data (dict). Define WizardStepResponse con current_step (int), is_complete (bool), extracted_skills (list[str]), next_step_hint (str).

Crea app/api/v1/wizard.py con prefijo /api/v1/wizard y tag "Wizard":

GET /api/v1/wizard/progress — RF096
Requiere role=worker con worker_type=primer_empleo. Devuelve el estado actual del wizard (paso actual, respuestas guardadas, skills extraídas).

POST /api/v1/wizard/step — RF097–RF099
Requiere role=worker con worker_type=primer_empleo. Recibe WizardStepRequest. Llama save_wizard_step. Si current_step llega a 6 actualiza profile_completeness del worker a 80. Devuelve WizardStepResponse.

GET /api/v1/wizard/summary — RF100
Requiere role=worker con worker_type=primer_empleo. Solo disponible si current_step == 6. Devuelve get_wizard_summary. Si el wizard no está completo devuelve 400.

---

BLOQUE 4 — PORTFOLIO OFICIO: CRUD + NLP AUTOMÁTICO (RF056–RF065 aplicados)

TAREA 12 — Endpoints de portfolio

Crea app/api/v1/portfolio.py con prefijo /api/v1/portfolio y tag "Portfolio".

Define en app/schemas/portfolio.py:
PortfolioEntryCreate con title (str, min 3, max 200), description (str, min 20, max 2000), period_start (date | None), period_end (date | None), client_rating (float | None, ge=1.0, le=5.0), is_public (bool, default True).
PortfolioEntryResponse con todos los campos más extracted_skills (list[str]).
PortfolioEntryUpdate todos opcionales.

POST /api/v1/portfolio/entries — RF056–RF058
Requiere role=worker con worker_type=oficio (validar). Recibe PortfolioEntryCreate. Extrae trade_category del perfil del worker. Llama extract_skills_from_job_description(description, trade_category) y guarda en extracted_skills. Crea el registro en portfolio_entries con embedding=NULL. Encola generate_portfolio_entry_embedding(entry_id) y generate_worker_embedding(worker_id). Actualiza avg_rating del worker si client_rating fue provisto (recalcular promedio de todos los ratings). Devuelve PortfolioEntryResponse con 201. Cubre RF057.

GET /api/v1/portfolio/entries — RF059
Requiere role=worker. Lista todas las entradas del portfolio del trabajador autenticado ordenadas por period_end DESC. Paginación estándar.

GET /api/v1/portfolio/{username} — RF060
Endpoint público (sin autenticación). Busca el worker por su slug/username público. Devuelve solo las entradas con is_public=True más los datos básicos del perfil (nombre, oficio, district, avg_rating, is_available). NUNCA exponer DNI, teléfono ni user_id internos. Si el worker no existe o no es tipo OFICIO devuelve 404.

PATCH /api/v1/portfolio/entries/{entry_id} — RF061
Requiere role=worker. Verifica que la entrada pertenezca al trabajador autenticado. Si cambia description, re-extrae skills y re-encola embedding. Devuelve PortfolioEntryResponse.

DELETE /api/v1/portfolio/entries/{entry_id} — RF062
Requiere role=worker. Borra físicamente (las entradas del portfolio sí se pueden eliminar). Recalcula avg_rating del worker. Encola regenerar embedding. Devuelve 204.

POST /api/v1/portfolio/entries/{entry_id}/photos — RF063
Requiere role=worker. Recibe hasta 5 fotos en multipart. Valida MIME (JPEG/PNG/WEBP únicamente), tamaño máximo 5 MB cada una. Simula subida a GCS/S3: en development guarda en disco local en /tmp/portfolio_photos/{entry_id}/ y devuelve URL ficticia "http://localhost:8000/static/{entry_id}/{filename}". En production usar cliente GCS/S3 real (dejar el stub documentado con un TODO claro). Actualiza portfolio_entries.photos. Devuelve lista de URLs. Cubre RF064.

Agrega también la tarea Celery generate_portfolio_entry_embedding(entry_id: str) en app/tasks/embeddings.py:
- Carga la entrada del portfolio.
- Construye texto: f"{entry.title} | habilidades: {', '.join(entry.extracted_skills)} | {entry.description[:300]}"
- Genera embedding y actualiza portfolio_entries.embedding. Cubre RF065.

---

BLOQUE 5 — MIGRACIÓN Y CAMPOS FALTANTES

TAREA 13 — Migración 0003_worker_profile_fields.py

El modelo de workers necesita campos adicionales que el Sprint 1 no contempló para soportar el NLP de EXPERIENCIA y el wizard de PRIMER_EMPLEO. Crea esta migración con las siguientes columnas nuevas en la tabla workers:

bio TEXT (resumen profesional libre, para EXPERIENCIA)
job_title VARCHAR(100) (cargo actual o buscado, para EXPERIENCIA)
username VARCHAR(50) UNIQUE (slug público para portfolio OFICIO, generado automáticamente desde full_name al crear el perfil)
education_level VARCHAR(50) (para PRIMER_EMPLEO: 'primaria','secundaria','tecnico','universitario','ninguno')

Y en wizard_progress:
job_interests JSONB DEFAULT '[]' (sectores de interés, paso 5 del wizard)

Agrega el campo username al WorkerProfileResponse y al WorkerProfileUpdate. Genera el username automáticamente en create_worker_profile del onboarding service usando slugify(full_name) + sufijo numérico si hay colisión.

---

BLOQUE 6 — TESTS DEL SPRINT 2

TAREA 14 — Tests unitarios e integración

Todos los tests nuevos se agregan a los archivos existentes o en archivos nuevos en tests/unit/ y tests/integration/. La cobertura total (Sprint 1 + Sprint 2) debe mantenerse >= 80%.

tests/unit/test_nlp_first_job.py:
test_extract_skills_puntual: "soy muy puntual" → "puntualidad" en resultado.
test_extract_skills_informal_experience: "ayudo a mi papá en su carpintería" → incluye habilidad relacionada con madera.
test_suggest_sectors_from_skills: skills de cocina → "Gastronomía" en top sectores.
test_normalize_text_removes_stopwords: "el trabajo en la empresa" → no contiene "el", "en", "la".
test_apply_local_dictionary_gasfitero: "gasfitero" → "plomero" en el texto.
test_apply_local_dictionary_case_insensitive: "GASFITERO" también se normaliza.
test_build_first_job_profile_text: verifica que el texto incluye district y skills.

tests/unit/test_nlp_cv_parser.py:
test_parse_pdf_returns_string: con un PDF de prueba (crear bytes mínimos válidos con reportlab o fixtures).
test_extract_email_from_text: texto con email → campo email en ParsedCVResult con confianza >= 0.99.
test_extract_phone_peruvian_format: "+51 987654321" → campo phone con confianza >= 0.95.
test_low_confidence_field_is_none: campo con confianza < 0.75 devuelve None.
test_empty_pdf_returns_warnings: PDF con < 100 chars → parse_warnings no vacío.

tests/unit/test_nlp_trade_portfolio.py:
test_extract_skills_electricidad: descripción con "cableado" y "tablero" → skills relevantes de electricidad.
test_extract_skills_gasfiteria: descripción con "cañería" y "baño" → skills de gasfitería.
test_estimated_level_avanzado: descripción larga con muchas skills → nivel "avanzado".
test_estimated_level_basico: descripción corta → nivel "básico".
test_build_trade_profile_text_format: verifica que incluye trade_category, años y district.

tests/unit/test_embeddings.py:
test_generate_embedding_returns_384_dims: generate_embedding("texto de prueba") devuelve lista de 384 floats.
test_normalize_embeddings_unit_length: la norma L2 del embedding debe ser aproximadamente 1.0 (normalized_embeddings=True).
test_generate_embeddings_batch_consistent: batch de 2 textos devuelve 2 embeddings de 384 dims cada uno.
test_local_dict_cache_loaded_once: apply_local_dictionary llamado 3 veces solo carga el JSON una vez (mockear open).

tests/unit/test_security_sprint2.py (agregar al archivo existente):
test_reset_password_blocks_all_sessions: después de reset, verify_token con token anterior lanza 401.
test_get_client_ip_from_forwarded_for: en production mode, X-Forwarded-For="1.2.3.4, 10.0.0.1" devuelve "1.2.3.4".
test_rate_limit_blocks_after_threshold: después de N+1 llamadas, check_rate_limit lanza 429.
test_forgot_password_schema_validates_email: ForgotPasswordRequest con "no-es-email" lanza ValidationError.

tests/integration/test_api_employers.py:
test_create_employer_profile_returns_200.
test_create_duplicate_employer_returns_409.
test_ruc_never_in_response: verificar que la respuesta no contiene el campo ruc.
test_create_job_offer_queues_embedding_task: mockear Celery, verificar que se encola generate_job_embedding.
test_deactivate_job_offer_returns_200.

tests/integration/test_api_nlp.py:
test_extract_skills_wizard_requires_primer_empleo_type: worker tipo EXPERIENCIA recibe 403.
test_parse_cv_requires_experiencia_type: worker tipo PRIMER_EMPLEO recibe 403.
test_parse_cv_validates_mime_type: archivo .txt devuelve 422.
test_extract_portfolio_skills_returns_skills_list.

tests/integration/test_api_portfolio.py:
test_create_portfolio_entry_extracts_skills: la respuesta incluye extracted_skills no vacío.
test_portfolio_public_endpoint_no_auth_required.
test_portfolio_public_hides_dni.
test_delete_entry_returns_204.
test_oficio_worker_type_required: worker EXPERIENCIA recibe 403 al intentar crear entrada de portfolio.

tests/integration/test_api_wizard.py:
test_wizard_step_1_saves_progress.
test_wizard_step_3_extracts_skills.
test_wizard_cannot_skip_steps: intentar ir directo al paso 4 sin haber completado 3 devuelve 400.
test_wizard_summary_requires_step_6_complete.
test_wizard_requires_primer_empleo_type.

Ejecuta al terminar:
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80 -v
ruff check . && ruff format --check .

Si algún test falla, corrígelo antes de terminar.

---

CRITERIOS DE ACEPTACIÓN — OBLIGATORIOS ANTES DE TERMINAR

Ejecuta cada uno y muéstrame la salida:

1. python backend/scripts/rotate_aes_key.py imprime la nueva clave en base64 sin errores.
2. verify_token con token de usuario cuya contraseña fue reseteada lanza HTTPException 401.
3. check_rate_limit lanza 429 después de superar el límite con IP real (no de proxy).
4. alembic upgrade head aplica las migraciones 0002 y 0003 sin error.
5. POST /api/v1/nlp/extract-skills/wizard con texto coloquial peruano devuelve al menos 2 skills.
6. POST /api/v1/nlp/parse-cv con un PDF de texto devuelve ParsedCVResult con al menos email o full_name extraído.
7. POST /api/v1/portfolio/entries crea una entrada con extracted_skills no vacío.
8. POST /api/v1/wizard/step con step=3 y texto de habilidades actualiza extracted_skills en BD.
9. GET /api/v1/portfolio/{username} funciona sin token y no expone DNI.
10. pytest --cov=app --cov-fail-under=80 pasa.
11. ruff check . sin errores.
12. grep -r "print(" backend/app/ no devuelve resultados.

---

LO QUE NO DEBES IMPLEMENTAR EN ESTE SPRINT

No implementes el motor de matching ni el score combinado (Sprint 3). No implementes el marketplace de servicios (Sprint 3). No implementes los reportes del panel DRTPE-Junín (Sprint 4). No implementes la subida real a GCS/S3 (dejar stub documentado con TODO para Sprint 4). No modifiques migraciones ya aplicadas (0001_initial_schema.py). No uses integers como PK. No escribas SQL con f-strings. No almacenes DNI en texto plano. No devuelvas stack traces en producción.

Al abrir el PR, declara en la descripción qué RF cubre cada archivo nuevo o modificado.

---

ORDEN DE EJECUCIÓN DE AGENTES RECOMENDADO

1. security-auditor → cierra el Bloque 0 primero (deuda de seguridad).
2. python-pro → implementa Bloques 1, 2, 3 y 4 (empleadores, NLP, wizard, portfolio).
3. ml-engineer → revisa y optimiza los pipelines NLP del Bloque 2 (embeddings, extracción de skills, normalización).
4. devops-engineer → genera y aplica las migraciones 0002 y 0003, verifica docker-compose sigue funcionando.
5. python-pro → escribe y corre todos los tests del Bloque 6.
6. api-documenter → actualiza la documentación OpenAPI de los nuevos endpoints.
