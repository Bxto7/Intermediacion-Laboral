# INFORME DE AUDITORÍA DE CALIDAD DE SOFTWARE
## Norma ISO/IEC 25010:2011 — Familia SQuaRE (ISO/IEC 25000)

---

| Campo | Detalle |
|---|---|
| **Sistema auditado** | Linku — Sistema de Intermediación Laboral DRTPE-Junín |
| **Versión** | 0.2.0 (Sprint 5 — Rediseño UI "Andino") |
| **Fecha de auditoría** | 2026-06-23 |
| **Auditor** | Análisis técnico asistido por Claude Code (Anthropic) |
| **Norma de referencia** | ISO/IEC 25010:2011 — SQuaRE Product Quality Model |
| **Alcance** | Backend (FastAPI/Python 3.11), Frontend (React 18/TypeScript 5), Infraestructura (Docker Compose), Base de datos (PostgreSQL 15 + pgvector), Colas async (Celery/Redis) |
| **Metodología** | Revisión estática de código fuente, análisis de arquitectura, revisión de configuraciones de despliegue, análisis de dependencias, revisión de pruebas automatizadas y documentación técnica (CLAUDE.md) |

---

## 1. RESUMEN EJECUTIVO

### 1.1 Nivel General de Calidad

El sistema Linku es un producto de intermediación laboral de **complejidad alta** que integra NLP, ML, generación de PDF, WebSockets, colas asíncronas y arquitectura de microservicios en contenedores. Se encuentra en **Sprint 5 de desarrollo activo** y exhibe una madurez técnica notable para un proyecto académico-institucional, con decisiones de diseño bien fundamentadas (JWT RS256, AES-256-GCM para PII, equidad en ranking, monitoreo con Prometheus/Grafana, análisis de calidad con SonarQube).

**Puntuación global estimada: 3.4 / 5.0 (68% de cumplimiento)**

### 1.2 Principales Fortalezas

- Arquitectura de seguridad robusta: JWT RS256, cifrado AES-256-GCM de PII, blacklist de tokens en Redis, rate limiting por IP
- Diseño modular y bien estructurado (separación de capas: API → Services → NLP → ML → Models)
- Infraestructura observable: Prometheus + Grafana + Flower + structlog
- Cobertura de pruebas amplia: 24 pruebas unitarias + 16 pruebas de integración identificadas
- Headers de seguridad HTTP (OWASP) implementados via middleware dedicado
- Mecanismo de equidad algorítmica (disparate impact + re-ranking) diferenciador
- Análisis de calidad continuo con SonarQube (Quality Gate OK al 2026-05-31)
- Frontend con code splitting, lazy loading y manejo explícito de estados loading/error

### 1.3 Principales Debilidades

- **`ml_score` es un stub fijo (0.5)**: el componente ML supervisado del matching no está operativo
- **Notificaciones por email/push son stubs**: ningún mensaje real llega al usuario
- **`/cv/download` es síncrono y bloqueante**: ejecuta WeasyPrint dentro del request HTTP
- **Sin refresh automático de access token**: un 401 en background fuerza el re-login
- **CV tipo `experiencia` no cablea datos parseados**: el PDF generado está siempre vacío de contenido
- **Credenciales por defecto en configuración**: contraseñas `postgres/postgres`, `AES_KEY` placeholder en dev, `changeme` en Grafana
- **SMTP no configurado**: ningún flujo de verificación de email ni recuperación de contraseña funciona realmente
- **Sin tests de frontend** (no hay suite de pruebas en `package.json`)
- **Nginx sin TLS**: la configuración sirve solo en HTTP puerto 80 sin HTTPS

---

## 2. TABLA DE EVALUACIÓN DETALLADA — ISO/IEC 25010

---

### CARACTERÍSTICA 1: ADECUACIÓN FUNCIONAL

> Grado en que el producto software proporciona funciones que satisfacen las necesidades declaradas e implícitas cuando es usado en condiciones especificadas.

