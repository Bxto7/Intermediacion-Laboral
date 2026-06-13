# Plan de Remediación de Seguridad — OWASP Top 10 (2021)

> Proyecto: **Linku — Sistema de Intermediación Laboral DRTPE-Junín**
> Entrada: [`04_Auditoria_OWASP.md`](04_Auditoria_OWASP.md)
> Fecha: 2026-06-13 · Rama: `AUDITORIAS`
> Autor: Agente 5 — Arquitecto de Seguridad / DevSecOps.
> Principio rector: **mitigar el riesgo sin romper la funcionalidad existente.** Cada ítem incluye validación y rollback.

---

## 1. Resumen Ejecutivo y Riesgos de Implementación

### 1.1 Panorama de la deuda técnica de seguridad

La auditoría confirmó una base criptográfica y de autorización sólida (RS256, AES-256-GCM, bcrypt 12, RBAC a nivel de router, anti-IDOR), sin inyección explotable ni SSRF. La deuda de seguridad **no está en el diseño del núcleo**, sino en tres frentes operativos y de mantenimiento:

1. **Dependencias con CVE conocidas** en la cadena de autenticación (riesgo Alto, A06).
2. **Controles implementados pero inactivos o incompletos** — el rate limiting global existe pero no se monta (A04); los fallos de login no se auditan (A07/A09).
3. **Configuración de infraestructura insegura por defecto** — credenciales débiles y Redis sin contraseña expuesto (A05).

La buena noticia para la planificación: **la mayoría de los hallazgos son de bajo riesgo de regresión** porque corrigen omisiones (activar lo que ya existe, subir versiones parcheadas, endurecer config) más que reescribir lógica de negocio.

### 1.2 Principales riesgos al implementar las soluciones

| Cambio propuesto | Riesgo de regresión | Mitigación del riesgo |
|------------------|---------------------|------------------------|
| Subir `python-jose` / `python-multipart` | Cambios de firma/comportamiento en validación JWT o parsing multipart | Suite de tests de auth + uploads como *gate*; despliegue en *staging* primero |
| Montar el rate limiting global | Bloqueo accidental de tráfico legítimo (límites mal calibrados) | Modo "shadow"/observación con umbrales altos; *feature flag* por variable de entorno |
| Migrar tokens de `localStorage` a cookies `HttpOnly` | Romper el flujo de login/logout de toda la SPA | Cambio en **fase**, detrás de *feature flag*; mantener compatibilidad de lectura durante transición |
| Endurecer Redis (password) | Caída de todos los servicios que dependen de Redis (auth blacklist, Celery, rate limit) | Rotación coordinada de `REDIS_URL` en todos los servicios del compose en el mismo despliegue |
| Política de contraseñas fuerte | Afectar registro de usuarios nuevos (no debe afectar a los existentes) | Aplicar solo a `register`/`reset`, **nunca** invalidar contraseñas vigentes |

### 1.3 Estrategia Global para preservar la funcionalidad

1. **Backward-compatibility primero:** ningún cambio invalida sesiones, contraseñas ni datos existentes salvo que sea el objetivo explícito de seguridad (y entonces se comunica y se hace en ventana controlada).
2. **Feature flags por variable de entorno:** los cambios de comportamiento observable (rate limiting, almacenamiento de tokens, política de contraseñas) se activan progresivamente y se pueden desactivar sin redeploy de código.
3. **Despliegue en fases con `staging` obligatorio:** todo cambio de dependencia o middleware pasa por `docker-compose.staging.yml` con la suite de tests completa antes de producción.
4. **Cada cambio en su propia rama y PR atómico** (`fix/owasp-aXX-descripcion`), revisable y reversible de forma aislada.
5. **Observabilidad antes de bloquear:** los controles que pueden rechazar tráfico (rate limit, validaciones) se despliegan primero en modo "log-only" para medir impacto real antes de hacer *enforce*.

---

## 2. Roadmap de Remediación (Orden Recomendado)

### Fase 1 — Quick Wins y Críticos
> Alto impacto de seguridad, bajo riesgo de regresión. Ejecutar de inmediato.

| ID | Vulnerabilidad | OWASP | Por qué primero |
|----|----------------|-------|-----------------|
| R-01 | Dependencias con CVE (`python-jose`, `python-multipart`) | A06 | Riesgo Alto, parche es subir versión + correr tests |
| R-02 | Rate limiting global no montado | A04 | El control ya existe; activarlo es de bajo riesgo con modo observación |
| R-03 | Redis sin contraseña expuesto al host | A05 | Compromiso de Redis = elusión de sesiones; config, no código |
| R-04 | Credenciales por defecto (Grafana/DB/Sonar) | A05 | Cambio de secretos, sin tocar lógica |
| R-05 | Fallos de login no auditados | A07/A09 | Pocas líneas, habilita detección de fuerza bruta |

