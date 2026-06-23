# INFORME DE AUDITORÍA DE SEGURIDAD — ISO/IEC 27001
## Sistema de Intermediación Laboral Linku — DRTPE-Junín

---

| Campo | Valor |
|---|---|
| **Organización auditada** | Dirección Regional de Trabajo y Promoción del Empleo de Junín (DRTPE-Junín) |
| **Sistema auditado** | Linku — Sistema de Intermediación Laboral ML/NLP |
| **Versión del sistema** | 0.2.0 (Sprint 5) |
| **Fecha de auditoría** | 2026-06-23 |
| **Normas de referencia** | ISO/IEC 27001:2022 · ISO/IEC 27002:2022 · ISO/IEC 25010:2023 |
| **Clasificación del informe** | CONFIDENCIAL — USO INTERNO |
| **Auditor** | Auditor Líder certificado ISO/IEC 27001 |

---

## RESUMEN EJECUTIVO

### Nivel General de Seguridad

El sistema Linku ha implementado controles de seguridad de **nivel ACEPTABLE-BUENO** para un sistema en fase de desarrollo activo. La arquitectura de autenticación es técnicamente sólida (JWT RS256, AES-256-GCM, bcrypt cost=12), existe trazabilidad de acciones críticas mediante logs de auditoría estructurados, y se aplican controles OWASP fundamentales. Sin embargo, existen **brechas significativas** que impiden la preparación para certificación formal en el estado actual.

### Calificación Global por Dominio

| Dominio | Calificación | Nivel |
|---|---|---|
| Control de Acceso | 3.5/5 | Aceptable |
| Autenticación y Autorización | 3/5 | Aceptable |
| Protección de Datos | 4/5 | Bueno |
| Registro y Trazabilidad | 3.5/5 | Aceptable |
| Seguridad de Aplicaciones | 4/5 | Bueno |
| Gestión de Riesgos | 2/5 | Deficiente |
| Continuidad y Recuperación | 1.5/5 | Muy Deficiente |
| Cumplimiento Normativo | 2.5/5 | Deficiente |

**Calificación global estimada: 3.0 / 5.0 (ACEPTABLE)**

### Principales Fortalezas

1. **Criptografía robusta**: JWT RS256 con par de claves asimétricas, AES-256-GCM para datos PII (DNI, nombre, teléfono), bcrypt cost=12 para contraseñas.
2. **Control de acceso basado en roles**: 4 roles diferenciados (WORKER, EMPLOYER, ADMIN, MODERATOR) con verificación en cada endpoint vía `require_role()`.
3. **Invalidación de tokens**: Blacklist Redis por JTI (logout) y por user_id (cambio de contraseña), previniendo reutilización de tokens robados.
4. **Rate limiting**: Implementado en Redis para registro (10/h), login (20/h) y recuperación de contraseña (5/h) por IP.
5. **Headers de seguridad**: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `HSTS` (en producción) vía middleware.
6. **Prevención de inyección SQL**: Todas las consultas utilizan SQLAlchemy ORM con parámetros enlazados.
7. **Logs de auditoría**: Tabla `audit_logs` registra acciones críticas (login, logout, registro, actualización de perfil) con IP, user_id y timestamp.
8. **Validación de archivos**: MIME type, tamaño máximo (5 MB) y sanitización de nombres de archivo en subida de fotos.
9. **Gestión de errores**: Handler global que oculta detalles técnicos en producción; Jinja2 con `autoescape=True`.
10. **Ownership verification**: Endpoints de CV y matching verifican que `worker.user_id == token.sub`.

### Principales Vulnerabilidades

1. **Sin autenticación multifactor (MFA)** — ausente en todos los flujos.
2. **Verificación de email no obligatoria al login** — `email_verified` existe en BD pero no se evalúa en `/auth/login`.
3. **PII almacenada en texto plano en Redis** — `reg_identity:{user.id}` guarda `full_name|DNI` sin cifrar durante 1 hora.
4. **Notificaciones como stub** — ningún email de verificación, recuperación de contraseña ni alertas se envía realmente (solo log).
5. **Token de acceso con vida de 24 horas** — ventana de exposición excesiva ante robo de token.
6. **Sin política de complejidad de contraseñas** — solo longitud mínima de 8 caracteres.
7. **Sin bloqueo de cuenta por intentos fallidos** — el rate limit es por IP, no por cuenta.
8. **Header Content-Security-Policy ausente** — el middleware de seguridad no lo incluye.
9. **Sin plan de continuidad ni backup documentado**.
10. **Clave RSA privada sin passphrase** — almacenada sin cifrado en el sistema de archivos.

### Riesgos Críticos

| ID | Riesgo | Nivel |
|---|---|---|
| R-01 | PII (DNI) expuesta en Redis sin cifrar | ALTO |
| R-02 | Sistema de email stub — recuperación de contraseña inoperativa | ALTO |
| R-03 | Sin MFA — cuentas admin vulnerables a credential stuffing | ALTO |
| R-04 | Token de acceso 24h — ventana extendida ante robo | MEDIO-ALTO |
| R-05 | Sin CSP header — riesgo de XSS persistente | MEDIO |

### Controles Ausentes

- Autenticación multifactor (MFA) — ISO 27002 A.8.5
- Sistema de notificaciones por email funcional
- Content-Security-Policy header
- Plan de recuperación ante desastres documentado
- Política de contraseñas con complejidad
- Bloqueo de cuenta por intentos fallidos
- Rotación de claves AES documentada
- Análisis de vulnerabilidades (DAST/SAST automatizado)
- Gestión formal de activos de información
- Inventario de riesgos documentado (SGSI)