| Subcaracterística | Evidencia encontrada | Nivel de cumplimiento | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|
| **Completitud funcional** | 17 routers REST declarados (`auth`, `onboarding`, `workers`, `employers`, `jobs`, `nlp`, `wizard`, `portfolio`, `cv`, `alerts`, `matching`, `marketplace`, `applications`, `contracts`, `surveys`, `ws_notifications`, `admin`). Flujo completo worker→onboarding→perfil→matching→postulación→admin implementado. | Alto | **4** | Toda la funcionalidad principal está presente. Se detectan 2 flujos incompletos: CV tipo `experiencia` (sin datos) y notificaciones (stubs). | Completar `_build_template_context` para el tipo `experiencia` cableando datos de `/nlp/parse-cv`. Implementar SMTP para notificaciones. |
| **Corrección funcional** | Matching produce resultados ordenados por `combined_score`. Generación de CV selecciona template por `worker_type`. Onboarding detecta tipo y redirige correctamente. SonarQube reporta Quality Gate OK, Fiabilidad C (3 bugs HTML `<title>` — ya corregidos según doc). | Medio-Alto | **3** | `ml_score` fijo en 0.5 distorsiona el ranking (no es un resultado "correcto" del modelo ML). Bug conocido `CV-EXP-VACIO` (BUG tabla: pendiente). Posible desajuste ruta NLP front vs back (`INT-NLP`). | Resolver `CV-EXP-VACIO`. Confirmar y corregir `INT-NLP`. Entrenar e integrar modelo ML supervisado. |
| **Pertinencia funcional** | El sistema implementa 3 tipos de trabajador diferenciados (primer empleo, oficio, experiencia) con flujos, templates de CV y pesos de matching distintos. Responde al contexto de informalidad laboral de Huancayo con diccionario local (`huancayo_trades.json`). Encuesta económica, marketplace de servicios y portafolio público alineados con necesidades DRTPE. | Alto | **4** | Las funciones implementadas son pertinentes al dominio. El diccionario local de oficios es una diferenciación de valor. | Documentar cobertura de requisitos funcionales (matriz RF vs endpoints) para evidencia de auditoría formal. |

**Promedio Adecuación Funcional: 3.67 / 5**

---

### CARACTERÍSTICA 2: EFICIENCIA DEL DESEMPEÑO

> Desempeño relativo a la cantidad de recursos utilizados bajo condiciones establecidas.

| Subcaracterística | Evidencia encontrada | Nivel de cumplimiento | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|
| **Comportamiento temporal** | Middleware `add_process_time` añade cabecera `X-Process-Time` a toda respuesta. Prometheus + Grafana para métricas de latencia. Celery separa workers por cola (embeddings=2, cv=2, notifications=4, reports=1). Vite con code splitting y lazy loading por ruta. Redis con política `allkeys-lru` y límite 256MB. | Medio | **3** | `/cv/download` ejecuta WeasyPrint síncronamente en el request HTTP → puede bloquear bajo carga. Carga del modelo sentence-transformers (384D) al inicio puede demorar el arranque. No se evidencian benchmarks ni SLOs definidos. | Mover generación de PDF al pipeline Celery y servir desde storage (ya existe `generate_cv_task`). Definir y documentar SLOs (p99 < X ms). Añadir health check de modelo NLP. |
| **Utilización de recursos** | Worker-embeddings limitado a 1G RAM, worker-cv a 512M. PostgreSQL con pgvector para búsqueda vectorial eficiente. Redis como broker y caché de blacklist. Índices implícitos en FK de SQLAlchemy. | Medio | **3** | No se evidencian índices explícitos en columnas de búsqueda frecuente (`worker_type`, `district`, `is_active`). No se evidencia configuración de pool de conexiones async (asyncpg default). Embeddings se regeneran con Celery Beat (02:00) pero no hay estrategia de caché de embeddings frecuentes. | Añadir índices compuestos en `job_offers(is_active, district, worker_type_target)` y `workers(worker_type, is_available)`. Configurar pool size en `create_async_engine`. |
| **Capacidad** | Stack diseñado para escalado horizontal (workers Celery independientes). Docker Compose con redes aisladas. Nginx como reverse proxy con `worker_processes auto`. pgvector soporta búsqueda ANN eficiente. | Medio-Alto | **4** | Sin evidencia de pruebas de carga o definición de usuarios concurrentes objetivo. Celery Beat corre en instancia única (SPOF). Staging compose existe (`docker-compose.staging.yml`) pero sin evidencia de pruebas de capacidad. | Ejecutar pruebas de carga con Locust o k6. Documentar capacidad objetivo (usuarios concurrentes, RPS). Considerar Celery Beat con RedBeat para HA. |

**Promedio Eficiencia del Desempeño: 3.33 / 5**

---

### CARACTERÍSTICA 3: COMPATIBILIDAD

> Grado en que el producto puede intercambiar información con otros productos y/o realizar sus funciones requeridas mientras comparte el mismo entorno.

