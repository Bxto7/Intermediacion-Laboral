# Informe de Auditoría de Seguridad — OWASP Top 10 (2021)

> Proyecto: **Linku — Sistema de Intermediación Laboral DRTPE-Junín**
> Tipo: Auditoría estática de seguridad, **solo lectura**, basada estrictamente en evidencia del código.
> Fecha: 2026-06-13 · Rama auditada: `AUDITORIAS`
> Auditor: Agente 4 — Auditor de Seguridad Senior (OWASP Top 10).
> Alcance: Backend (FastAPI), Frontend (React/TS), APIs y flujos de auth/authz, configuración de infraestructura (Docker Compose), dependencias de terceros.

> **Nota metodológica:** Cada hallazgo cita archivo y línea. Donde el código contradijo una sospecha inicial (p. ej. autorización del panel admin, SSRF), se documenta como **Seguro** tras verificación, evitando falsos positivos. No se proponen ni escriben correcciones de código.

---

## Resumen por categoría

| # | Categoría OWASP | Estado | Severidad |
|---|-----------------|--------|-----------|
| A01 | Broken Access Control | Seguro / Sin hallazgos | — |
| A02 | Cryptographic Failures | Vulnerable | Medio |
| A03 | Injection | Seguro (con observación menor) | Bajo |
| A04 | Insecure Design | Vulnerable | Medio |
| A05 | Security Misconfiguration | Vulnerable | Medio |
| A06 | Vulnerable and Outdated Components | Vulnerable | **Alto** |
| A07 | Identification and Authentication Failures | Vulnerable | Medio |
| A08 | Software and Data Integrity Failures | Vulnerable | Medio |
| A09 | Security Logging and Monitoring Failures | Vulnerable | Medio |
| A10 | Server-Side Request Forgery (SSRF) | Seguro / Sin hallazgos | — |

---

## A01 — Broken Access Control