### Controles Parcialmente Implementados

- Verificación de email (existe campo pero no se exige)
- Rate limiting (por IP, no por cuenta)
- Generación de CV (sincrónica, riesgo DoS)
- Matching engine (ml_score fijo en 0.5, no entrenado)
- Monitoreo (Prometheus disponible, alertas no configuradas)

---

## METODOLOGÍA

La auditoría se realizó mediante **revisión estática de código fuente** (gray-box), análisis de configuraciones, y verificación de controles implementados contra los requisitos de la norma. Las evidencias se extrajeron directamente de los archivos fuente del repositorio. No se realizaron pruebas de penetración activas.

**Archivos principales revisados:**
- `backend/app/core/security.py`
- `backend/app/core/config.py`
- `backend/app/core/security_headers.py`
- `backend/app/core/rate_limit.py`
- `backend/app/core/logging.py`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/matching.py`
- `backend/app/api/v1/workers.py`
- `backend/app/api/v1/jobs.py`
- `backend/app/api/v1/portfolio.py`
- `backend/app/api/v1/admin/__init__.py`
- `backend/app/api/v1/admin/dashboard.py`
- `backend/app/models/audit_log.py`
- `backend/app/services/cv_builder/pdf_generator.py`
- `backend/app/tasks/notifications.py`
- `backend/app/schemas/auth.py`
- `backend/app/main.py`
- `docker-compose.yml` (referenciado)
- `CLAUDE.md` (documentación del sistema)

---

## MATRIZ DE RESULTADOS DETALLADA

### 1. CONTROL DE ACCESO

| Dominio | Control evaluado | Evidencia encontrada | Cumplimiento | Riesgo identificado | Nivel de riesgo | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|---|---|---|
| Control de Acceso | Gestión de usuarios y roles | `UserRole` enum (WORKER, EMPLOYER, ADMIN, MODERATOR) en `security.py:26`. `require_role()` en todos los endpoints sensibles. | Cumple | Rol asignado en registro sin validación institucional | Bajo | 4 | El rol `ADMIN` puede auto-asignarse en el registro (`body.role`). En producción debe restringirse. | Bloquear asignación de roles ADMIN/MODERATOR en endpoint público de registro. Requiere flujo administrativo separado. |
| Control de Acceso | Principio de mínimo privilegio | Workers solo acceden a su propio perfil (`worker.user_id == token.sub`). Admin requiere rol ADMIN en todos los endpoints. Employers solo gestionan sus propias ofertas. | Cumple parcialmente | Endpoint `/jobs/feed` público (sin autenticación requerida) | Bajo | 4 | La decisión de exponer el feed de trabajos sin autenticación parece intencional (UX). Acceptable si no expone PII. | Verificar que `/jobs/feed` no exponga datos personales de trabajadores. Documentar la decisión de acceso anónimo. |
| Control de Acceso | Segregación de funciones | Roles distintos para Admin, Empleador, Trabajador. Admin protegido por `dependencies=[Depends(require_role(UserRole.ADMIN))]` a nivel de router. | Cumple | Sin evidencia de segregación dentro del rol ADMIN | Medio | 3 | No existe rol intermedio para operaciones de solo lectura en el panel admin. Todo admin tiene acceso completo. | Considerar rol MODERATOR para acceso de lectura al panel admin. Documentar matriz de acceso por función. |
| Control de Acceso | Gestión de sesiones | Blacklist por JTI en Redis (`invalidate_token`). Blacklist por user_id en cambio de contraseña. Tokens stateless JWT. | Cumple | Token de acceso 24h — ventana extendida | Medio-Alto | 3 | `ACCESS_TOKEN_EXPIRE_MINUTES=1440` (24 horas) es excesivo. Best practice: 15-30 minutos con refresh automático. | Reducir access token a 15-30 min. Implementar refresh automático en el frontend (pendiente `AUTH-REFRESH`). |
| Control de Acceso | Políticas de contraseñas | `password: str = Field(..., min_length=8, max_length=128)` en `auth.py`. bcrypt cost=12. | Cumple parcialmente | Sin complejidad de contraseña | Medio | 3 | Solo se valida longitud mínima (8 chars). No se requieren mayúsculas, números ni caracteres especiales. | Implementar validación de complejidad: al menos 1 mayúscula, 1 número y 1 carácter especial. Usar `zxcvbn` para estimación de fortaleza. |

---

### 2. AUTENTICACIÓN Y AUTORIZACIÓN

| Dominio | Control evaluado | Evidencia encontrada | Cumplimiento | Riesgo identificado | Nivel de riesgo | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|---|---|---|
| Autenticación | Inicio de sesión seguro | JWT RS256 con claves asimétricas auto-generadas. `verify_token()` valida firma + expiración + blacklist. Respuesta genérica "Credenciales invalidas" evita enumeración. | Cumple | Tiempo de respuesta variable (timing attack menor) | Bajo | 4 | La respuesta genérica es correcta. El uso de RS256 es preferible a HS256. Las claves se auto-generan si no existen. | Considerar tiempo de respuesta constante (`hmac.compare_digest`) en verificación de contraseña para mitigar timing attacks. |
| Autenticación | MFA — Doble Factor | Sin evidencia de implementación en ningún archivo fuente. | No cumple | Cuentas admin accesibles con solo contraseña | ALTO | 1 | Ausencia total de MFA. Cuentas administrativas con acceso a datos PII de todos los usuarios expuestas. | Implementar TOTP (RFC 6238) para cuentas ADMIN y MODERATOR como mínimo. Evaluar para EMPLOYER en etapas posteriores. |
| Autenticación | Recuperación de contraseñas | Token UUID aleatorio (`uuid4()`), TTL 1 hora en Redis. Respuesta no revela si el email existe. `reset-password` invalida todos los tokens del usuario. | Cumple parcialmente | Token enviado a STUB (nunca llega al usuario) | ALTO | 2 | `send_reset_email.delay()` en `notifications.py` solo hace `logger.info()`. El usuario nunca recibe el email. El flujo técnico es correcto pero inoperativo. | Implementar SMTP real (SendGrid, SES, Postfix). Prioridad máxima antes de producción. |
| Autenticación | Bloqueo de cuentas | Rate limit por IP (20 intentos/hora login). No existe bloqueo por cuenta. | Cumple parcialmente | Ataques de credenciales desde múltiples IPs no bloqueados | Medio | 3 | El rate limiting por IP no protege contra ataques distribuidos (botnets). Un atacante con múltiples IPs puede intentar contraseñas indefinidamente contra una cuenta. | Implementar contador de intentos fallidos por cuenta en Redis. Tras 5 fallos: bloqueo 15 min con notificación al usuario. |
| Autenticación | Verificación de email | Campo `email_verified` existe en modelo `User`. Endpoint `/verify-email` funcional. Login NO verifica este campo. | Cumple parcialmente | Usuarios con emails no verificados pueden operar | Medio | 3 | El flujo de verificación existe pero no está integrado en el login. Además, el email de verificación no se envía (stub). | Exigir `email_verified=True` en login. Implementar SMTP. Agregar reenvío de verificación. |
| Autenticación | Gestión de credenciales | `hashed_password` nunca expuesto en respuestas (verificado en `UserResponse`). AES-256-GCM para PII. RSA sin passphrase. | Cumple parcialmente | Clave RSA privada sin cifrado adicional en disco | Medio | 3 | `serialization.NoEncryption()` en `security.py:46`. Si el servidor es comprometido, la clave está inmediatamente disponible. | Agregar passphrase a la clave RSA privada (vía variable de entorno). Almacenar clave en vault (HashiCorp Vault o AWS Secrets Manager) en producción. |

---

### 3. PROTECCIÓN DE DATOS

| Dominio | Control evaluado | Evidencia encontrada | Cumplimiento | Riesgo identificado | Nivel de riesgo | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|---|---|---|
| Protección de Datos | Cifrado de datos en reposo (PII) | AES-256-GCM implementado en `security.py:80-91`. Campos `full_name`, `dni`, `phone` almacenados como `BYTEA` cifrado. Nonce de 12 bytes aleatorio por cifrado. | Cumple | Clave AES única para todo el sistema, sin rotación | Medio | 5 | Implementación correcta y robusta. El nonce aleatorio por cifrado previene ataques de replay. El modo GCM provee autenticidad además de confidencialidad. | Implementar rotación de clave AES. Documentar procedimiento de re-encriptado. Considerar cifrado por usuario (data isolation). |
| Protección de Datos | PII en caché Redis | `reg_identity:{user.id}` almacena `"full_name\|DNI"` como string plano en Redis con TTL 1h (`auth.py:73-77`). | No cumple | DNI y nombre en texto claro en Redis | ALTO | 1 | Crítico: Redis no tiene cifrado en reposo por defecto en la configuración detectada. Un atacante con acceso a Redis obtiene DNIs directamente. | Cifrar el valor antes de almacenar en Redis usando `encrypt_field()`. O eliminar el almacenamiento de PII en Redis — el DNI puede solicitarse de nuevo en onboarding. |
| Protección de Datos | Cifrado en tránsito | HTTPS no configurado en `docker-compose.yml` de desarrollo. HSTS configurado solo en producción. Nginx presente en infra/. | Cumple parcialmente | HTTP en desarrollo puede exponer credenciales | Medio | 3 | En desarrollo se usa HTTP. En producción Nginx debe terminar TLS. No hay evidencia de certificado configurado en el código revisado. | Verificar que Nginx en staging/producción tenga TLS 1.2+ configurado. Agregar `SECURE_COOKIES` en frontend. Prohibir HTTP en producción mediante HSTS (ya implementado condicionalmente). |
| Protección de Datos | Confidencialidad | Respuestas API no exponen `hashed_password`. `UserResponse` solo retorna `id`, `email`, `role`. PII se descifra solo para uso interno. | Cumple | Sin evidencia de scrubbing de logs | Bajo | 4 | Buena práctica en respuestas. Verificar que structlog no capture PII descifrada accidentalmente en eventos de debug. | Auditar todos los `logger.*` que puedan incluir objetos `Worker` con PII descifrada. Agregar masking de campos sensibles en el pipeline de logging. |
| Protección de Datos | Integridad de datos | AES-GCM provee autenticidad (MAC integrado). Pydantic v2 valida inputs. SQLAlchemy tipado. UUIDs como PKs. | Cumple | Sin checksums en archivos PDF generados | Bajo | 4 | La integridad de los datos en BD es adecuada. Los PDFs generados no tienen firma ni hash para verificar autenticidad. | Considerar firma digital (marca de agua o hash SHA256 en metadata) para PDFs generados. |
| Protección de Datos | Protección de datos sensibles (sector financiero) | Salary fields (`salary_min`, `salary_max`) en texto claro. RUC de employer cifrado. | Cumple parcialmente | Rangos salariales en texto claro podrían ser sensibles | Bajo | 4 | Los salarios en texto claro permiten análisis de mercado, considerado aceptable en plataformas de empleo. RUC cifrado es correcto. | Documentar decisión de diseño sobre datos salariales. Revisar qué datos del empleador son PII según legislación peruana (Ley 29733). |

---

### 4. REGISTRO Y TRAZABILIDAD

| Dominio | Control evaluado | Evidencia encontrada | Cumplimiento | Riesgo identificado | Nivel de riesgo | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|---|---|---|
| Registro | Auditoría de acciones críticas | Tabla `audit_logs` registra: `user_registered`, `user_login`, `user_logout`, `worker_profile_updated`. Campos: `user_id`, `action`, `ip_address`, `details` (JSONB), `created_at`. | Cumple parcialmente | Eventos de acceso fallido no auditados explícitamente | Medio | 3 | El registro de login exitoso y logout es correcto. Los intentos de login fallidos solo son contados por rate limit (Redis) pero no persisten en `audit_logs`. | Registrar intentos de login fallidos en `audit_logs` con `action="login_failed"`. Registrar también: cambio de contraseña, accesos al panel admin, generación de CV. |
| Registro | Logging estructurado | `structlog` configurado con JSON output, timestamps ISO, nivel INFO. `configure_logging()` aplicado al iniciar. | Cumple | Logs no incluyen correlación de request_id | Bajo | 4 | Logging estructurado JSON es la práctica correcta para sistemas modernos. Facilita análisis con ELK/Loki. | Agregar `request_id` (UUID por request HTTP) como contexto de structlog para correlación. Integrar con sistema centralizado de logs. |
| Registro | Retención de logs | Sin evidencia de política de retención de logs en el código o configuración. | Sin evidencia | Logs sin retención definida — riesgo de pérdida o sobreacumulación | Medio | 2 | No se encontraron configuraciones de log rotation, archivado o eliminación. En producción esto puede llenar el disco o violar regulaciones de retención. | Definir política de retención: audit_logs en BD → 2 años mínimo (ISO 27002 A.8.15). Logs de aplicación → 90 días. Implementar archivado automático. |
| Registro | Monitoreo de actividades sospechosas | Rate limit genera `logger.warning("rate_limit_exceeded")`. `SearchLog` registra búsquedas. Prometheus expuesto en `/metrics`. | Cumple parcialmente | Sin alertas automáticas sobre eventos de seguridad | Medio | 3 | Los datos de monitoreo existen (Prometheus, structlog) pero no hay evidencia de alertas configuradas (Grafana alerts, PagerDuty, etc.) para eventos de seguridad. | Configurar alertas en Grafana para: tasa alta de 401/429, errores 500, rate limits excedidos. Integrar con canal de notificación (email/Slack). |
| Registro | Inmutabilidad de logs | Logs escritos a stdout (contenedor Docker). Tabla `audit_logs` en PostgreSQL sin restricciones de inmutabilidad. | Cumple parcialmente | Administrador de BD puede modificar/eliminar audit_logs | Alto | 2 | Un usuario con acceso a PostgreSQL puede alterar los registros de auditoría. Esto viola el principio de no repudio. | Implementar `audit_logs` como append-only (trigger que rechace UPDATE/DELETE). Considerar exportar logs a sistema externo (S3, WORM storage) en producción. |

---

### 5. SEGURIDAD DE APLICACIONES

| Dominio | Control evaluado | Evidencia encontrada | Cumplimiento | Riesgo identificado | Nivel de riesgo | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|---|---|---|
| Seguridad App | Prevención de inyección SQL | SQLAlchemy ORM con consultas parametrizadas en toda la capa de datos. Consultas SQL raw en admin (`text()`) usan parámetros enlazados (`:limit`, `:offset`). | Cumple | Sin evidencia | Bajo | 5 | Excelente. Ninguna concatenación de strings en consultas SQL detectada en los archivos revisados. | Mantener disciplina de no usar concatenación de strings en consultas. Agregar análisis SAST (Bandit) al CI para detectar regresiones. |
| Seguridad App | Prevención de XSS | Jinja2 con `autoescape=True` en `pdf_generator.py:76`. Frontend React escapa por defecto. Headers `X-XSS-Protection` y `X-Content-Type-Options` presentes. | Cumple | Sin CSP header | Medio | 4 | La protección contra XSS reflected es buena. Sin embargo, la ausencia de CSP deja abierta la ventana para XSS almacenado en frontend. | Agregar header `Content-Security-Policy` en `SecurityHeadersMiddleware`. Definir directivas restrictivas (default-src 'self'). |
| Seguridad App | Prevención de CSRF | El esquema Bearer Token no requiere cookies, por lo que los ataques CSRF clásicos no aplican. Frontend usa localStorage (no cookies httpOnly). | Cumple parcialmente | localStorage vulnerable a XSS (tokens accesibles por JS) | Medio | 3 | El enfoque Bearer + localStorage es común en SPAs pero significa que tokens son accesibles por JavaScript. Si hay XSS, los tokens pueden robarse. | Evaluar migrar a cookies httpOnly + SameSite=Strict para mayor seguridad. Requiere implementar CSRF tokens en ese caso. |
| Seguridad App | Validación de entradas | Pydantic v2 valida todos los schemas de entrada. EmailStr valida emails. Min/max lengths definidos. Archivos: MIME type y tamaño validados. | Cumple parcialmente | `body: dict` sin tipado en `/workers/apply` | Bajo | 4 | El endpoint `apply_to_job` recibe `body: dict` sin schema Pydantic, accediendo con `body.get("job_offer_id", "")` sin validación de UUID. | Crear schema Pydantic `JobApplicationRequest` para el endpoint `/apply`. Validar que `job_offer_id` sea un UUID válido. |
| Seguridad App | Gestión de errores | Handler global `global_exception_handler` oculta detalles en producción (`"Error interno del servidor"`). En desarrollo expone el string del error. | Cumple | Detalles de excepción expuestos en desarrollo | Bajo | 4 | El comportamiento diferenciado prod/dev es correcto. Revisar que los strings de excepción de WeasyPrint, pypdf o spaCy no expongan paths del sistema en desarrollo. | Documentar que `ENVIRONMENT=development` nunca debe usarse con datos reales. Considerar un nivel de verbosidad controlada incluso en desarrollo. |
| Seguridad App | OWASP A01 — Broken Access Control | Ownership checks en CV (`worker.user_id == token.sub`), matching (mismo), workers (`_get_worker_or_404` por user_id). | Cumple | Endpoint `POST /register` permite auto-asignar rol ADMIN | Alto | 3 | La auto-asignación de rol ADMIN desde el registro público es la brecha más crítica de control de acceso. | Eliminar `role` del `RegisterRequest` público o whitelist solo `WORKER`/`EMPLOYER`. Crear endpoint admin separado para asignar roles elevados. |
| Seguridad App | OWASP A02 — Cryptographic Failures | AES-256-GCM, RS256, bcrypt-12. Sin TLS forzado en desarrollo. Clave AES default en config. | Cumple parcialmente | Clave AES default puede usarse accidentalmente en staging | Medio | 4 | El validador en `config.py:58-59` bloquea la clave default solo en `ENVIRONMENT=production`. En staging (`development`) puede usarse la clave default. | Agregar variable `STAGING` y bloquear la clave default también. O agregar advertencia en startup log si se usa la clave default. |
| Seguridad App | OWASP A03 — Injection | Sin SQL injection detectada. Parameterized queries. Jinja2 autoescape. | Cumple | Sin evidencia | Bajo | 5 | Cobertura sólida. | Mantener. |
| Seguridad App | OWASP A05 — Security Misconfiguration | API docs deshabilitados en producción. CORS restrictivo. Security headers configurados. `/tmp` en desarrollo (SonarQube SONAR-2). | Cumple parcialmente | `/tmp` para fotos en desarrollo — hotspot SonarQube | Bajo | 3 | El uso de `/tmp` para desarrollo es aceptable pero genera advertencias de seguridad. La configuración general es buena. | Resolver hotspot SONAR-2. Considerar directorio configurable en lugar de `/tmp` hardcodeado. |
| Seguridad App | OWASP A07 — Auth Failures | RS256, rate limiting, blacklist, bcrypt. Sin MFA. Sin account lockout. | Cumple parcialmente | Sin MFA ni lockout por cuenta | Alto | 3 | Los controles existentes son buenos pero incompletos. La ausencia de MFA es la debilidad principal. | Implementar MFA (ver recomendación en dominio Autenticación). |

---

### 6. GESTIÓN DE RIESGOS

| Dominio | Control evaluado | Evidencia encontrada | Cumplimiento | Riesgo identificado | Nivel de riesgo | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|---|---|---|
| Gestión de Riesgos | Identificación y documentación de riesgos | El archivo `CLAUDE.md` contiene una tabla de bugs/deuda conocida con prioridades. No existe un documento formal de evaluación de riesgos SGSI. | No cumple | Sin tratamiento formal de riesgos | Alto | 2 | La tabla de bugs en CLAUDE.md es una buena práctica de desarrollo pero no constituye un registro de riesgos de seguridad formal conforme a ISO 27001 Cláusula 6.1. | Crear y mantener un Registro de Riesgos de Seguridad (Statement of Applicability), incluyendo: identificación, evaluación de impacto/probabilidad, tratamiento y responsable. |
| Gestión de Riesgos | Análisis de impacto | Sin evidencia de Business Impact Analysis (BIA) formal. | Sin evidencia | Impacto de incidentes no cuantificado | Alto | 1 | No hay documentación que evalúe el impacto financiero, legal o reputacional de una brecha de seguridad. Considerando que el sistema maneja DNI de trabajadores informales vulnerables, el impacto sería alto. | Realizar BIA contemplando: exposición de DNIs, impacto en usuarios vulnerables, obligaciones bajo Ley 29733 (Perú) y sanciones ARCO. |
| Gestión de Riesgos | Equidad algorítmica | `ml/equity_ranker/ranker.py` implementa detección de disparate impact (< 0.80) y re-ranking. `equity_audit_log` tabla existe. | Cumple | `ml_score` fijo en 0.5 afecta la equidad real | Medio | 3 | La intención es correcta y la infraestructura existe. Sin embargo, con `ml_score=0.5` (stub), el re-ranking de equidad no opera sobre datos reales. | Priorizar el entrenamiento del modelo ML (`ML-STUB`). Documentar los criterios de equidad y umbrales. Auditar periódicamente la distribución de matches por distrito/género. |

---

### 7. CONTINUIDAD Y RECUPERACIÓN

| Dominio | Control evaluado | Evidencia encontrada | Cumplimiento | Riesgo identificado | Nivel de riesgo | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|---|---|---|
| Continuidad | Copias de seguridad | Sin evidencia de configuración de backups en `docker-compose.yml` ni en la documentación. PostgreSQL y Redis sin backup automatizado identificado. | No cumple | Pérdida total de datos ante fallo de infraestructura | ALTO | 1 | No se encontró ninguna configuración de pg_dump, snapshot o backup de Redis. Los datos PII de trabajadores y sus perfiles no tienen respaldo identificado. | Implementar pg_dump automatizado (diario mínimo) con retención de 30 días. Configurar backup de Redis RDB/AOF. Almacenar backups cifrados en ubicación externa (GCS bucket ya configurado). |
| Continuidad | Recuperación ante desastres | Sin Plan de Recuperación ante Desastres (DRP) documentado. Sin RPO/RTO definidos. | No cumple | Sin procedimiento de recuperación ante incidentes | ALTO | 1 | Ausencia total de documentación de DRP. En caso de pérdida de datos o compromiso del sistema, no existe guía de actuación. | Definir RPO (máxima pérdida de datos tolerable) y RTO (tiempo máximo de recuperación). Documentar procedimiento de restauración. Probar con drill semestral. |
| Continuidad | Disponibilidad del sistema | Docker Compose con múltiples servicios (api, worker-embeddings, worker-cv, worker-notifications). Nginx como proxy. Celery para tareas async. | Cumple parcialmente | Sin health checks en compose, sin auto-restart, sin HA | Medio | 2 | El stack es adecuado para desarrollo. Para producción falta: health checks en compose, restart policies, load balancing, configuración de alta disponibilidad. | Agregar `restart: unless-stopped` y `healthcheck` a todos los servicios en docker-compose. Evaluar Kubernetes u orquestador para producción. |
| Continuidad | Planes de contingencia | Celery Beat automatiza tareas periódicas. Sin plan de contingencia manual si Celery falla. Generación de PDF síncrona puede fallar bajo carga. | Cumple parcialmente | CV download sincrónico — single point of failure | Medio | 2 | Si WeasyPrint falla o tarda, el endpoint `/cv/download` bloquea el request. Para producción esto es un riesgo de disponibilidad. | Migrar `/cv/download` a servicio del resultado de la tarea Celery + storage (GCS). El endpoint síncrono es aceptable solo en dev. |

---

### 8. CUMPLIMIENTO NORMATIVO

| Dominio | Control evaluado | Evidencia encontrada | Cumplimiento | Riesgo identificado | Nivel de riesgo | Calificación | Observaciones | Recomendaciones |
|---|---|---|---|---|---|---|---|---|
| Normativo | Alineación ISO/IEC 27001 Cláusula 4 (Contexto) | Sin evidencia de definición de partes interesadas, alcance del SGSI, ni análisis del contexto organizacional documentado. | No cumple | Sin marco SGSI formal | Alto | 1 | La norma exige documentación del contexto organizacional como base del SGSI. No hay evidencia de este proceso. | Definir formalmente: alcance del SGSI, partes interesadas (DRTPE, trabajadores, empleadores, ARCO), contexto interno y externo. |
| Normativo | Alineación ISO/IEC 27001 Cláusula 6 (Planificación) | Tabla de bugs en CLAUDE.md aproxima un registro de riesgos pero no cumple el formato requerido. | No cumple | Sin evaluación de riesgos formal | Alto | 1 | La Cláusula 6.1 exige proceso documentado de evaluación y tratamiento de riesgos con criterios de aceptación. | Implementar proceso formal de gestión de riesgos con: metodología, criterios, registro y plan de tratamiento. |
| Normativo | Controles ISO/IEC 27002 — A.8.2 Identidades | UUIDs como identificadores únicos. Gestión de usuarios en BD. Sin proceso formal de baja de usuarios. | Cumple parcialmente | Sin proceso de baja de usuario documentado | Bajo | 3 | No hay endpoint ni proceso identificado para desactivar/eliminar cuentas de usuarios que ya no deben tener acceso. | Implementar endpoint de desactivación de cuenta (`is_active=False`). Documentar proceso de baja de empleados/usuarios. |
| Normativo | Protección de datos personales — Ley 29733 (Perú) | AES-256-GCM para DNI y datos biométricos. Sin cláusula de consentimiento explícita identificada en el código. Sin mecanismo ARCO (Acceso, Rectificación, Cancelación, Oposición). | Cumple parcialmente | Sin mecanismo ARCO visible | Alto | 2 | La Ley 29733 y su reglamento exigen: consentimiento informado, finalidad declarada, seguridad de datos (cumple parcialmente), y mecanismo ARCO para los titulares de datos. | Implementar: modal de consentimiento en registro, política de privacidad visible, endpoint de eliminación/exportación de datos propios. Registrar el banco de datos en ARCO (MINJUSDH). |
| Normativo | ISO/IEC 25010 — Seguridad Funcional | Autenticidad (JWT), confidencialidad (AES), integridad (AES-GCM MAC), no repudio (audit_logs), responsabilidad (roles). | Cumple parcialmente | Audit_logs modificables por admin BD | Medio | 3 | La mayoría de las características de seguridad de ISO 25010 están implementadas técnicamente. La inmutabilidad de logs y el no repudio son débiles. | Implementar audit_logs append-only. Considerar firma de registros críticos. |

---

## MATRIZ DE RIESGOS

| ID | Activo | Vulnerabilidad | Amenaza | Impacto | Probabilidad | Nivel de Riesgo | Tratamiento Propuesto |
|---|---|---|---|---|---|---|---|
| R-01 | PII en Redis (DNI, nombre) | Almacenamiento en texto plano en `reg_identity:{id}` | Acceso no autorizado a Redis — dump de memoria | ALTO (exposición masiva DNIs) | MEDIO (Redis interno, pero sin cifrado) | **ALTO** | Cifrar con `encrypt_field()` antes de guardar en Redis. O eliminar almacenamiento de PII en caché. |
| R-02 | Sistema de recuperación de contraseña | Email de reset solo en stub (log) — nunca llega al usuario | Usuario malintencionado solicita reset de cuenta ajena para denegación de servicio | ALTO (pérdida de acceso para usuarios legítimos) | BAJO (requiere conocer email) | **MEDIO-ALTO** | Implementar SMTP funcional urgente. Sin esto, el sistema no es operable en producción. |
| R-03 | Cuentas de administrador DRTPE | Sin MFA — acceso con solo contraseña | Credential stuffing, phishing, brute force distribuido | ALTO (acceso a todos los datos de usuarios) | MEDIO | **ALTO** | Implementar TOTP/FIDO2 para cuentas ADMIN. Prioridad máxima. |
| R-04 | Token JWT de acceso | Vida útil de 24 horas | Robo de token (XSS, red insegura, dispositivo robado) | ALTO (acceso completo a cuenta por 24h) | BAJO-MEDIO | **MEDIO** | Reducir a 15-30 min. Implementar refresh automático en frontend. |
| R-05 | Endpoint de registro público | Campo `role` permite auto-asignar ADMIN | Creación de cuenta ADMIN no autorizada | ALTO (acceso total al sistema) | MEDIO (requiere conocer la API) | **ALTO** | Eliminar `role` del registro público o whitelist WORKER/EMPLOYER únicamente. |
| R-06 | Clave RSA privada | Sin passphrase ni almacenamiento seguro | Compromiso del servidor → exfiltración de private.pem | ALTO (falsificación de tokens ilimitada) | BAJO (requiere acceso al servidor) | **MEDIO** | Almacenar en vault. Agregar passphrase configurada vía env var. Rotar periódicamente. |
| R-07 | Datos en PostgreSQL | Sin backups identificados | Fallo de hardware, corrupción, ransomware | ALTO (pérdida total de datos de trabajadores) | BAJO-MEDIO | **ALTO** | Implementar backup diario cifrado a GCS. Probar restauración. Definir RPO/RTO. |
| R-08 | Audit logs en PostgreSQL | Tabla modificable por DBA | Administrador malintencionado altera evidencias | ALTO (violación de no repudio) | BAJO | **MEDIO** | Trigger append-only. Exportar logs a sistema inmutable externo. |
| R-09 | Endpoint `/cv/download` síncrono | WeasyPrint bloqueante | Denegación de servicio mediante múltiples requests de generación de PDF | MEDIO (degradación de disponibilidad) | MEDIO | **MEDIO** | Migrar a flujo async Celery + storage. Aplicar rate limit al endpoint. |
| R-10 | Cuentas sin verificación de email | `email_verified` no se verifica en login | Registro con email de tercero, uso del sistema en nombre ajeno | MEDIO | MEDIO | **MEDIO** | Exigir verificación de email antes del primer acceso. |
| R-11 | Bloqueo por IP solamente | Sin bloqueo por cuenta | Ataque de fuerza bruta distribuida contra cuenta específica | MEDIO | MEDIO | **MEDIO** | Contador de fallos por cuenta en Redis. Bloqueo temporal + notificación. |
| R-12 | Ausencia de CSP header | Sin Content-Security-Policy | XSS almacenado permite robo de tokens desde localStorage | ALTO (si XSS ejecutado) | BAJO | **MEDIO** | Agregar CSP restrictivo en SecurityHeadersMiddleware. |
| R-13 | Tokens en localStorage | Accesibles por JavaScript | XSS → exfiltración de access_token y refresh_token | ALTO | BAJO | **MEDIO** | Evaluar cookies httpOnly+SameSite. Implementar CSP como mitigación principal. |
| R-14 | Ley 29733 — Sin mecanismo ARCO | Sin endpoint de eliminación/exportación de datos propios | Incumplimiento regulatorio, sanción de autoridad peruana | ALTO (legal y reputacional) | MEDIO (si operación comercial) | **ALTO** | Implementar portal ARCO. Registrar banco de datos. Consultar asesoría legal. |
| R-15 | Ausencia de backups Redis | Estado de sesiones (blacklist, rate limit) en Redis sin persistencia AOF verificada | Pérdida de blacklist → tokens invalidados vuelven a ser válidos | MEDIO | BAJO | **MEDIO** | Verificar configuración de Redis AOF. Evaluar Redis Cluster para producción. |

---

## CONCLUSIÓN FINAL

### Porcentaje Estimado de Cumplimiento ISO/IEC 27001

| Cláusula ISO 27001 | Estado | % Cumplimiento Estimado |
|---|---|---|
| Cláusula 4 — Contexto de la organización | No implementado | 5% |
| Cláusula 5 — Liderazgo | Sin evidencia | 10% |
| Cláusula 6 — Planificación (riesgos) | Parcial | 20% |
| Cláusula 7 — Soporte (recursos, concienciación) | Sin evidencia | 10% |
| Cláusula 8 — Operación (controles técnicos) | Parcial | 55% |
| Cláusula 9 — Evaluación del desempeño | Parcial (Prometheus) | 25% |
| Cláusula 10 — Mejora continua | Sin evidencia formal | 10% |
| **Controles técnicos (Anexo A / ISO 27002)** | **Parcial** | **50%** |

**Porcentaje global estimado de cumplimiento: ~35%**

> Nota: Este porcentaje refleja el estado actual, donde los controles técnicos están significativamente más avanzados que la documentación del SGSI. Un sistema puede tener excelentes controles técnicos y aun así no superar una auditoría formal si carece del marco documental que exige ISO 27001.

### Nivel de Madurez de Seguridad

Basado en el modelo CMMI aplicado a seguridad:

| Nivel | Descripción | Estado |
|---|---|---|
| 1 — Inicial | Controles ad-hoc, sin documentación | Superado |
| 2 — Gestionado | Controles básicos implementados, parcialmente documentados | **NIVEL ACTUAL** |
| 3 — Definido | Procesos documentados y estandarizados | Parcialmente |
| 4 — Cuantificado | Métricas de seguridad y KPIs definidos | No alcanzado |
| 5 — Optimizado | Mejora continua con lecciones aprendidas | No alcanzado |

**Madurez actual: Nivel 2 (Gestionado) — con elementos de Nivel 3 en controles técnicos**

### Preparación para Auditoría Formal

**El sistema NO está preparado para una auditoría formal ISO/IEC 27001 en el estado actual.**

Razones principales:
1. Ausencia del marco documental del SGSI (cláusulas 4-7, 9-10)
2. Riesgos críticos sin mitigar (PII en Redis, sin MFA, sin backups)
3. Incumplimiento de Ley 29733 (sin mecanismo ARCO)
4. Ausencia de plan de continuidad y recuperación

### Acciones Prioritarias Antes de Certificación

**Plazo inmediato (≤ 30 días):**
1. Cifrar PII en Redis (`reg_identity`) — R-01
2. Eliminar auto-asignación de rol ADMIN en registro público — R-05
3. Implementar SMTP funcional para emails críticos — R-02
4. Agregar CSP header en middleware de seguridad — R-12

**Plazo corto (≤ 90 días):**
5. Implementar MFA (TOTP) para cuentas ADMIN — R-03
6. Reducir lifetime del access token a 15-30 min + refresh automático — R-04
7. Implementar backup automatizado de PostgreSQL a GCS — R-07
8. Forzar verificación de email en login — R-10
9. Agregar bloqueo de cuenta por intentos fallidos — R-11
10. Implementar mecanismo ARCO básico — R-14

**Plazo medio (≤ 180 días):**
11. Redactar SGSI: contexto, alcance, política de seguridad
12. Documentar registro formal de riesgos
13. Hacer audit_logs append-only
14. Definir y probar Plan de Recuperación ante Desastres
15. Implementar política de retención de logs
16. Entrenar y desplegar el modelo ML real (`ML-STUB`)
17. Integrar Bandit/SonarQube en pipeline CI/CD

### Recomendaciones Estratégicas

1. **Establecer un rol de Responsable de Seguridad de la Información (RISI)** dentro de la DRTPE-Junín que supervise el SGSI y la evolución de controles.

2. **Separar los entornos** de manera formal: development → staging → producción, con controles distintos por entorno y prohibición explícita de usar datos reales en desarrollo.

3. **Adoptar el principio de Secure by Default**: cada nueva funcionalidad debe incluir análisis de seguridad en su definición (security requirements as acceptance criteria).

4. **Integrar seguridad en el ciclo CI/CD**: Bandit (Python SAST), npm audit (frontend), análisis SonarQube en cada PR, no solo al final del sprint.

5. **Concienciación en seguridad**: dado el contexto de usuarios con baja alfabetización digital, agregar mensajes claros sobre phishing, contraseñas seguras y manejo de datos en la UX.

6. **Gestión de secretos**: migrar AES_KEY, credenciales de BD y claves RSA a un gestor de secretos (HashiCorp Vault, AWS Secrets Manager, o GCP Secret Manager) en producción.

7. **Cumplimiento Ley 29733**: consultar asesoría legal especializada en protección de datos personales en Perú para asegurar el cumplimiento regulatorio, especialmente por el manejo de DNIs de población vulnerable.

---

## APÉNDICE — EVIDENCIAS TÉCNICAS CLAVE

### E-01: Cifrado AES-256-GCM para PII (FORTALEZA)
```python
# backend/app/core/security.py:80-91
def encrypt_field(value: str) -> bytes:
    aesgcm = AESGCM(_get_aes_key())
    nonce = os.urandom(12)          # Nonce aleatorio por cifrado — correcto
    ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
    return nonce + ciphertext       # Nonce prepended para descifrado