| Subcaracterística | Evidencia encontrada | Nivel de cumplimiento | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|
| **Coexistencia** | Stack completamente dockerizado. Redes aisladas (`drtpe_net`). Puertos documentados sin colisiones (8000, 5173, 5433, 6379, 5555, 9090, 3001, 9000). SonarQube con BD dedicada (`sonar-db`). | Alto | **4** | El `docker-compose.yml` principal incluye SonarQube (BD separada, hostname fijo para resolver issue Elasticsearch en WSL/Docker). Coexistencia bien gestionada. | Separar SonarQube a un compose independiente en producción (es una herramienta de desarrollo, no un servicio de negocio). |
| **Interoperabilidad** | API REST con OpenAPI (Swagger en dev). WebSocket en `/ws/`. Prometheus metrics en `/metrics`. Conectores DRTPE en `integrations/drtpe/`. Axios con interceptores JWT estándar. Formato de respuesta JSON consistente con schemas Pydantic. | Medio-Alto | **4** | Integración DRTPE existe pero su estado real no pudo verificarse en detalle. Formato i18n solo `es-PE` (intencional). OpenAPI solo expuesto en `development` (seguro en prod). | Documentar contrato de integración con sistema DRTPE. Añadir versión en cabecera `API-Version`. |

**Promedio Compatibilidad: 4.0 / 5**

---

### CARACTERÍSTICA 4: USABILIDAD

> Grado en que el producto puede ser usado por usuarios específicos para conseguir metas específicas con efectividad, eficiencia y satisfacción en un contexto de uso especificado.

| Subcaracterística | Evidencia encontrada | Nivel de cumplimiento | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|
| **Capacidad para reconocer su adecuación** | Landing page dedicada (`LandingPage.tsx`). Flujo de onboarding con detección automática de tipo de trabajador (`/onboarding/detect-type`). Wizard de 6 pasos guiado (NLP-asistido) para primer empleo. Portfolio visual para oficios. | Alto | **4** | El contexto DRTPE exige UX para baja alfabetización digital. Hay wizard guiado y onboarding, que son las mejores prácticas para este perfil. No se puede verificar sin pruebas de usuario reales. | Realizar pruebas de usabilidad con trabajadores reales del área de Huancayo. Añadir tooltips explicativos y ejemplos dentro del wizard. |
| **Capacidad de aprendizaje** | Wizard paso a paso con NLP para extracción de habilidades. Formularios con validación Zod + react-hook-form con mensajes de error en español peruano. i18n `es-PE` único idioma. | Medio-Alto | **3** | No hay evidencia de documentación de usuario, tutoriales en la app ni ayuda contextual. Los mensajes de error técnicos del backend (ej. "422 Unprocessable Entity") podrían llegar al frontend. | Implementar mensajes de error amigables en el frontend para cada caso de error API. Añadir un tour/onboarding guiado (tooltips progresivos). |
| **Operabilidad** | Zustand persist para no perder progreso del wizard. `sessionStorage.login_return_url` para recuperar navegación post-login. Guards de rol (`AuthGuard`, `WorkerTypeGuard`, `AdminGuard`) evitan estados inválidos. Manejo explícito de `loading`/`error`/`data` requerido por convenciones. | Medio-Alto | **4** | Sin refresh automático de token: si la sesión expira durante el uso, el próximo 401 interrumpe al usuario abruptamente. | Implementar refresh automático de access token en interceptor Axios. Mostrar advertencia antes de expiración de sesión. |
| **Protección frente a errores de usuario** | Validación con Pydantic v2 en backend. Validación con Zod en frontend. Rate limiting evita abuso accidental. Wizard guarda progreso en localStorage. Confirmación requerida para acciones destructivas no evidenciada. | Medio | **3** | No se evidencia confirmación de acciones destructivas (borrar portfolio entry, cancelar postulación). No hay validación de tamaño/tipo de archivo en el frontend antes de subir CV. | Añadir diálogos de confirmación para acciones irreversibles. Validar tipo MIME y tamaño en el cliente antes de `upload`. |
| **Accesibilidad** | Paleta "Andino" con contrastes definidos (arcilla `#b8442a`, teal `#0f6e6e`). Componentes Radix UI (accesibles por defecto con ARIA). Tipografía Fraunces + Geist. | Medio | **3** | No se evidencian pruebas de contraste WCAG AA/AAA. No hay evidencia de navegación por teclado probada. No hay soporte para lectores de pantalla documentado. Población objetivo con posible baja visión o analfabetismo digital. | Verificar contraste de color con herramienta WCAG (apuntar a nivel AA mínimo). Realizar prueba con NVDA/VoiceOver. Considerar tamaños de fuente mínimos 16px para texto de cuerpo. |