### Fase 2 — Remediaciones Estructurales
> Requieren refactor o despliegue por fases. Priorizadas tras la Fase 1.

| ID | Vulnerabilidad | OWASP | Naturaleza |
|----|----------------|-------|------------|
| R-06 | Tokens en `localStorage` (exposición a XSS) | A02 | Migración a cookies `HttpOnly` en fases con feature flag |
| R-07 | Identidad de rate limit basada en header spoofable | A04 | Derivar del JWT validado |
| R-08 | Generación de PDF síncrona en el request | A04 | Mover a tarea async con cuota |
| R-09 | Política de contraseñas débil y sin bloqueo de cuenta | A07 | Validación + backoff por cuenta |
| R-10 | Gestión de secretos fuera del código (AES/RSA/secret manager) | A02/A05 | Integrar gestor de secretos |

### Fase 3 — Deuda Técnica y Hardening
> Riesgos medios/bajos y buenas prácticas.

| ID | Vulnerabilidad | OWASP | Naturaleza |
|----|----------------|-------|------------|
| R-11 | Build de frontend con `npm install` en runtime | A08 | `npm ci` + build inmutable |
| R-12 | Token JWT del WebSocket en query string | A02 | Transporte por subprotocolo/header |
| R-13 | Access token de larga vida (24 h) sin refresh | A02/A07 | Reducir TTL + rotación de refresh |
| R-14 | `except Exception: pass` y ausencia de alertado | A09 | Logging explícito + alertas SIEM |
| R-15 | Vector de embedding concatenado en SQL | A03 | Parametrizar (defensa en profundidad) |
| R-16 | SCA automatizado y configuración segura por defecto | A06/A05 | Gate de seguridad en CI/CD |

---

## 3. Plan Detallado por Vulnerabilidad