* **Categoría OWASP:** A01:2021 - Broken Access Control
* **Estado:** **Seguro / Sin hallazgos significativos**
* **Evidencia (verificada):**
  * El panel administrativo impone autorización **a nivel de router**, no solo por endpoint: [`admin/__init__.py:6-10`](backend/app/api/v1/admin/__init__.py#L6) → `APIRouter(prefix="/admin", dependencies=[Depends(require_role(UserRole.ADMIN))])`. Todos los endpoints `/admin/*` quedan protegidos aunque el handler individual no declare la dependencia.
  * Control de acceso a nivel de objeto (anti-IDOR) en CV: [`cv.py:46`](backend/app/api/v1/cv.py#L46) y [`cv.py:73`](backend/app/api/v1/cv.py#L73) verifican `str(worker.user_id) != token_user_id` → 403. Un trabajador no puede generar/descargar el CV de otro.
  * El WebSocket valida propiedad del recurso: [`ws_notifications.py:36`](backend/app/api/v1/ws_notifications.py#L36) compara `token_user_id != str(user_id)` y cierra la conexión.
  * `require_role` valida pertenencia de rol contra el claim del JWT: [`security.py:152-169`](backend/app/core/security.py#L152).
* **Observación menor (defensa en profundidad):** los chequeos de propiedad de objeto son manuales y repetidos por endpoint; no existe una política/decorador centralizado. Es correcto hoy, pero un endpoint nuevo podría omitir el chequeo por descuido. Recomendable un patrón de autorización a nivel de objeto reutilizable.

---

## A02 — Cryptographic Failures

* **Categoría OWASP:** A02:2021 - Cryptographic Failures
* **Estado:** **Vulnerable**
* **Evidencia:**
  1. **Tokens en `localStorage`:** [`client.ts:13`](frontend/src/api/client.ts#L13) y [`client.ts:40-41`](frontend/src/api/client.ts#L40) guardan `access_token`/`refresh_token` en `localStorage`. Cualquier XSS en la SPA permite exfiltrarlos (no son `HttpOnly`).
  2. **Clave AES por defecto embebida en el código fuente:** [`config.py:12`](backend/app/core/config.py#L12) y [`config.py:30`](backend/app/core/config.py#L30) (`_DEFAULT_AES_KEY_B64`). *Mitigado parcialmente:* el validador [`config.py:58`](backend/app/core/config.py#L58) rechaza el placeholder si `ENVIRONMENT == production`. Riesgo real solo si se opera sin fijar `AES_KEY`.
  3. **Token JWT transportado en query string del WebSocket:** [`ws_notifications.py:19`](backend/app/api/v1/ws_notifications.py#L19) (`?token=...`). Las URLs suelen quedar en logs de proxy/servidor → riesgo de fuga del token.
  4. **Access token de larga vida:** `ACCESS_TOKEN_EXPIRE_MINUTES=1440` (24 h) en [`config.py:28`](backend/app/core/config.py#L28). Amplía la ventana de uso si el token es robado, agravado por (1) y por la ausencia de refresh automático.
  5. **Clave privada RSA en disco sin cifrar:** [`security.py:46`](backend/app/core/security.py#L46) usa `NoEncryption()` al serializar el PEM. Aceptable si los secretos del contenedor están protegidos, pero es un secreto en reposo sin envoltura.
* **Fortalezas confirmadas:** JWT **RS256** (asimétrico), cifrado de PII con **AES-256-GCM** y **nonce aleatorio de 12 bytes** ([`security.py:80-91`](backend/app/core/security.py#L80)), `bcrypt` con `cost=12` ([`security.py:72`](backend/app/core/security.py#L72)).
* **Impacto:** Medio — robo de sesión vía XSS y exposición de tokens; el cifrado de datos en reposo en sí es robusto.
* **Probabilidad:** Media — depende de la existencia de un XSS o de acceso a logs/disco.
* **Severidad:** **Medio**
* **Control mitigante sugerido:** tokens en cookies `HttpOnly`/`Secure`/`SameSite`; gestión de secretos fuera del código (vault/secret manager); reducir TTL del access token con rotación de refresh; transportar el token del WS por header/subprotocolo en lugar de query string.

---

## A03 — Injection

* **Categoría OWASP:** A03:2021 - Injection
* **Estado:** **Seguro / Sin hallazgos explotables** (con observación menor)
* **Evidencia (verificada):**
  * Acceso a datos vía ORM SQLAlchemy 2.x con parámetros vinculados. Donde se usa SQL crudo `text()`, los valores de usuario van como *bind params*: `:wid` en [`surveys.py:47-56`](backend/app/api/v1/surveys.py#L47), `:wtype` en [`dataset_builder.py:48`](backend/app/ml/matching_engine/dataset_builder.py#L48), `:tc`/`:av`/`:limit`/`:offset` en [`marketplace_service.py:200-204`](backend/app/services/marketplace/marketplace_service.py#L200).
  * Los dos usos de `text(f"...")` no interpolan strings de usuario: en [`dataset_builder.py:29-31`](backend/app/ml/matching_engine/dataset_builder.py#L29) el fragmento `where_type` es un literal fijo del propio código; el valor real va por `:wtype`.
  * No se hallaron `os.system`, `subprocess`, `eval` ni concatenación de comandos.
* **Observación menor (defensa en profundidad):** en [`marketplace_service.py:173-182`](backend/app/services/marketplace/marketplace_service.py#L173) el vector de embedding se concatena como string dentro del SQL (`'{embedding_str}'::vector`). El contenido son **floats generados por el modelo**, no input directo del usuario, por lo que el riesgo de inyección es bajo; aun así no está parametrizado. Conviene pasarlo como parámetro para robustez.
* **Severidad:** **Bajo**
* **Control mitigante sugerido:** parametrizar también el literal del vector (no concatenar) como principio uniforme de *prepared statements*.

---

## A04 — Insecure Design

* **Categoría OWASP:** A04:2021 - Insecure Design
* **Estado:** **Vulnerable**
* **Evidencia:**
  1. **Rate limiting global definido pero NUNCA montado:** existe `RateLimitMiddleware` (límites global/auth/matching) en [`rate_limiter.py:16-54`](backend/app/core/rate_limiter.py#L16), pero [`main.py:53-62`](backend/app/main.py#L53) solo registra `CORSMiddleware` y `SecurityHeadersMiddleware`. El middleware de rate limiting es **código muerto**. En consecuencia, solo los endpoints de auth están limitados (vía llamadas explícitas a `check_rate_limit`); el resto de la API (matching, NLP, generación de PDF síncrona, feed) **no tiene límite de tasa**.
  2. **Identificador de usuario spoofable en el limitador de matching:** [`rate_limiter.py:34`](backend/app/core/rate_limiter.py#L34) usa el header `X-User-ID` (controlable por el cliente) como clave del límite. Incluso si el middleware estuviera montado, sería evadible cambiando el header.
  3. **Generación de PDF síncrona dentro del request:** [`cv.py:79`](backend/app/api/v1/cv.py#L79) ejecuta WeasyPrint en el hilo del request → vector de agotamiento de recursos sin rate limit que lo proteja.
* **Impacto:** Medio — denegación de servicio y abuso de endpoints costosos (matching, embeddings, PDF).
* **Probabilidad:** Media — trivial de disparar con peticiones automatizadas.
* **Severidad:** **Medio**
* **Control mitigante sugerido:** montar efectivamente el middleware de rate limiting; derivar la identidad del límite del JWT validado (no de un header), no de input del cliente; mover trabajo pesado (PDF) a tareas asíncronas con cuotas.

---

## A05 — Security Misconfiguration

* **Categoría OWASP:** A05:2021 - Security Misconfiguration
* **Estado:** **Vulnerable**
* **Evidencia:**
  1. **Credenciales por defecto en infraestructura:** Grafana `admin/changeme` ([`docker-compose.yml:166-167`](docker-compose.yml#L166)), PostgreSQL `postgres/postgres` ([`docker-compose.yml:29-30`](docker-compose.yml#L29)), SonarQube DB `sonar/sonar` ([`docker-compose.yml:190-191`](docker-compose.yml#L190)).
  2. **Servicios sensibles expuestos al host sin autenticación:** Redis en `6379:6379` **sin contraseña** ([`docker-compose.yml:49-50`](docker-compose.yml#L49) y `redis-server` sin `--requirepass` en línea 48), Flower en `5555` sin auth ([`docker-compose.yml:133-134`](docker-compose.yml#L133)), Prometheus `9090`, Grafana `3001`. Redis sin auth almacena la blacklist de tokens y el rate limiting → comprometerlo permite revocar/eludir sesiones.
  3. **Fuga de detalle de error en desarrollo:** el handler global retorna `str(exc)` cuando `ENVIRONMENT != production` ([`main.py:77`](backend/app/main.py#L77)). Correcto que se oculte en prod, pero el comportamiento depende enteramente de una variable de entorno bien fijada.
  4. **Clave criptográfica placeholder versionada** en el repositorio ([`config.py:12`](backend/app/core/config.py#L12)).
* **Fortalezas:** CORS con orígenes explícitos y `allow_methods`/`allow_headers` restringidos ([`main.py:53-59`](backend/app/main.py#L53)); cabeceras de seguridad OWASP (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, HSTS en prod) en [`security_headers.py`](backend/app/core/security_headers.py); `docs`/`redoc` deshabilitados fuera de desarrollo ([`main.py:42-43`](backend/app/main.py#L42)).
* **Impacto:** Medio-Alto si la configuración de desarrollo se reutiliza en entornos accesibles.
* **Probabilidad:** Media.
* **Severidad:** **Medio**
* **Control mitigante sugerido:** secretos únicos por entorno fuera del compose; no exponer puertos de datos/monitoreo al host; habilitar `requirepass` en Redis; principio de configuración segura por defecto.

---

## A06 — Vulnerable and Outdated Components

* **Categoría OWASP:** A06:2021 - Vulnerable and Outdated Components
* **Estado:** **Vulnerable**
* **Evidencia:**
  1. **`python-jose==3.3.0`** ([`requirements.txt:22`](backend/requirements.txt#L22)) — versión afectada por **CVE-2024-33663** (confusión de algoritmo en JWE/JWS) y **CVE-2024-33664** (DoS por "JWT bomb"/descompresión). Es la librería que firma y valida **todos los JWT de autenticación** → impacto directo sobre el núcleo de seguridad.
  2. **`python-multipart==0.0.12`** ([`requirements.txt:3`](backend/requirements.txt#L3)) — afectada por **CVE-2024-53981** (DoS por *boundary* malformado en `multipart/form-data`), corregida en 0.0.18. Se usa en todos los endpoints de subida (portafolio, `parse-cv`).
  3. No hay evidencia de escaneo de dependencias (SCA) en CI ni de fijación verificada de hashes.
* **Mitigación parcial observada:** `verify_token` restringe explícitamente el algoritmo a `[settings.JWT_ALGORITHM]` = `["RS256"]` ([`security.py:116`](backend/app/core/security.py#L116)), lo que reduce el vector de confusión de algoritmo a nivel de aplicación. No elimina el riesgo de la versión vulnerable.
* **Impacto:** Alto — la vulnerabilidad reside en la cadena de autenticación.
* **Probabilidad:** Media — explotación conocida y pública para estas CVE.
* **Severidad:** **Alto**
* **Control mitigante sugerido:** actualizar a versiones parcheadas; incorporar análisis de composición de software (SCA) automatizado al pipeline con *gate* de severidad.

---

## A07 — Identification and Authentication Failures

* **Categoría OWASP:** A07:2021 - Identification and Authentication Failures
* **Estado:** **Vulnerable**
* **Evidencia:**
  1. **Política de contraseñas débil:** solo `min_length=8`, sin requisitos de complejidad ni verificación contra contraseñas filtradas ([`auth.py (schema):9`](backend/app/schemas/auth.py#L9) y [`auth.py (schema):46`](backend/app/schemas/auth.py#L46)).
  2. **Sin bloqueo de cuenta:** la única defensa contra fuerza bruta es el rate limit por **IP** (20 login/h, [`auth.py:44,111`](backend/app/api/v1/auth.py#L111)). Un ataque de *credential stuffing* distribuido (múltiples IP) no se mitiga a nivel de cuenta.
  3. **Intentos fallidos de login no se auditan:** el handler lanza 401 ([`auth.py:116-120`](backend/app/api/v1/auth.py#L116)) **antes** de escribir en `AuditLog`; solo los logins exitosos quedan registrados. (Ver también A09.)
  4. **`email_verified` no se exige** para iniciar sesión (confirmado por ausencia de chequeo en `login`).
* **Fortalezas confirmadas:** mensaje de error de login genérico → sin enumeración de usuarios ([`auth.py:119`](backend/app/api/v1/auth.py#L119)); `forgot-password` con respuesta neutra anti-enumeración ([`auth.py:265-266`](backend/app/api/v1/auth.py#L265)); invalidación de sesiones tras reset de contraseña vía blacklist por usuario ([`auth.py:291`](backend/app/api/v1/auth.py#L291)); blacklist de `jti` en logout ([`security.py:142-149`](backend/app/core/security.py#L142)).
* **Impacto:** Medio.
* **Probabilidad:** Media.
* **Severidad:** **Medio**
* **Control mitigante sugerido:** política de contraseñas robusta + verificación contra *breach lists*; bloqueo/backoff progresivo por cuenta además del límite por IP; registrar y monitorear fallos de autenticación.

---

## A08 — Software and Data Integrity Failures

* **Categoría OWASP:** A08:2021 - Software and Data Integrity Failures
* **Estado:** **Vulnerable**
* **Evidencia:**
  1. **Instalación de dependencias en tiempo de arranque del contenedor:** el frontend ejecuta `npm install --legacy-peer-deps && npm run dev` como comando del servicio ([`docker-compose.yml:144`](docker-compose.yml#L144)). Usar `npm install` (no `npm ci`) en runtime no garantiza integridad reproducible del *lockfile* y puede traer versiones no fijadas.
  2. La CVE de `python-jose` (A06) es también un problema de **integridad de datos** (riesgo de forja de tokens por confusión de algoritmo), mitigado en parte por la restricción `algorithms=["RS256"]` en [`security.py:116`](backend/app/core/security.py#L116).
  3. No hay evidencia, dentro del alcance provisto, de verificación de integridad en el pipeline (firmas, hashes pinned, SRI).
* **Impacto:** Medio.
* **Probabilidad:** Baja-Media.
* **Severidad:** **Medio**
* **Control mitigante sugerido:** builds inmutables con `npm ci` sobre lockfile, dependencias con hashes fijados, verificación de integridad en CI/CD y artefactos firmados.

---

## A09 — Security Logging and Monitoring Failures

* **Categoría OWASP:** A09:2021 - Security Logging and Monitoring Failures
* **Estado:** **Vulnerable**
* **Evidencia:**
  1. **Fallos de autenticación no auditados:** `AuditLog` registra registro, login exitoso y logout, pero **no** los intentos fallidos de login (el 401 se lanza antes del audit — [`auth.py:116`](backend/app/api/v1/auth.py#L116)). Sin trazabilidad de fuerza bruta/credential stuffing en el registro de auditoría.
  2. **Eventos de seguridad sin alertado:** las violaciones de rate limit solo emiten `logger.warning` ([`rate_limit.py:25`](backend/app/core/rate_limit.py#L25)); no hay integración con un sistema de alertas/SIEM (Prometheus cubre métricas de infraestructura, no eventos de seguridad).
  3. **Errores silenciados:** bloques `except Exception: pass` ocultan fallos en [`dashboard.py:35,42`](backend/app/api/v1/admin/dashboard.py#L35) y [`rate_limiter.py:43`](backend/app/core/rate_limiter.py#L43) — incidentes potencialmente invisibles.
* **Fortalezas:** logging estructurado con `structlog` y un `AuditLog` persistente para acciones clave de usuario.
* **Impacto:** Medio — detección y respuesta a incidentes degradadas.
* **Probabilidad:** Media.
* **Severidad:** **Medio**
* **Control mitigante sugerido:** auditar explícitamente eventos de seguridad (login fallido, 403, rate-limit), centralizar logs y definir alertas sobre umbrales anómalos; evitar el silenciamiento de excepciones.

---

## A10 — Server-Side Request Forgery (SSRF)

* **Categoría OWASP:** A10:2021 - Server-Side Request Forgery
* **Estado:** **Seguro / Sin hallazgos**
* **Evidencia (verificada):** la única salida HTTP del servidor es el conector DRTPE, que usa una **URL base fija de constante** (`BASE_URL = "https://api.drtpe.gob.pe/v1"`, [`connector.py:100`](backend/app/integrations/drtpe/connector.py#L100)) y parámetros estructurados; el cliente no controla el destino de la petición. El parser de CV procesa archivos subidos, no descarga URLs. No se halló ningún endpoint que tome una URL del usuario y la solicite del lado del servidor.

---

## Resumen Ejecutivo

**Score Global de Seguridad: B — Nivel de Riesgo Global: MEDIO**

La arquitectura parte de **cimientos criptográficos y de autorización sólidos**, que constituyen su mayor fortaleza: JWT **RS256**, cifrado de PII con **AES-256-GCM** y nonce aleatorio, `bcrypt` cost 12, control de acceso por rol **a nivel de router** en el panel admin, verificación de propiedad de objeto (anti-IDOR) en CV y WebSocket, mensajes anti-enumeración y blacklist de tokens. La inyección está bien contenida por el uso de ORM con parámetros vinculados, y **no existe superficie de SSRF**. Estos dos puntos se confirmaron leyendo el código —no por suposición—, descartando falsos positivos.

Sin embargo, la postura presenta **brechas concretas y accionables** que impiden una calificación superior:

* **El riesgo más alto (A06)** son dependencias con CVE conocidas en el corazón de la autenticación: **`python-jose 3.3.0`** y **`python-multipart 0.0.12`**.
* **Diseño (A04):** el middleware de rate limiting global **está implementado pero no se monta**, dejando sin protección a todos los endpoints salvo auth, incluido un endpoint de PDF síncrono costoso.
* **Configuración (A05):** credenciales por defecto y servicios sensibles —en particular **Redis sin contraseña**— expuestos al host.
* **Cripto (A02) y Auth (A07):** tokens en `localStorage`, access tokens de 24 h, política de contraseñas mínima y ausencia de bloqueo por cuenta.
* **Monitoreo (A09):** los fallos de autenticación no se auditan.

**Conclusión:** ninguna vulnerabilidad crítica explotable de forma trivial fue confirmada, pero la combinación de componentes desactualizados con CVE, rate limiting inactivo y configuración de infraestructura insegura sitúa el riesgo global en **MEDIO**. La prioridad de remediación es: **(1) actualizar dependencias vulnerables, (2) activar el rate limiting, (3) endurecer la configuración de infraestructura (Redis/credenciales).**

---

*Auditoría estática basada en evidencia. No se modificó código ni se generaron remediaciones, conforme al alcance del encargo. Las CVE citadas corresponden a las versiones declaradas en `requirements.txt`; se recomienda confirmarlas con un escaneo SCA actualizado.*