**Promedio Usabilidad: 3.4 / 5**

---

### CARACTERÍSTICA 5: FIABILIDAD

> Grado en que el sistema, producto o componente realiza las funciones especificadas bajo condiciones especificadas durante un periodo de tiempo especificado.

| Subcaracterística | Evidencia encontrada | Nivel de cumplimiento | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|
| **Madurez** | 24 tests unitarios + 16 tests de integración. SonarQube Fiabilidad C (3 bugs `<title>` — corregidos). Fallback hash SHA256 si el modelo de embeddings no carga. Manejo de excepciones global en FastAPI. Lifespan pattern para inicialización ordenada. | Medio | **3** | No se evidencia cobertura de código medida actualmente (requiere generar `coverage.xml`). El score de Fiabilidad C en SonarQube (aunque los bugs se corrigieron) indica deuda técnica. `ml_score` stub no afecta fiabilidad pero sí correctitud. | Integrar generación de `coverage.xml` en CI. Apuntar a cobertura ≥ 70% en paths críticos. Añadir tests para flujos de error (DB down, Redis down, modelo NLP no disponible). |
| **Disponibilidad** | Healthchecks en todos los servicios Docker (db, redis, api con `curl`). `depends_on` con condición `service_healthy`. Celery workers independientes (fallo de un worker no tumba la API). Redis con persistencia `redis_data` volume. PostgreSQL con `postgres_data` volume. | Medio-Alto | **4** | Celery Beat corre en instancia única (SPOF para tareas programadas). No hay configuración de restart policy (`restart: always` ausente en `docker-compose.yml`). Sin evidencia de backup automatizado de PostgreSQL. | Añadir `restart: unless-stopped` a servicios críticos (api, db, redis). Implementar backup periódico de PostgreSQL (pg_dump en Celery Beat). Documentar RTO/RPO objetivo. |
| **Tolerancia a fallos** | Fallback en embeddings (SHA256 hash). Global exception handler en FastAPI evita exposición de stack traces en producción. `try/except ImportError` para Prometheus (carga opcional). Jinja2 con `autoescape=True` para seguridad en templates. | Medio-Alto | **4** | No se evidencia circuit breaker para llamadas externas (DRTPE, GCS). Si Redis no está disponible, rate limiting y blacklist de tokens fallan sin degradación elegante. | Añadir manejo de `ConnectionError` con degradación elegante cuando Redis no está disponible. Implementar retry con backoff exponencial para llamadas externas. |
| **Recuperabilidad** | Alembic para migraciones versionadas de BD. Volúmenes Docker para persistencia de datos. Tokens refresh de 7 días permiten recuperación de sesión. | Medio | **3** | No se evidencia procedimiento documentado de recuperación ante desastre (DR). Las claves RSA se auto-generan si no existen (pero se perderían en un nuevo contenedor sin volume). | Persistir claves RSA en volume Docker o secretos gestionados. Documentar procedimiento de recuperación. Implementar backup automatizado. |

**Promedio Fiabilidad: 3.5 / 5**

---

### CARACTERÍSTICA 6: SEGURIDAD

> Grado en que el producto protege la información y los datos para que personas u otros sistemas tengan el grado de acceso a datos adecuado a sus tipos y niveles de autorización.