```

### E-02: PII en Redis sin cifrar (VULNERABILIDAD CRÍTICA)
```python
# backend/app/api/v1/auth.py:73-77
if body.full_name or body.dni:
    await redis.setex(
        f"reg_identity:{user.id}",
        3600,
        f"{body.full_name}|{body.dni}"   # DNI y nombre en texto plano
    )
```

### E-03: Auto-asignación de rol ADMIN (VULNERABILIDAD ALTA)
```python
# backend/app/schemas/auth.py:10
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.WORKER   # Cualquier usuario puede enviar role=ADMIN
```

### E-04: Token de acceso 24 horas (RIESGO MEDIO)
```python
# backend/app/core/config.py:29
ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas — excesivo
```

### E-05: Security Headers parciales (sin CSP)
```python
# backend/app/core/security_headers.py
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
# FALTA: Content-Security-Policy
```

### E-06: Notificaciones stub (FUNCIONALIDAD INOPERATIVA)
```python
# backend/app/tasks/notifications.py:9-12
@app.task(name="send_reset_email")
def send_reset_email(user_id: str, token: str) -> None:
    logger.info("reset_email_queued", user_id=user_id)
    # Sin envío real — token de reset nunca llega al usuario
```

---

*Informe generado el 2026-06-23. Válido para revisión durante 6 meses o hasta cambio de versión mayor del sistema.*
*Próxima auditoría recomendada: 2026-12-23 o tras implementación de acciones prioritarias.*