### R-01 — Dependencias con CVE en la cadena de autenticación
* **Vulnerabilidad:** `python-jose==3.3.0` (CVE-2024-33663, CVE-2024-33664) y `python-multipart==0.0.12` (CVE-2024-53981) en [`requirements.txt:22,3`](../backend/requirements.txt#L22).
* **Riesgo e Impacto:** posible confusión de algoritmo / DoS sobre el motor que firma y valida **todos los JWT**, y DoS en endpoints de subida. Compromete autenticación y disponibilidad — el núcleo del negocio.
* **Prioridad:** **Crítico** (severidad Alto del informe + facilidad de explotación pública).
* **Estrategia de Mitigación:** actualizar a versiones parcheadas (`python-jose` ≥ 3.4.0, `python-multipart` ≥ 0.0.18) con *pinning* exacto. Mantener la restricción explícita `algorithms=["RS256"]` ya presente en [`security.py:116`](../backend/app/core/security.py#L116) como defensa en profundidad. Verificar compatibilidad con FastAPI 0.115.
* **Estrategia de Validación:** correr la suite de auth (`tests/` de login/register/refresh/logout/verify) y de uploads (portafolio, `parse-cv`) en `staging`; confirmar que un JWT válido sigue verificándose y uno manipulado se rechaza con 401; escaneo SCA posterior sin hallazgos de severidad alta.
* **Estrategia de Rollback:** revertir el pin de versión en `requirements.txt` al valor anterior y reconstruir la imagen (`docker-compose build api worker-*`). Sin migración de datos involucrada → rollback inmediato y sin pérdida.

---

### R-02 — Rate limiting global implementado pero no montado
* **Vulnerabilidad:** `RateLimitMiddleware` definido en [`rate_limiter.py:16-54`](../backend/app/core/rate_limiter.py#L16) nunca se registra en [`main.py:53-62`](../backend/app/main.py#L53). API sin límite de tasa salvo `/auth`.
* **Riesgo e Impacto:** DoS y abuso de endpoints costosos (matching, NLP, PDF síncrono). Afecta disponibilidad del servicio público.
* **Prioridad:** **Alto**.
* **Estrategia de Mitigación:** registrar el middleware en `main.py` **detrás de un feature flag** (`RATE_LIMIT_ENABLED`) con un **modo observación** inicial (loguea pero no bloquea) para calibrar umbrales con tráfico real antes de hacer *enforce*. Cerrar de forma segura ante fallo de Redis (ya hace *fail-open* en la línea 43, lo cual preserva disponibilidad).
* **Estrategia de Validación:** test de integración que dispare N+1 peticiones y verifique `429` cuando el flag está en *enforce*; revisar métricas/logs de `rate_limit_exceeded` en modo observación para confirmar que no afecta tráfico legítimo.
* **Estrategia de Rollback:** poner `RATE_LIMIT_ENABLED=false` (o volver a modo observación) — desactiva el bloqueo **sin redeploy de código**. El middleware queda inerte como antes.

---

### R-03 — Redis sin contraseña expuesto al host
* **Vulnerabilidad:** Redis en `6379:6379` sin `--requirepass` ([`docker-compose.yml:48-50`](../docker-compose.yml#L48)). Almacena blacklist de tokens y rate limiting.
* **Riesgo e Impacto:** quien acceda a Redis puede borrar la blacklist (reactivar sesiones revocadas) o manipular contadores de rate limit. Compromiso de control de sesiones.
* **Prioridad:** **Alto**.
* **Estrategia de Mitigación:** (1) no exponer el puerto 6379 al host (eliminar el mapeo de puertos en la red interna `drtpe_net`); (2) configurar `--requirepass` y propagar la credencial a `REDIS_URL` en **todos** los servicios (api, workers, beat, flower) en el mismo despliegue para evitar desincronización.
* **Estrategia de Validación:** verificar que `api` y los `worker-*` se conectan a Redis con la nueva URL (health checks en verde); confirmar desde el host que el puerto ya no responde sin credencial.
* **Estrategia de Rollback:** restaurar el `docker-compose.yml` previo y reiniciar la pila (`docker-compose up -d`). Redis es almacén efímero (blacklist/rate limit con TTL) → sin pérdida de datos de negocio; en el peor caso se reinician contadores.

---

### R-04 — Credenciales por defecto en infraestructura
* **Vulnerabilidad:** Grafana `admin/changeme` ([`docker-compose.yml:166-167`](../docker-compose.yml#L166)), PostgreSQL `postgres/postgres` ([`:29-30`](../docker-compose.yml#L29)), SonarQube DB `sonar/sonar` ([`:190-191`](../docker-compose.yml#L190)).
* **Riesgo e Impacto:** acceso administrativo a paneles y base de datos si estos entornos quedan accesibles. Fuga de PII y métricas institucionales.
* **Prioridad:** **Alto** (Medio-Alto del informe; trivial de remediar).
* **Estrategia de Mitigación:** mover todas las credenciales a variables de entorno por entorno (`.env` no versionado / secret manager), con secretos únicos y robustos. Documentar que los valores del compose son **solo placeholders de desarrollo local**.
* **Estrategia de Validación:** confirmar arranque de cada servicio con las nuevas credenciales; intentar login con las credenciales por defecto y verificar que fallan.
* **Estrategia de Rollback:** los servicios afectados (Grafana, Sonar) no son parte del flujo de negocio del usuario final; revertir variables y reiniciar el servicio puntual. Para PostgreSQL, cambiar la contraseña es reversible vía rotación; **coordinar con `DATABASE_URL`** para no dejar la API sin BD.

---

### R-05 — Fallos de autenticación no auditados
* **Vulnerabilidad:** el 401 de login se lanza antes de escribir `AuditLog` ([`auth.py:116-120`](../backend/app/api/v1/auth.py#L116)); solo se auditan logins exitosos.
* **Riesgo e Impacto:** sin trazabilidad de fuerza bruta / credential stuffing; ceguera ante incidentes (A09).
* **Prioridad:** **Medio**.
* **Estrategia de Mitigación:** registrar el intento fallido en `AuditLog` (acción `login_failed`, IP, email tentado) **antes** de lanzar la excepción, sin filtrar si el email existe (preservar la respuesta genérica anti-enumeración actual).
* **Estrategia de Validación:** test que provoque un login inválido y verifique una entrada `login_failed` en `AuditLog`; confirmar que el mensaje al cliente sigue siendo genérico ("Credenciales invalidas").
* **Estrategia de Rollback:** revertir el bloque de auditoría; es aditivo y no altera el flujo de autenticación, por lo que el rollback no afecta a usuarios.

---

### R-06 — Tokens de sesión en `localStorage`
* **Vulnerabilidad:** `access_token`/`refresh_token` en `localStorage` ([`client.ts:13,40`](../frontend/src/api/client.ts#L13)), expuestos a exfiltración por XSS.
* **Riesgo e Impacto:** robo de sesión completo ante cualquier XSS en la SPA. Suplantación de usuarios.
* **Prioridad:** **Alto** (severidad Medio, pero alto impacto si hay XSS).
* **Estrategia de Mitigación:** migrar a cookies `HttpOnly` + `Secure` + `SameSite=Strict` emitidas por el backend, en **fases** detrás de un feature flag: (1) backend acepta ambos esquemas (header Bearer **y** cookie) durante la transición; (2) frontend pasa a usar cookies; (3) se retira el soporte de `localStorage`. Requiere ajustar CORS (`allow_credentials` ya es `true`).
* **Estrategia de Validación:** E2E de login/refresh/logout en ambos esquemas durante la transición; verificar que el token ya no es accesible vía `document.cookie` / JS; pruebas de CSRF (al usar cookies, validar `SameSite` y/o token anti-CSRF).
* **Estrategia de Rollback:** desactivar el feature flag → el frontend vuelve a `localStorage` + header Bearer, que el backend sigue aceptando durante la transición. Sin invalidar sesiones existentes.

---

### R-07 — Identidad de rate limit basada en header spoofable
* **Vulnerabilidad:** el límite de matching usa el header `X-User-ID` controlable por el cliente ([`rate_limiter.py:34`](../backend/app/core/rate_limiter.py#L34)).
* **Riesgo e Impacto:** evasión trivial del límite cambiando el header → abuso de un endpoint costoso.
* **Prioridad:** **Medio** (depende de R-02 para tener efecto).
* **Estrategia de Mitigación:** derivar la identidad del límite del **JWT validado** (claim `sub`), no de un header arbitrario. Si el middleware no valida JWT, mover la lógica de límite por usuario a una dependencia del router de matching que ya tiene el token verificado.
* **Estrategia de Validación:** test que envíe `X-User-ID` falsificado y confirme que el límite se aplica por usuario real del token; verificar que dos usuarios distintos no comparten cubeta.
* **Estrategia de Rollback:** desactivar vía `RATE_LIMIT_ENABLED` (mismo flag de R-02); revertir a la clave por IP si fuese necesario.

---

### R-08 — Generación de PDF síncrona dentro del request
* **Vulnerabilidad:** `download_cv` ejecuta WeasyPrint en el hilo del request ([`cv.py:79`](../backend/app/api/v1/cv.py#L79)).
* **Riesgo e Impacto:** agotamiento de recursos / bloqueo del event loop bajo carga (DoS) y degradación de toda la API.
* **Prioridad:** **Medio**.
* **Estrategia de Mitigación:** ya existe la tarea async `generate_cv_task` (cola `cv_generation`). Estrategia: servir la descarga desde el resultado de la tarea/almacenamiento en lugar de generar en el request. **Compatibilidad hacia atrás:** mantener el endpoint síncrono detrás de un flag para dev/testing mientras el flujo async se vuelve el predeterminado en producción, y proteger ambos con rate limit (R-02).
* **Estrategia de Validación:** prueba de carga comparando latencia/uso de CPU del flujo async vs síncrono; verificar que el PDF descargado sigue siendo válido (`%PDF-`, contenido coherente por `worker_type`).
* **Estrategia de Rollback:** reactivar el flag del endpoint síncrono; el código async ya existe y convive con el síncrono, por lo que no hay pérdida de capacidad.

---

### R-09 — Política de contraseñas débil y sin bloqueo de cuenta
* **Vulnerabilidad:** solo `min_length=8` sin complejidad ([`schemas/auth.py:9,46`](../backend/app/schemas/auth.py#L9)); defensa anti-fuerza-bruta solo por IP, sin bloqueo por cuenta ([`auth.py:111`](../backend/app/api/v1/auth.py#L111)).
* **Riesgo e Impacto:** credenciales débiles y credential stuffing distribuido (múltiples IP) no mitigado.
* **Prioridad:** **Medio**.
* **Estrategia de Mitigación:** (1) reforzar la política en `register`/`reset-password` (longitud + complejidad y/o verificación contra listas de filtradas), aplicada **solo a contraseñas nuevas** para no invalidar las vigentes; (2) añadir backoff/bloqueo temporal por cuenta (clave Redis por `user_id`) además del límite por IP. Dado el contexto institucional (baja alfabetización digital), calibrar la política para no degradar la UX de registro.
* **Estrategia de Validación:** tests de validación de contraseñas (acepta fuertes, rechaza débiles); test de bloqueo tras N fallos por cuenta; confirmar que usuarios existentes siguen pudiendo iniciar sesión.
* **Estrategia de Rollback:** la política nueva vive en el schema y una dependencia; revertir el schema restaura el comportamiento previo sin afectar cuentas existentes. El bloqueo por cuenta se desactiva quitando su flag.

---

### R-10 — Gestión de secretos fuera del código
* **Vulnerabilidad:** `AES_KEY` placeholder versionado ([`config.py:12`](../backend/app/core/config.py#L12)) y clave privada RSA en disco sin cifrar ([`security.py:46`](../backend/app/core/security.py#L46)).
* **Riesgo e Impacto:** si se opera sin sobreescribir secretos, PII y firma de tokens quedan comprometidas. Mitigado parcialmente por el validador que rechaza el placeholder en producción.
* **Prioridad:** **Medio**.
* **Estrategia de Mitigación:** integrar un gestor de secretos (vault / secret manager del proveedor) para `AES_KEY`, claves RSA y credenciales de BD; inyectarlos en runtime, nunca versionarlos. Mantener el validador existente como red de seguridad.
* **Estrategia de Validación:** confirmar arranque con secretos inyectados desde el gestor; verificar que `git` no contiene secretos reales (escaneo de secretos en CI).
* **Estrategia de Rollback:** los secretos se resuelven por variable de entorno; revertir a la fuente anterior es cambiar el origen de la variable. **Crítico:** una rotación de `AES_KEY` invalidaría PII ya cifrada → la rotación de esa clave requiere plan de re-cifrado y NO debe hacerse como simple rollback.

---

### R-11 — Build de frontend con `npm install` en runtime
* **Vulnerabilidad:** el servicio frontend ejecuta `npm install --legacy-peer-deps` al arrancar ([`docker-compose.yml:144`](../docker-compose.yml#L144)).
* **Riesgo e Impacto:** builds no reproducibles; riesgo de integridad de la cadena de suministro (A08).
* **Prioridad:** **Bajo-Medio**.
* **Estrategia de Mitigación:** usar `npm ci` sobre el `package-lock.json` en una imagen construida (multi-stage Dockerfile) en lugar de instalar en runtime. Mantener el modo dev con *hot reload* documentado aparte.
* **Estrategia de Validación:** build reproducible verificable (mismo lockfile → mismas versiones); arranque del frontend sin acceso de escritura a `node_modules`.
* **Estrategia de Rollback:** restaurar el comando del servicio en el compose; no afecta datos ni backend.

---

### R-12 — Token JWT del WebSocket en query string
* **Vulnerabilidad:** el WS recibe el token por `?token=...` ([`ws_notifications.py:19`](../backend/app/api/v1/ws_notifications.py#L19)), susceptible de quedar en logs.
* **Riesgo e Impacto:** fuga del token por logs de proxy/servidor.
* **Prioridad:** **Bajo**.
* **Estrategia de Mitigación:** transportar el token vía subprotocolo WebSocket (`Sec-WebSocket-Protocol`) o cookie `HttpOnly` (alineado con R-06), manteniendo compatibilidad temporal con el query param durante la transición del frontend.
* **Estrategia de Validación:** verificar autenticación del WS por el nuevo canal; confirmar que el token ya no aparece en logs de acceso.
* **Estrategia de Rollback:** reactivar la aceptación del query param (se mantiene durante la transición), sin cortar notificaciones en tiempo real.

---

### R-13 — Access token de larga vida sin refresh automático
* **Vulnerabilidad:** `ACCESS_TOKEN_EXPIRE_MINUTES=1440` (24 h) ([`config.py:28`](../backend/app/core/config.py#L28)); sin refresh automático en el cliente.
* **Riesgo e Impacto:** ventana amplia de uso de un token robado.
* **Prioridad:** **Bajo-Medio** (acoplado a R-06).
* **Estrategia de Mitigación:** reducir el TTL del access token e implementar rotación silenciosa del refresh token en el interceptor de Axios (el endpoint `/auth/refresh` ya existe y rota el `jti`). Desplegar el TTL reducido **después** de tener el refresh automático para no degradar la UX (evitar deslogueos frecuentes).
* **Estrategia de Validación:** E2E que verifique renovación transparente al expirar el access token; medir que no aumentan los deslogueos involuntarios.
* **Estrategia de Rollback:** restaurar `ACCESS_TOKEN_EXPIRE_MINUTES` al valor previo por variable de entorno (sin redeploy de código). El refresh automático es aditivo y desactivable.

---

### R-14 — Excepciones silenciadas y ausencia de alertado
* **Vulnerabilidad:** `except Exception: pass` en [`dashboard.py:35,42`](../backend/app/api/v1/admin/dashboard.py#L35) y [`rate_limiter.py:43`](../backend/app/core/rate_limiter.py#L43); eventos de seguridad sin alertas (A09).
* **Riesgo e Impacto:** incidentes invisibles; respuesta tardía.
* **Prioridad:** **Bajo-Medio**.
* **Estrategia de Mitigación:** reemplazar el `pass` por logging explícito del error (sin alterar el *fail-open* deliberado del rate limiter, que preserva disponibilidad); definir alertas sobre eventos de seguridad (picos de 401/403/429, `login_failed`) en el stack Prometheus/Grafana ya presente.
* **Estrategia de Validación:** forzar el fallo (p. ej. Redis caído) y confirmar que se loguea en vez de silenciarse; verificar que la alerta dispara ante umbral simulado.
* **Estrategia de Rollback:** el cambio es puramente observacional (logging/alertas); revertir no afecta el comportamiento funcional.

---

### R-15 — Vector de embedding concatenado en SQL (defensa en profundidad)
* **Vulnerabilidad:** en [`marketplace_service.py:173-182`](../backend/app/services/marketplace/marketplace_service.py#L173) el vector se concatena como string dentro del SQL. Valores numéricos del modelo → riesgo de inyección bajo, pero no parametrizado.
* **Riesgo e Impacto:** bajo hoy; mejora de robustez (consistencia de prepared statements).
* **Prioridad:** **Bajo**.
* **Estrategia de Mitigación:** pasar el literal del vector como parámetro vinculado en lugar de concatenarlo (alineado con el resto del código que ya parametriza).
* **Estrategia de Validación:** test de la búsqueda del marketplace que confirme resultados idénticos antes/después del cambio (no regresión funcional del ranking).
* **Estrategia de Rollback:** revertir a la consulta anterior; el resultado funcional es equivalente, sin impacto en datos.

---

### R-16 — SCA automatizado y configuración segura por defecto (proceso)
* **Vulnerabilidad:** ausencia de análisis de composición de software (SCA) en CI y configuración insegura por defecto (transversal a A05/A06).
* **Riesgo e Impacto:** reaparición de dependencias vulnerables y *drift* de configuración insegura.
* **Prioridad:** **Medio** (preventivo, evita reincidencia de R-01).
* **Estrategia de Mitigación:** añadir un *gate* de SCA al pipeline (escaneo de dependencias backend y frontend) que falle ante severidad Alta/Crítica; añadir escaneo de secretos y *linting* de configuración de contenedores. Integrar con SonarQube ya configurado en el proyecto.
* **Estrategia de Validación:** introducir intencionalmente una dependencia vulnerable en una rama de prueba y confirmar que el pipeline la bloquea.
* **Estrategia de Rollback:** desactivar el *gate* (modo advertencia) si genera fricción inicial, manteniendo el escaneo informativo. No afecta runtime de producción.

---

## Apéndice — Trazabilidad Hallazgo → Remediación

| OWASP | Hallazgo (informe 04) | Remediación |
|-------|------------------------|-------------|
| A01 | Seguro | — (mantener patrón; cubrir con R-16) |
| A02 | Tokens localStorage, secretos, WS token, TTL, RSA en disco | R-06, R-10, R-12, R-13 |
| A03 | Vector embedding concatenado | R-15 |
| A04 | Rate limit no montado, header spoofable, PDF síncrono | R-02, R-07, R-08 |
| A05 | Credenciales por defecto, Redis expuesto, AES placeholder | R-03, R-04, R-10 |
| A06 | `python-jose` / `python-multipart` con CVE | R-01, R-16 |
| A07 | Password policy, sin lockout, fallos no auditados | R-05, R-09 |
| A08 | `npm install` en runtime, integridad | R-11 |
| A09 | Fallos no auditados, `except: pass`, sin alertas | R-05, R-14 |
| A10 | Seguro | — |

---

*Plan de remediación táctico y estratégico. Cada ítem preserva la compatibilidad hacia atrás y define validación y rollback. Prioridad de ejecución: Fase 1 (R-01 a R-05) de inmediato; Fase 2 estructural; Fase 3 hardening. Recalibrar prioridades tras cada despliegue en `staging`.*