| Subcaracterística | Evidencia encontrada | Nivel de cumplimiento | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|
| **Confidencialidad** | AES-256-GCM para cifrado de PII (full_name, DNI, phone) almacenado como BYTEA. JWT RS256 con par de claves RSA 2048-bit. Tokens no exponen password_hash. Docs OpenAPI solo en `development`. Validación de `AES_KEY` ≠ placeholder en producción. | Alto | **5** | Implementación de cifrado de PII es correcta y robusta (nonce aleatorio de 12 bytes por operación). Validación de entorno en `config.py` previene uso del placeholder en producción. **Fortaleza destacada.** | Documentar política de rotación de `AES_KEY`. Considerar HSM o secretos gestionados (AWS Secrets Manager, Vault) para producción. |
| **Integridad** | Bcrypt cost 12 para passwords. JTI en JWT con blacklist Redis (logout real). JWT incluye `type` claim (access/refresh). SQLAlchemy parametrizado (protección SQL injection). Pydantic v2 valida todos los inputs. `python-magic` presente para validación de tipo de archivo. | Alto | **4** | Se detectó hotspot de seguridad en `portfolio.py:320` (directorio escribible — SONAR-2, pendiente). No se evidencia validación de tamaño máximo de archivo en todos los endpoints de upload. | Revisar y corregir `SONAR-2` en `portfolio.py:320`. Añadir límite de tamaño explícito en endpoints de upload (actualmente `client_max_body_size 20M` solo en Nginx). |
| **No repudio** | `AuditLog` model con registro de acciones. structlog para logging estructurado. `jti` único por token permite rastreo. | Medio-Alto | **4** | El `AuditLog` existe pero no se verificó cobertura completa de eventos auditables (qué acciones se registran). | Definir y documentar política de auditoría: qué eventos se registran (login, logout, postulación, generación de CV, cambio de rol). |
| **Responsabilidad** | Blacklist de tokens por `jti` y por `user_id` (permite invalidar todos los tokens de un usuario). `require_role` valida rol en cada endpoint protegido. Separación de roles (WORKER, EMPLOYER, ADMIN, MODERATOR). | Alto | **4** | Verificación de autorización correcta: endpoints de CV verifican `worker.user_id == token.sub`. Sin evidencia de RBAC granular (permisos por recurso individual más allá del rol). | Implementar scopes o permisos granulares para el rol MODERATOR (actualmente indefinido funcionalmente). |
| **Autenticidad** | RS256 garantiza autenticidad del servidor. HTTPBearer en todos los endpoints protegidos. Rate limiting en auth endpoints (register 10/h, login 20/h, forgot 5/h). `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy` implementados. HSTS en producción. | Alto | **4** | No hay MFA (autenticación multifactor). CSRF no aplica (API stateless con Bearer token), pero confirmarlo en documentación. Headers `Content-Security-Policy` (CSP) **no implementados** — es la defensa más importante contra XSS en aplicaciones web. | Implementar `Content-Security-Policy` en `SecurityHeadersMiddleware`. Evaluar TOTP para cuentas ADMIN. Documentar modelo de amenazas. |
| **Resistencia** | slowapi para rate limiting. Redis con `allkeys-lru` evita agotamiento de memoria. Nginx con `client_max_body_size 20M`. Workers Celery aislados evitan que una tarea lenta bloquee otras. | Medio | **3** | Nginx sirve en HTTP (port 80) sin TLS — vulnerable a ataques MITM. Sin evidencia de WAF. Sin evidencia de protección contra enumeración de usuarios en `/register` (respuesta 409 revela si email existe). | Configurar TLS en Nginx (Let's Encrypt / certificado institucional). Implementar respuesta genérica en `/register` para no revelar si el email existe. |

**Promedio Seguridad: 4.0 / 5**

---

### CARACTERÍSTICA 7: MANTENIBILIDAD

> Grado de efectividad y eficiencia con el que el producto puede ser modificado para mejorarlo, corregirlo o adaptarlo a cambios en el entorno y en los requisitos.

| Subcaracterística | Evidencia encontrada | Nivel de cumplimiento | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|
| **Modularidad** | Separación clara en capas: `api/v1/` → `services/` → `nlp/` → `ml/` → `models/`. Frontend con módulos por tipo de trabajador (`primer-empleo/`, `oficio/`, `experiencia/`). Celery workers por cola. Router agregador en `api/v1/router.py`. CLAUDE.md como fuente única de verdad. | Alto | **4** | Buena separación de responsabilidades. Algunos routers son largos (auth.py tiene lógica de negocio dentro). Dependencias circulares potenciales no verificadas. | Mover lógica de negocio de auth a un `services/auth_service.py`. Usar herramienta como `pydeps` para detectar dependencias circulares. |
| **Reusabilidad** | `require_role` como decorador reutilizable. `check_rate_limit` como función reutilizable. Schemas Pydantic compartidos (`schemas/common.py` con enums). `LinkuLogo` como componente reutilizable. Guards de React reutilizables. Módulo de seguridad centralizado. | Alto | **4** | Buena reutilización de componentes transversales. El módulo `security.py` centraliza toda la lógica de auth. | Crear un `shared/` de componentes backend (similar al frontend) para utilitarios comunes. |
| **Analizabilidad** | structlog con logging estructurado JSON. Prometheus + Grafana para observabilidad. Flower para monitoreo de Celery. `X-Process-Time` header en cada respuesta. SonarQube integrado. Referencias a RFs en comentarios del código (ej. `# RF: RF001-RF012`). | Alto | **5** | La observabilidad es un punto fuerte significativo. El sistema de referenciado a RFs en el código facilita la trazabilidad de requisitos. **Fortaleza destacada.** | Integrar correlación de request IDs en structlog para trazar requests entre servicios. |
| **Modificabilidad** | Alembic para migraciones sin downtime. Variables de entorno en `config.py` (Pydantic Settings). `TEMPLATE_MAP` y `SCORE_WEIGHTS` como configuración explícita (fácil de cambiar). Docker Compose como orquestador de fácil modificación. | Alto | **4** | Los pesos de matching (`SCORE_WEIGHTS`) están hardcodeados en el código — un cambio requiere redeploy. `AES_KEY` por defecto en código fuente (aunque validado). | Mover `SCORE_WEIGHTS` a configuración (env o tabla en BD) para ajustar sin redeploy. Usar CI/CD para automatizar el proceso de cambio. |
| **Capacidad de ser probado** | `pytest` con `pytest-asyncio`. `fakeredis` para mocking de Redis. `aiosqlite` para BD de prueba. Separación unit/integration. `conftest.py` para fixtures. `pytest-cov` para cobertura. | Medio-Alto | **4** | No se evidencia cobertura de código actual medida. Sin tests de frontend (no hay Vitest/Jest en `package.json`). Algunos stubs (notificaciones, ml_score) dificultan probar el comportamiento real. | Añadir Vitest al frontend con tests de componentes clave (LoginPage, WizardStep, MatchesPage). Medir y publicar cobertura actual. |

**Promedio Mantenibilidad: 4.2 / 5**

---

### CARACTERÍSTICA 8: PORTABILIDAD

> Grado de efectividad y eficiencia con que el sistema puede ser transferido de un entorno hardware, software u operacional a otro.

| Subcaracterística | Evidencia encontrada | Nivel de cumplimiento | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|
| **Adaptabilidad** | Docker + Docker Compose completo (backend, frontend, db, redis, workers, monitoring). `docker-compose.staging.yml` existe. `Dockerfile` con imagen fija `python:3.11-slim-bookworm` y repositorios HTTPS (adaptación para redes con puerto 80 bloqueado). Variables de entorno externalizadas. Frontend configurable via `VITE_API_URL`. | Alto | **4** | Dependencia de WeasyPrint en libs del SO (libpango, libcairo, libgdk-pixbuf) puede romper en imágenes base distintas. La adaptación de repos HTTPS en el Dockerfile muestra capacidad de resolver problemas de entorno. | Documentar los requisitos exactos del SO para WeasyPrint. Considerar imagen base con todas las dependencias pre-instaladas. |
| **Instalabilidad** | Stack completo desplegable con `docker-compose up -d --build`. `scripts/init.sql` para inicialización de BD. Auto-generación de claves RSA al inicio. | Medio-Alto | **4** | No hay evidencia de script de instalación automatizado (setup wizard). Las claves RSA se generan en tiempo de ejecución pero no se persisten en volume → se pierden al recrear el contenedor. El `backend/.env` no existe (requiere creación manual). | Crear script `setup.sh` que genere `.env` con valores seguros. Montar `backend/keys/` como volume Docker. Añadir documentación de instalación en `README.md`. |
| **Reemplazabilidad** | API REST estándar (no acoplada a vendor). Axios configurable (`VITE_API_URL`). PostgreSQL estándar + pgvector (extension open source). Redis estándar. Celery soporta múltiples brokers. sentence-transformers con modelo configurable (`EMBEDDING_MODEL` env var). | Alto | **5** | Alta independencia de vendor. Ningún componente propietario en el stack de producción. El modelo NLP es configurable via env var. **Fortaleza destacada.** | Documentar el proceso de migración de broker (Redis → RabbitMQ) y de BD si fuera necesario. |

**Promedio Portabilidad: 4.33 / 5**

---

## 3. TABLA RESUMEN DE CALIFICACIONES

| # | Característica ISO 25010 | Calificación Promedio | Nivel |
|---|---|---|---|
| 1 | Adecuación Funcional | 3.67 / 5.0 | Bueno |
| 2 | Eficiencia del Desempeño | 3.33 / 5.0 | Aceptable-Bueno |
| 3 | Compatibilidad | 4.00 / 5.0 | Bueno |
| 4 | Usabilidad | 3.40 / 5.0 | Aceptable-Bueno |
| 5 | Fiabilidad | 3.50 / 5.0 | Aceptable-Bueno |
| 6 | Seguridad | 4.00 / 5.0 | Bueno |
| 7 | Mantenibilidad | 4.20 / 5.0 | Bueno |
| 8 | Portabilidad | 4.33 / 5.0 | Bueno |
| | **PROMEDIO GLOBAL** | **3.80 / 5.0** | **Bueno** |
| | **% CUMPLIMIENTO ESTIMADO** | **76%** | — |

> **Nota metodológica:** La puntuación por subcaracterística fue ponderada linealmente. En una auditoría formal ISO/IEC 25040, los pesos deberían definirse con el cliente según criticidad del dominio.

---

## 4. NO CONFORMIDADES IDENTIFICADAS

### No Conformidades Mayores (Bloqueantes para producción)

| ID | Descripción | Característica afectada | Referencia en código |
|---|---|---|---|
| NC-01 | Nginx sin TLS/HTTPS — datos en tránsito no cifrados | Seguridad (Resistencia) | `nginx/nginx.conf:22` |
| NC-02 | SMTP no configurado — flujos de verificación de email y recuperación de contraseña no funcionan | Adecuación Funcional, Fiabilidad | `tasks/notifications.py:9-11` |
| NC-03 | CV tipo `experiencia` genera PDF vacío de contenido (bug CV-EXP-VACIO) | Adecuación Funcional (Corrección) | `services/cv_builder/pdf_generator.py:152-168` |
| NC-04 | `ml_score` fijo en 0.5 — el sistema de matching no usa un modelo ML real | Adecuación Funcional (Corrección) | `api/v1/matching.py` |
| NC-05 | Claves RSA auto-generadas sin volume persistente — se pierden al recrear contenedor | Fiabilidad (Recuperabilidad), Seguridad | `docker-compose.yml`, `core/security.py:33-57` |

### No Conformidades Menores (Observaciones)

| ID | Descripción | Característica afectada |
|---|---|---|
| NC-06 | `Content-Security-Policy` (CSP) ausente en headers de seguridad | Seguridad (Autenticidad) |
| NC-07 | Sin refresh automático de access token (24h de vida, pero 401 desloguea abruptamente) | Usabilidad (Operabilidad), Fiabilidad |
| NC-08 | Posible desajuste ruta/payload NLP front vs back (`INT-NLP`) | Adecuación Funcional |
| NC-09 | Sin tests de frontend (no hay Vitest/Jest) | Mantenibilidad (Capacidad de ser probado) |
| NC-10 | `restart: unless-stopped` ausente en servicios críticos de `docker-compose.yml` | Fiabilidad (Disponibilidad) |
| NC-11 | Hotspot de seguridad en `portfolio.py:320` (SONAR-2) sin resolver | Seguridad (Integridad) |
| NC-12 | Sin pruebas de accesibilidad WCAG — crítico para público objetivo (baja alfabetización digital) | Usabilidad (Accesibilidad) |
| NC-13 | Endpoint `/register` revela si email ya existe (409) — enumeración de usuarios | Seguridad |
| NC-14 | Grafana con contraseña por defecto `changeme` en `docker-compose.yml` | Seguridad |
| NC-15 | `/cv/download` síncrono y bloqueante en el request HTTP | Eficiencia del Desempeño |

---

## 5. RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Impacto | Nivel | Mitigación recomendada |
|---|---|---|---|---|
| Fuga de PII por transmisión sin TLS (NC-01) | Alta (en despliegue real) | Crítico | **CRÍTICO** | Configurar TLS en Nginx antes de cualquier despliegue a usuarios reales |
| Pérdida de claves RSA al recrear contenedor (NC-05) | Media | Alto | **ALTO** | Volume Docker para `backend/keys/` |
| Timeout/error en generación de CV bajo carga (NC-15) | Media | Alto | **ALTO** | Migrar a generación async con Celery + servir desde storage |
| Usuarios sin notificaciones reales (NC-02) | Alta | Medio | **ALTO** | Configurar SMTP (SendGrid, SES o servidor institucional) |
| Ranking de empleo sesgado por `ml_score` stub (NC-04) | Alta | Medio | **MEDIO** | Entrenar modelo o documentar limitación explícitamente al usuario |
| Enumeración de usuarios via `/register` (NC-13) | Media | Medio | **MEDIO** | Respuesta genérica de registro |
| XSS por ausencia de CSP (NC-06) | Baja | Alto | **MEDIO** | Implementar CSP estricto |

---

## 6. PRIORIZACIÓN DE ACCIONES CORRECTIVAS

### Prioridad 1 — CRÍTICA (antes de despliegue a usuarios reales)

1. **Configurar TLS en Nginx** (NC-01) — Protege toda la comunicación
2. **Configurar SMTP real** (NC-02) — Habilita flujos de verificación y recuperación
3. **Persistir claves RSA en volume** (NC-05) — Evita invalidar todas las sesiones en redeploy
4. **Corregir CV-EXP-VACIO** (NC-03) — El CV de `experiencia` es un producto clave

### Prioridad 2 — ALTA (Sprint 6)

5. **Implementar CSP en SecurityHeadersMiddleware** (NC-06)
6. **Migrar `/cv/download` a async** (NC-15)
7. **Implementar refresh automático de token** (NC-07)
8. **Añadir `restart: unless-stopped`** (NC-10)
9. **Resolver hotspot SONAR-2** (NC-11)
10. **Verificar y corregir INT-NLP** (NC-08)

### Prioridad 3 — MEDIA (Sprint 7+)

11. **Añadir tests de frontend** (NC-09)
12. **Pruebas de accesibilidad WCAG** (NC-12)
13. **Respuesta genérica en `/register`** (NC-13)
14. **Cambiar contraseña Grafana en staging/prod** (NC-14)
15. **Entrenar e integrar modelo ML supervisado** (NC-04)

---

## 7. EVIDENCIAS ADICIONALES NECESARIAS PARA AUDITORÍA FORMAL

Para completar una auditoría formal ISO/IEC 25040, se requieren las siguientes evidencias que no pudieron verificarse en esta revisión:

1. **Reporte de cobertura de código** (`backend/coverage.xml` generado con `pytest --cov`)
2. **Resultados de pruebas de carga** (herramienta como Locust o k6)
3. **Reporte completo SonarQube** (último análisis con todas las métricas)
4. **Capturas de pantalla / grabaciones de la aplicación en funcionamiento**
5. **Matriz de trazabilidad de requisitos** (RF → endpoint → test)
6. **Resultados de pruebas de accesibilidad WCAG** (herramienta como axe-core o Lighthouse)
7. **Pruebas de usuario** con trabajadores del público objetivo (DRTPE-Junín)
8. **Documentación de arquitectura** (diagrama C4 o similar)
9. **Política de seguridad y modelo de amenazas** documentados
10. **Evidencia de análisis estático del frontend** (ESLint report)

---

## 8. CONCLUSIÓN FINAL

### ¿Está el software preparado para una auditoría formal?

**Parcialmente.** El sistema Linku demuestra un nivel de madurez técnica superior al promedio para un proyecto académico-institucional, con decisiones de arquitectura sólidas, seguridad bien implementada en la capa de autenticación/cifrado, y un stack de observabilidad completo. Sin embargo, existen **5 no conformidades mayores** (NC-01 a NC-05) que deben resolverse antes de cualquier auditoría formal o despliegue a usuarios reales.

### Aspectos que requieren mejora antes de certificación o evaluación externa

1. Resolver todas las no conformidades mayores (NC-01 a NC-05)
2. Alcanzar cobertura de pruebas ≥ 70% con reporte generado
3. Implementar tests de frontend
4. Obtener reporte formal de SonarQube con Quality Gate OK en todos los aspectos
5. Realizar pruebas de usabilidad y accesibilidad documentadas
6. Completar documentación de arquitectura y modelo de amenazas
7. Configurar y probar el stack de staging con datos reales (anonimizados)

### Porcentaje estimado de cumplimiento con ISO/IEC 25010

> **76% de cumplimiento estimado** *(basado en promedio ponderado de subcaracterísticas evaluadas sobre evidencia disponible)*

Este porcentaje podría elevarse a **85%+** tras resolver las no conformidades de prioridad 1 y 2, y obtener las evidencias adicionales solicitadas.

---

## 9. RADAR DE CALIDAD

```
                    ADECUACIÓN FUNCIONAL
                         3.67
                          ▲
                          │
  PORTABILIDAD     ───────┼─────── EFICIENCIA
      4.33                │          3.33
        ╲                 │         ╱
         ╲                │        ╱
          ╲               │       ╱
MANTENIBILIDAD ──────────┼─────── COMPATIBILIDAD
      4.20                │          4.00
          ╱               │       ╲
         ╱                │        ╲
        ╱                 │         ╲
  SEGURIDAD        ───────┼─────── FIABILIDAD
      4.00                │          3.50
                          │
                          ▼
                       USABILIDAD
                         3.40
```

---

*Informe generado el 2026-06-23 | Auditoría técnica de código fuente y configuración*
*Norma de referencia: ISO/IEC 25010:2011 — Systems and software Quality Requirements and Evaluation (SQuaRE)*
*Este informe es de naturaleza técnica y no reemplaza una certificación formal por un organismo acreditado.*
