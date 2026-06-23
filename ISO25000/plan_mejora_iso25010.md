# PLAN DE MEJORA INTEGRAL DE CALIDAD DE SOFTWARE
## Basado en Auditoría ISO/IEC 25010:2011 — Familia SQuaRE (ISO/IEC 25000)

---

| Campo | Detalle |
|---|---|
| **Sistema** | Linku — Sistema de Intermediación Laboral DRTPE-Junín |
| **Versión base auditada** | 0.2.0 (Sprint 5 — Rediseño UI "Andino") |
| **Fecha de elaboración del plan** | 2026-06-23 |
| **Referencia de auditoría** | `ISO25000/auditoria_iso25010.md` — Auditoría ISO/IEC 25010 (2026-06-23) |
| **Cumplimiento actual** | 76% (3.80 / 5.0) |
| **Cumplimiento objetivo** | ≥ 88% (4.40 / 5.0) |
| **Marco metodológico** | PDCA (Plan-Do-Check-Act) + ISO/IEC 25040 (proceso de evaluación) |
| **Horizonte del plan** | 12 meses (2026-07 → 2027-06) |

---

## 1. RESUMEN EJECUTIVO

### 1.1 Contexto y Propósito

El presente Plan de Mejora Integral se elabora como respuesta directa a los hallazgos de la Auditoría ISO/IEC 25010 realizada al sistema **Linku** el 23 de junio de 2026. El sistema obtuvo un cumplimiento general del **76%**, con fortalezas notables en Mantenibilidad (4.20/5), Portabilidad (4.33/5) y Seguridad de autenticación (5/5 en Confidencialidad), pero con brechas críticas en Seguridad de transmisión, completitud funcional y calidad de pruebas.

Se identificaron **15 no conformidades** (5 mayores + 10 menores) y **7 riesgos** (1 crítico, 3 altos, 3 medios). Este plan establece las acciones correctivas y preventivas necesarias para elevar el cumplimiento al **≥88%**, organizadas en un horizonte temporal de 12 meses bajo el ciclo PDCA.

### 1.2 Principales Problemas Identificados

| # | Problema | Impacto | NC Ref. |
|---|---|---|---|
| 1 | Nginx sin TLS: datos en tránsito no cifrados | **CRÍTICO** — fuga de PII de ciudadanos | NC-01 |
| 2 | SMTP no operativo: verificación de email y recuperación de contraseña inoperantes | **ALTO** — flujos de negocio incompletos | NC-02 |
| 3 | CV tipo `experiencia` siempre vacío de contenido | **ALTO** — producto principal defectuoso | NC-03 |
| 4 | `ml_score` fijo en 0.5: matching no usa modelo real | **ALTO** — valor diferencial del sistema no operativo | NC-04 |
| 5 | Claves RSA sin volumen persistente: pérdida al recrear contenedor | **ALTO** — sesiones inválidas masivas en redeploy | NC-05 |
| 6 | Content-Security-Policy (CSP) ausente | **MEDIO** — exposición a XSS | NC-06 |
| 7 | Sin refresh automático de token de acceso | **MEDIO** — interrupción abrupta de sesión | NC-07 |
| 8 | Desajuste de ruta NLP front vs. back (`INT-NLP`) | **MEDIO** — extracción de habilidades no funciona | NC-08 |
| 9 | Sin suite de pruebas de frontend | **MEDIO** — regressions no detectadas | NC-09 |
| 10 | Sin política de reinicio en servicios Docker | **MEDIO** — no hay auto-recuperación tras caída | NC-10 |

### 1.3 Acciones de Mayor Impacto

1. Configuración de TLS en Nginx (NC-01) → elimina el riesgo crítico de fuga de PII
2. Integración SMTP real (NC-02) → habilita flujos de negocio bloqueados
3. Corrección de bug `CV-EXP-VACIO` (NC-03) → restaura funcionalidad del producto CV para profesionales
4. Persistencia de claves RSA (NC-05) → garantiza continuidad de sesiones en deploys
5. Implementación de CSP (NC-06) → cierra la principal brecha de seguridad web
6. Suite de pruebas frontend con Vitest (NC-09) → previene regresiones en la UI

### 1.4 Beneficios Esperados

| Beneficio | Indicador | Valor actual | Valor objetivo |
|---|---|---|---|
| Cumplimiento ISO/IEC 25010 | % cumplimiento global | 76% | ≥ 88% |
| Seguridad de transmisión | Datos cifrados en tránsito | 0% | 100% |
| Completitud funcional | Flujos sin stubs | 60% | 90% |
| Cobertura de pruebas backend | % cobertura | Desconocida | ≥ 70% |
| Cobertura de pruebas frontend | % cobertura | 0% | ≥ 60% |
| Disponibilidad del servicio | Uptime mensual | Sin SLO | ≥ 99% |
| Precisión del matching | ml_score real vs stub | Stub (0.5) | Modelo entrenado |

### 1.5 Riesgos de No Implementar las Mejoras

| Riesgo | Consecuencia | Plazo de materialización |
|---|---|---|
| No configurar TLS (NC-01) | Multa por incumplimiento LPDP (Ley 29733 Perú) + fuga de DNI de ciudadanos | Inmediato en producción |
| No persistir claves RSA (NC-05) | Todos los usuarios forzados a re-login ante cada redeploy | Primer redeploy |
| No corregir CV-EXP-VACIO (NC-03) | Trabajadores profesionales reciben un CV en blanco | En uso actual |
| No implementar SMTP (NC-02) | Sistema de recuperación de contraseña inoperante | En uso actual |
| No entrenar modelo ML (NC-04) | El "matching inteligente" es equivalente a un orden aleatorio | Mediano plazo |

### 1.6 Incremento Esperado en Cumplimiento ISO/IEC 25010

```
Estado actual:     76%  ████████████████████████████████████████░░░░░░░░░░░░
Tras CP (3 meses): 84%  ████████████████████████████████████████████░░░░░░░░
Tras MP (6 meses): 88%  ██████████████████████████████████████████████░░░░░░
Tras LP (12 meses):92%  ████████████████████████████████████████████████░░░░
```

---

## 2. MARCO METODOLÓGICO — CICLO PDCA

```
┌─────────────────────────────────────────────────────────┐
│                     CICLO PDCA                          │
│                                                         │
│   PLANIFICAR ──────────────────► HACER                  │
│   (este documento)               (implementación        │
│   · Identificar NC               por sprints)           │
│   · Priorizar acciones                │                 │
│   · Definir indicadores               ▼                 │
│         ▲                       VERIFICAR               │
│         │                       · Métricas SMART        │
│         │                       · SonarQube             │
│         │                       · Cobertura tests       │
│   ACTUAR ◄──────────────────────· Re-auditoría          │
│   · Ajustar plan                · Dashboards            │
│   · Nuevas NC                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 3. MATRIZ DE PLAN DE MEJORA

> La matriz se organiza de mayor a menor prioridad dentro de cada plazo. Referencias: NC = No Conformidad de la auditoría; RF = Requisito Funcional del sistema.

---

### 3.1 ACCIONES DE CORTO PLAZO — 0 a 3 meses (Jul – Sep 2026)

| N° | Hallazgo (NC Ref.) | Característica ISO 25010 | Subcaracterística | Causa raíz | Impacto actual | Acción correctiva | Acción preventiva | Prioridad | Responsable sugerido | Recursos requeridos | Indicador SMART | Meta | Plazo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **PM-01** | NC-01 — Nginx sin TLS/HTTPS | Seguridad | Resistencia | Configuración de desarrollo usada en producción; ausencia de proceso de hardening pre-despliegue | CRÍTICO: datos de usuarios (DNI, nombre) viajan en texto plano entre cliente y servidor | 1. Obtener certificado TLS (Let's Encrypt gratuito o certificado institucional de Gobierno Regional Junín). 2. Modificar `nginx/nginx.conf`: añadir `listen 443 ssl`, `ssl_certificate`, `ssl_certificate_key`, redirección 301 de puerto 80 a 443. 3. Actualizar `ALLOWED_ORIGINS` con URL HTTPS. | Crear checklist de hardening pre-producción que incluya verificación TLS. Añadir health check que valide que el certificado no vence en < 30 días. | **ALTA** | DevOps / Líder técnico | Certbot (gratuito) o certificado institucional; 4h de trabajo | % de requests servidas sobre HTTPS = 100% en producción; certificado con validez ≥ 90 días | 100% HTTPS antes de primer despliegue a usuarios reales | Ago 2026 |
| **PM-02** | NC-05 — Claves RSA sin volumen persistente | Fiabilidad | Recuperabilidad | Las claves RSA se auto-generan en el directorio de trabajo del contenedor sin respaldo; al recrear el contenedor se pierden | ALTO: todas las sesiones activas se invalidan en cada redeploy; los usuarios deben volver a iniciar sesión | 1. Añadir en `docker-compose.yml`: `volumes: - ./backend/keys:/app/keys` para el servicio `api`. 2. Generar las claves RSA inicialmente con `docker-compose exec api python -c "from app.core.security import _ensure_rsa_keys; _ensure_rsa_keys()"` y verificar que se crearon en `./backend/keys/`. 3. Añadir `backend/keys/` a `.gitignore` (si no está ya). | Documentar el procedimiento de backup de claves RSA en el runbook. En producción, usar Docker Secrets o HashiCorp Vault para gestión de claves. | **ALTA** | Desarrollador backend | 2h de trabajo; Docker volume | Número de sesiones invalidadas por redeploy = 0; claves RSA presentes tras `docker-compose down && docker-compose up` | 0 pérdidas de sesión por redeploy | Jul 2026 |
| **PM-03** | NC-03 — CV tipo `experiencia` vacío (CV-EXP-VACIO) | Adecuación Funcional | Corrección funcional | `_build_template_context` en `pdf_generator.py:152-168` no cablea los datos retornados por `/nlp/parse-cv`; los campos `job_title`, `bio`, `years_experience`, experiencias y educación del `Worker` no se transfieren al contexto de la plantilla | ALTO: los trabajadores de tipo `experiencia` reciben un CV en blanco al descargar su documento, haciendo el producto inútil para este segmento | 1. Auditar `_build_template_context` para el tipo `experiencia`: leer `worker.bio`, `worker.job_title`, `worker.years_experience`. 2. Implementar consulta a `WizardProgress` o tabla de experiencia parseada para obtener `experiences`, `education` y `skills`. 3. Normalizar con `_norm_experiences` y `_norm_education` ya disponibles. 4. Añadir test unitario `test_cv_experiencia_context_not_empty`. | Añadir assertion en test que valide que el contexto de la plantilla `experiencia` contiene al menos `job_title` o `bio` no vacíos. Incluir en checklist de PR la revisión de contextos de plantilla. | **ALTA** | Desarrollador backend | 6h de trabajo | % de CVs tipo `experiencia` con contenido ≠ vacío = 100%; tamaño PDF > 5KB | 100% de CVs con contenido en < 30 días | Jul 2026 |
| **PM-04** | NC-08 — Desajuste ruta/payload NLP (INT-NLP) | Adecuación Funcional | Corrección funcional | El frontend llama `POST /nlp/extract-skills` pero el backend expone `POST /nlp/extract-skills/wizard` con un payload diferente; divergencia entre la especificación del contrato API y la implementación del cliente | ALTO: la extracción de habilidades NLP del wizard (Step 3) no funciona, bloqueando el flujo central de `primer_empleo` | 1. Verificar en `frontend/src/modules/primer-empleo/wizard/steps/Step3*.tsx` la URL y el payload exactos. 2. Verificar en `backend/app/api/v1/nlp.py` los endpoints disponibles. 3. Corregir el lado que diverge (preferiblemente el frontend para no romper el contrato de API). 4. Añadir test de integración `test_api_nlp.py::test_extract_skills_wizard_step3`. | Implementar contrato API con OpenAPI y validarlo contra el cliente con `openapi-typescript-codegen` o similar. | **ALTA** | Fullstack developer | 3h de diagnóstico + 2h de corrección | Tasa de éxito de llamadas a `/nlp/extract-skills/*` desde el wizard = 100% (sin errores 404/422 en logs) | 0 errores 404/422 en flujo wizard | Jul 2026 |
| **PM-05** | NC-02 — SMTP no configurado | Adecuación Funcional | Completitud funcional | No se configuró un servidor de correo real; las tareas Celery de notificación son stubs que solo loguean | ALTO: verificación de email inoperante; recuperación de contraseña imposible; notificaciones de postulación mudas | 1. Configurar proveedor SMTP: SendGrid (gratuito hasta 100 correos/día) o servidor SMTP institucional del Gobierno Regional Junín. 2. Añadir variables en `backend/.env`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`. 3. Implementar envío real en `tasks/notifications.py:send_reset_email` usando `aiosmtplib`. 4. Añadir test con `aioresponses` para mock SMTP. | Usar servicio SMTP con monitoreo de entrega (SendGrid tiene dashboard de bounces). Definir plantillas de email en HTML. | **ALTA** | Desarrollador backend | 8h de trabajo; cuenta SMTP (gratuita o institucional) | % de emails transaccionales entregados ≥ 95%; tiempo de entrega < 30 segundos | 95% de entrega de emails en producción | Ago 2026 |
| **PM-06** | NC-06 — Content-Security-Policy ausente | Seguridad | Autenticidad | `SecurityHeadersMiddleware` no incluye el header CSP; no se definió la política de fuentes permitidas | MEDIO-ALTO: ausencia de la defensa principal contra ataques XSS; un atacante podría inyectar scripts en la UI | 1. Añadir en `security_headers.py` el header `Content-Security-Policy` con política restrictiva: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'`. 2. Ajustar para Three.js (KPIGlobe) si requiere `unsafe-eval`. 3. Verificar en el frontend que no haya `eval()` ni inline scripts que rompan la política. | Ejecutar `npm audit` y `eslint` con reglas de seguridad para detectar patrones XSS en el frontend. Añadir escaneo DAST (OWASP ZAP) en CI. | **ALTA** | Desarrollador backend / Seguridad | 4h de implementación + 2h de pruebas | 100% de respuestas HTTP incluyen `Content-Security-Policy`; 0 violaciones CSP en consola de navegador en flujo normal | 100% de respuestas con CSP válido; 0 violaciones en producción | Ago 2026 |
| **PM-07** | NC-10 — Sin política de reinicio Docker | Fiabilidad | Disponibilidad | `docker-compose.yml` no define `restart: unless-stopped`; los servicios no se recuperan automáticamente tras un crash o reinicio del host | MEDIO: una caída del SO o del daemon Docker deja el sistema inaccesible hasta intervención manual | Añadir a los servicios críticos en `docker-compose.yml`: `restart: unless-stopped` para `api`, `db`, `redis`, `worker-*`, `celery-beat`, `nginx`. Excepcionar `sonarqube` y `flower` (herramientas de dev). | Implementar monitoreo de uptime (UptimeRobot gratuito o Prometheus Alertmanager) que notifique caídas. | **ALTA** | DevOps | 1h de trabajo | Uptime mensual del servicio `api` ≥ 99%; tiempo de recuperación automática < 60 segundos | Uptime ≥ 99% medido mensualmente | Jul 2026 |
| **PM-08** | NC-11 — Hotspot SONAR-2 en `portfolio.py:320` | Seguridad | Integridad | Directorio de almacenamiento configurable sin validación del path — posible directory traversal o escritura en rutas no autorizadas | MEDIO: un atacante podría manipular el path de almacenamiento para acceder o escribir en directorios no previstos | 1. Revisar `api/v1/portfolio.py:320`: identificar qué directorio se escribe. 2. Validar que el path resultante está dentro del directorio base permitido (`BASE_UPLOAD_DIR`). 3. Usar `Path.resolve()` y verificar que `.is_relative_to(BASE_DIR)`. 4. Reemplazar directorio escribible por llamada al servicio `storage.py` (GCS o storage abstraction). | Añadir `bandit` al pipeline de CI para análisis de seguridad estático en Python. Configurar regla en SonarQube para fallar el Quality Gate ante hotspots de seguridad no revisados. | **ALTA** | Desarrollador backend / Seguridad | 3h de análisis + 2h de corrección | SonarQube: hotspot SONAR-2 en estado "Resuelto" o "Falso positivo documentado"; 0 vulnerabilidades nuevas de path traversal | 0 hotspots sin resolver en SonarQube | Ago 2026 |
| **PM-09** | NC-14 — Contraseña Grafana por defecto | Seguridad | Resistencia | El archivo `docker-compose.yml` define `GF_SECURITY_ADMIN_PASSWORD: changeme` — credencial trivial y pública en el repositorio | MEDIO: acceso no autorizado al panel de métricas; posible obtención de información sobre el sistema productivo | 1. Cambiar `GF_SECURITY_ADMIN_PASSWORD` en `docker-compose.staging.yml` y en producción a una contraseña segura (≥16 chars, aleatoria). 2. En dev, dejar `changeme` solo explicitando que es solo para desarrollo local. 3. Usar variables de entorno (no hardcoded en compose): `GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}`. | Añadir pre-commit hook que detecte contraseñas conocidas débiles en archivos de configuración. Usar `detect-secrets` en CI. | **ALTA** | DevOps | 1h de trabajo | 0 contraseñas por defecto en entornos staging/prod; credenciales Grafana no en repositorio | 0 contraseñas triviales en prod | Jul 2026 |
| **PM-10** | NC-13 — Enumeración de usuarios via `/register` | Seguridad | Resistencia | El endpoint `POST /auth/register` retorna HTTP 409 cuando el email ya existe, revelando si un email está registrado | MEDIO: un atacante puede enumerar qué emails tienen cuenta; viola privacidad de usuarios y facilita ataques dirigidos | 1. Cambiar la respuesta HTTP 409 a 200 con un mensaje genérico: `"Si el email no está registrado, recibirás un correo de confirmación"`. 2. Enviar el email de verificación solo si el usuario es nuevo (flujo silencioso). 3. Mantener el log interno de intentos de re-registro para auditoría. | Documentar este patrón en el estándar de diseño de API del proyecto. Revisarlo en todos los endpoints de recuperación de identidad. | **MEDIA** | Desarrollador backend | 2h de trabajo | 0 respuestas HTTP 409 en `/register` en producción; respuesta genérica verificada con test | Respuesta genérica implementada y probada | Sep 2026 |

---

### 3.2 ACCIONES DE MEDIANO PLAZO — 3 a 6 meses (Oct 2026 – Dic 2026)

| N° | Hallazgo (NC Ref.) | Característica ISO 25010 | Subcaracterística | Causa raíz | Impacto actual | Acción correctiva | Acción preventiva | Prioridad | Responsable sugerido | Recursos requeridos | Indicador SMART | Meta | Plazo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **PM-11** | NC-07 — Sin refresh automático de access token | Usabilidad | Operabilidad | El interceptor Axios en `api/client.ts` no implementa lógica de refresh; al recibir un 401, limpia la sesión sin intentar renovar el token primero | MEDIO: usuarios activos son deslogueados abruptamente al expirar el token de 24h; interrumpe flujos largos (ej. completar el wizard) | 1. En `api/client.ts`, añadir interceptor de respuesta que detecte 401 y llame a `POST /auth/refresh` con el `refresh_token` del localStorage. 2. Si el refresh tiene éxito, reintentar la request original con el nuevo token. 3. Si el refresh falla (token expirado o revocado), entonces sí limpiar sesión y redirigir a `/login`. 4. Mostrar un banner de advertencia 5 minutos antes de la expiración. | Configurar `ACCESS_TOKEN_EXPIRE_MINUTES` a 60 min (en lugar de 1440) para reducir la ventana de exposición de tokens; el refresh automático compensa la experiencia de usuario. | **ALTA** | Desarrollador frontend | 8h de trabajo | Número de sesiones terminadas abruptamente por token expirado = 0 medido en logs de Axios; tasa de refresh exitoso ≥ 95% | 0 cierres abruptos de sesión por token expirado en usuarios activos | Nov 2026 |
| **PM-12** | NC-15 — `/cv/download` síncrono y bloqueante | Eficiencia del Desempeño | Comportamiento temporal | La generación PDF con WeasyPrint se ejecuta directamente en el request HTTP en lugar de usar la tarea Celery `generate_cv_task` ya existente | MEDIO: bajo carga concurrente, los requests de generación de CV pueden agotar el pool de workers Uvicorn y generar timeouts | 1. Modificar `GET /cv/download/{worker_id}` para delegar a `generate_cv_task.delay(worker_id)` y esperar el resultado con `AsyncResult.get(timeout=30)`, o mejor aún: 2. Implementar flujo poll: `POST /cv/generate/{id}` → `{task_id}`, luego `GET /cv/status/{task_id}` → cuando `DONE`, `GET /cv/download/{id}` sirve desde storage (GCS o volume local). 3. Cachear el PDF en Redis/storage por 1 hora. | Añadir SLO documentado: generación de CV ≤ 10 segundos P95. Configurar alerta en Grafana cuando el tiempo de respuesta de `/cv/*` supere 5 segundos. | **ALTA** | Desarrollador backend | 12h de trabajo | Tiempo de respuesta P95 de `/cv/download` ≤ 10 segundos con 10 usuarios concurrentes; tasa de error < 1% | P95 ≤ 10s con 10 usuarios concurrentes | Nov 2026 |
| **PM-13** | NC-09 — Sin suite de pruebas de frontend | Mantenibilidad | Capacidad de ser probado | El `package.json` no incluye Vitest, Jest ni React Testing Library; no existe ningún archivo de test en `frontend/src/` | MEDIO: los cambios en componentes React no se validan automáticamente; las regresiones se detectan solo en pruebas manuales | 1. Instalar: `npm install -D vitest @vitest/ui @testing-library/react @testing-library/user-event jsdom`. 2. Configurar `vitest.config.ts` con `environment: 'jsdom'`. 3. Añadir script `"test": "vitest"` y `"test:coverage": "vitest --coverage"` en `package.json`. 4. Implementar pruebas iniciales para: `LoginPage` (formulario, submit, error), `AuthGuard` (redirección sin token), `WizardStep1` (validación), `MatchesPage` (render con mocks). | Añadir `vitest` a pre-commit hooks para ejecutar tests afectados antes de cada commit. Integrar `"test:coverage"` en el pipeline CI. | **ALTA** | Desarrollador frontend | 16h de trabajo (setup + tests iniciales) | Cobertura de pruebas frontend ≥ 60% en componentes clave (`LoginPage`, `AuthGuard`, `WizardLayout`, `MatchesPage`); 0 regresiones en rutas de navegación | ≥ 60% cobertura en < 90 días desde inicio | Dic 2026 |
| **PM-14** | NC-12 — Sin pruebas de accesibilidad WCAG | Usabilidad | Accesibilidad | No se ejecutaron pruebas de accesibilidad automatizadas ni manuales; el público objetivo incluye personas con baja alfabetización digital y posiblemente adultos mayores | MEDIO: la aplicación puede ser inutilizable para usuarios con discapacidades visuales o motrices; riesgo de exclusión de la población objetivo | 1. Integrar `axe-core` en Vitest: `npm install -D @axe-core/react`. 2. Ejecutar análisis de accesibilidad en Lighthouse CI para las rutas principales. 3. Corregir los hallazgos de alta severidad: contraste de color, etiquetas de formulario, orden de tabulación. 4. Verificar que `Fraunces` (display) tenga tamaño mínimo 16px en texto de cuerpo. | Establecer como criterio de aceptación de PR que el score Lighthouse Accessibility ≥ 85. Incluir revisión manual con lectores de pantalla (NVDA en Windows) para flujos críticos. | **MEDIA** | Desarrollador frontend / UX | 12h de trabajo | Score Lighthouse Accessibility ≥ 85 en `/login`, `/wizard`, `/dashboard`; 0 violaciones axe-core de severidad "critical" o "serious" | Score ≥ 85 en rutas críticas | Dic 2026 |
| **PM-15** | Ausencia de índices en columnas de búsqueda frecuente | Eficiencia del Desempeño | Utilización de recursos | Las migraciones Alembic no definen índices explícitos en columnas de alta cardinalidad usadas en WHERE y JOIN frecuentes | MEDIO: las consultas de matching y búsqueda de ofertas hacen full-table-scans en tablas que crecerán con el uso | 1. Generar migración Alembic: `alembic revision -m "add_performance_indexes"`. 2. Añadir índices: `Index('ix_job_offers_active_district', 'is_active', 'district', 'worker_type_target')`, `Index('ix_workers_type_available', 'worker_type', 'is_available')`, `Index('ix_applications_worker_status', 'worker_id', 'status')`. 3. Configurar pool de conexiones en `create_async_engine`: `pool_size=10, max_overflow=20`. | Usar `EXPLAIN ANALYZE` en queries de matching después de cada migración. Añadir query de análisis de performance en el runbook. | **MEDIA** | Desarrollador backend / DBA | 4h de trabajo | Tiempo de respuesta P95 de `GET /match/{worker_id}` ≤ 500ms con 1000 ofertas activas en BD | P95 ≤ 500ms de latencia de matching | Oct 2026 |
| **PM-16** | Cobertura de pruebas backend no medida | Mantenibilidad | Capacidad de ser probado | `coverage.xml` no se genera en el flujo normal de desarrollo; no existe pipeline CI/CD que mida y reporte la cobertura | MEDIO: no se conoce qué porcentaje del código está cubierto; bugs en rutas no testeadas pueden pasar a producción | 1. Ejecutar: `docker-compose exec api pytest --cov=app --cov-report=xml --cov-report=term-missing`. 2. Revisar el reporte e identificar módulos con < 50% de cobertura. 3. Añadir tests para los módulos críticos no cubiertos: `services/cv_builder/`, `ml/matching_engine/`, `nlp/embeddings/`. 4. Añadir step en CI: `pytest --cov=app --cov-fail-under=70`. | Configurar SonarQube para bloquear el Quality Gate si la cobertura cae por debajo del umbral. Revisar cobertura en cada PR. | **MEDIA** | Desarrollador backend / QA | 20h de trabajo (generar reporte + añadir tests) | Cobertura de código backend ≥ 70% medida en SonarQube; 0 módulos críticos con cobertura < 50% | ≥ 70% cobertura total backend | Nov 2026 |
| **PM-17** | Sin circuit breaker para dependencias externas | Fiabilidad | Tolerancia a fallos | Las llamadas a DRTPE y GCS no tienen reintentos ni circuit breaker; un fallo en estos servicios propaga errores 500 sin degradación elegante | BAJO-MEDIO: interrupciones de servicios externos generan errores no controlados para el usuario | 1. Instalar `tenacity` (ya puede estar en el entorno). 2. Envolver las llamadas a `integrations/drtpe/` y `services/storage.py` con decorador `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))`. 3. Implementar respuesta de degradación elegante: si DRTPE no responde, retornar últimos datos cacheados en Redis (TTL 1h). | Añadir health check de DRTPE y GCS en el endpoint `/api/v1/health`. Configurar alerta en Prometheus cuando la tasa de errores en integraciones externas supere 5%. | **MEDIA** | Desarrollador backend | 6h de trabajo | Tasa de errores 5xx causados por servicios externos < 1%; tiempo de recuperación tras fallo de DRTPE < 5 segundos (con datos cacheados) | < 1% de errores por servicios externos | Nov 2026 |
| **PM-18** | Mensajes de error técnicos expuestos en frontend | Usabilidad | Capacidad de aprendizaje | El interceptor Axios y los componentes muestran los mensajes de error crudos del backend (ej. "422 Unprocessable Entity", "detail: string expected") sin adaptación para el usuario | MEDIO: un usuario con baja alfabetización digital no comprende los mensajes técnicos; abandona el flujo | 1. Crear un mapa de errores en `api/client.ts`: `{ 422: "Por favor verifica que todos los campos estén completos", 401: "Tu sesión ha expirado", 500: "Ocurrió un error inesperado. Intenta más tarde" }`. 2. Usar `react-intl` para internacionalizar los mensajes. 3. En cada componente, mostrar el mensaje mapeado en lugar del error crudo. | Revisar todos los `catch` y `error` states del frontend para garantizar mensajes en lenguaje llano. Añadir prueba: ningún mensaje de error debe contener códigos HTTP o stacktraces. | **MEDIA** | Desarrollador frontend / UX | 8h de trabajo | 0 mensajes de error HTTP crudos (422, 500, etc.) visibles al usuario en la UI en pruebas de usabilidad | 0 mensajes técnicos visibles en producción | Oct 2026 |

---

### 3.3 ACCIONES DE LARGO PLAZO — 6 a 12 meses (Ene 2027 – Jun 2027)

| N° | Hallazgo (NC Ref.) | Característica ISO 25010 | Subcaracterística | Causa raíz | Impacto actual | Acción correctiva | Acción preventiva | Prioridad | Responsable sugerido | Recursos requeridos | Indicador SMART | Meta | Plazo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **PM-19** | NC-04 — `ml_score` fijo en 0.5 (stub) | Adecuación Funcional | Corrección funcional | El modelo ML supervisado de matching no ha sido entrenado; se usa un valor fijo como placeholder; la similitud coseno (pgvector) es el único componente real del score | ALTO (estratégico): el valor diferencial del sistema (matching inteligente basado en ML) no está operativo; el ranking equivale a similitud semántica sin aprendizaje de preferencias | 1. Diseñar dataset de entrenamiento: exportar `match_event` + `applications` con `status` para obtener pares (worker, job_offer, label:aceptado/rechazado). 2. Entrenar modelo de clasificación binaria (XGBoost o LightGBM) usando features: cosine_sim, district_match, salary_match, years_experience_delta. 3. Serializar con joblib, versionar con MLflow. 4. Cargar en `ml/matching_engine/scorer.py` reemplazando el stub 0.5. 5. Configurar reentrenamiento semanal en Celery Beat (lunes 04:00 ya configurado). | Monitorear drift del modelo con PSI (Population Stability Index) — `test_psi_drift_detector.py` ya existe. Documentar política de reentrenamiento. | **ALTA** | Data Scientist / Desarrollador ML | 40h de trabajo; dataset histórico de al menos 500 postulaciones | F1-score del modelo ≥ 0.70 en conjunto de validación; `ml_score` ≠ 0.5 en respuestas de `/match`; mejora en tasa de postulación exitosa ≥ 15% | F1 ≥ 0.70; deployment en producción | Mar 2027 |
| **PM-20** | Sin documentación de arquitectura formal | Mantenibilidad | Analizabilidad | El conocimiento de arquitectura está concentrado en `CLAUDE.md` (formato informal); no hay diagrama C4 ni ADRs (Architecture Decision Records) | MEDIO: incorporación de nuevos desarrolladores es lenta; cambios arquitecturales no se documentan formalmente | 1. Crear diagrama C4 nivel 1 (Context) y nivel 2 (Container) usando PlantUML o draw.io. 2. Documentar ADRs para decisiones clave: JWT RS256, AES-256-GCM, pgvector, worker_type diferenciación. 3. Publicar en `docs/arquitectura/`. | Establecer proceso de ADR para toda decisión técnica nueva (plantilla en `docs/adr/template.md`). | **MEDIA** | Arquitecto / Líder técnico | 16h de trabajo | Documentación de arquitectura revisada y aprobada por el equipo; 100% de decisiones técnicas mayores con ADR desde la implementación del proceso | Diagrama C4 publicado; 3 ADRs iniciales | Feb 2027 |
| **PM-21** | Sin backup automatizado de PostgreSQL | Fiabilidad | Recuperabilidad | No hay tarea Celery ni script que realice backups periódicos de la BD; un fallo del volumen Docker resultaría en pérdida de datos de ciudadanos | ALTO: pérdida irreversible de datos de trabajadores y postulaciones ante fallo de almacenamiento | 1. Crear tarea Celery `backup_database` en cola `reports` con `pg_dump` a GCS. 2. Configurar en Beat: `backup: cron(0, 2, '*', '*', '*')` — diario a las 02:00 AM. 3. Verificar backup con restore test mensual en entorno de staging. 4. Retención: 30 días de backups diarios. | Configurar alerta en Prometheus si el backup no se ejecuta en 25 horas. Documentar RTO/RPO: RTO ≤ 4h, RPO ≤ 24h. | **ALTA** | DevOps / Backend | 8h de trabajo; GCS bucket | Backup diario ejecutado exitosamente = 100% (medido en Celery Flower); test de restore exitoso mensual = 100% | 100% de backups exitosos; restore < 4h | Feb 2027 |
| **PM-22** | Pruebas de carga no ejecutadas | Eficiencia del Desempeño | Capacidad | No existe evidencia de pruebas de carga ni definición de SLOs; el sistema no ha sido validado bajo uso concurrente | MEDIO: el sistema puede degradarse o fallar ante la carga real de usuarios DRTPE-Junín | 1. Instalar `locust`: `pip install locust`. 2. Crear escenario de carga: 50 usuarios concurrentes realizando login + búsqueda de ofertas + matching durante 10 minutos. 3. Documentar SLOs: API latencia P95 ≤ 500ms, error rate < 1%, matching ≤ 2s. 4. Ejecutar en entorno staging antes del despliegue a producción. | Integrar prueba de carga ligera (smoke test) en pipeline CI: 5 usuarios, 60 segundos, falla si error rate > 5%. | **MEDIA** | QA / DevOps | 16h de trabajo; entorno staging | Resultados de prueba de carga documentados: P95 ≤ 500ms bajo 50 usuarios concurrentes; error rate < 1% | Prueba exitosa con 50 usuarios concurrentes | Abr 2027 |
| **PM-23** | Pruebas de usabilidad con usuarios reales | Usabilidad | Capacidad para reconocer adecuación | El sistema fue diseñado para baja alfabetización digital pero no ha sido validado con el público objetivo real (trabajadores informales de Huancayo) | MEDIO: la UX puede ser inadecuada para el perfil de usuario real a pesar del diseño orientado al contexto | 1. Coordinar con DRTPE-Junín: sesión de prueba con 10 usuarios reales (mix: trabajador primer empleo, artesano, profesional). 2. Registrar tiempo en tarea (Time on Task) para flujos clave: registro → onboarding → primer paso del wizard → descarga de CV. 3. Medir SUS (System Usability Scale, escala 0-100). 4. Implementar mejoras basadas en hallazgos. | Establecer ciclo de pruebas de usabilidad semestrales como parte del proceso de mejora continua. | **MEDIA** | UX Researcher / Coordinación DRTPE | 24h de trabajo; coordinación institucional | SUS score ≥ 70 (Good en escala de Bangor); Time on Task para registro completo ≤ 10 minutos; tasa de completitud del wizard ≥ 80% | SUS ≥ 70; completitud wizard ≥ 80% | May 2027 |
| **PM-24** | RBAC granular no implementado para rol MODERATOR | Seguridad | Responsabilidad | El rol `MODERATOR` está definido en el enum `UserRole` pero no tiene endpoints ni permisos diferenciados implementados; sus capacidades son equivalentes a `WORKER` | BAJO: el rol existe pero no agrega valor; puede confundir la gestión de accesos | 1. Definir el alcance del rol MODERATOR: revisión de portafolios públicos, gestión de contenido inapropiado, moderación del marketplace. 2. Crear endpoints dedicados en `admin/` con `require_role(UserRole.MODERATOR, UserRole.ADMIN)`. 3. Añadir interfaz en `AdminLayout` para moderadores. | Documentar la política de control de acceso en el ADR de seguridad. | **BAJA** | Desarrollador backend | 16h de trabajo | 100% de funciones de moderación solo accesibles por MODERATOR o ADMIN; 0 accesos no autorizados en audit log | RBAC completo implementado y probado | Jun 2027 |

---

## 4. CRONOGRAMA DE IMPLEMENTACIÓN

### 4.1 Diagrama de Gantt por Plazo

```
ACCIÓN      | Jul26 | Ago26 | Sep26 | Oct26 | Nov26 | Dic26 | Ene27 | Feb27 | Mar27 | Abr27 | May27 | Jun27
------------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------
PM-01 TLS   | ████  | ░░░░  |       |       |       |       |       |       |       |       |       |
PM-02 RSA   | ████  |       |       |       |       |       |       |       |       |       |       |
PM-03 CV-EXP| ████  |       |       |       |       |       |       |       |       |       |       |
PM-04 NLP   | ████  |       |       |       |       |       |       |       |       |       |       |
PM-05 SMTP  |       | ████  | ░░░░  |       |       |       |       |       |       |       |       |
PM-06 CSP   |       | ████  |       |       |       |       |       |       |       |       |       |
PM-07 Restart| ████ |       |       |       |       |       |       |       |       |       |       |
PM-08 SONAR2|       | ████  |       |       |       |       |       |       |       |       |       |
PM-09 Grafana| ████ |       |       |       |       |       |       |       |       |       |       |
PM-10 Enum  |       |       | ████  |       |       |       |       |       |       |       |       |
PM-11 Refresh|      |       |       | ████  | ████  |       |       |       |       |       |       |
PM-12 CV-Async|     |       |       | ████  | ████  |       |       |       |       |       |       |
PM-13 Test FE|      |       |       | ████  | ████  | ████  |       |       |       |       |       |
PM-14 WCAG  |       |       |       |       | ████  | ████  |       |       |       |       |       |
PM-15 Índices|      |       |       | ████  |       |       |       |       |       |       |       |
PM-16 Cob.BE|       |       |       |       | ████  | ████  |       |       |       |       |       |
PM-17 Circuit|      |       |       |       | ████  |       |       |       |       |       |       |
PM-18 Mensaj|       |       |       | ████  |       |       |       |       |       |       |       |
PM-19 ML    |       |       |       |       |       |       | ████  | ████  | ████  |       |       |
PM-20 Docs  |       |       |       |       |       |       | ████  | ████  |       |       |       |
PM-21 Backup|       |       |       |       |       |       | ████  | ████  |       |       |       |
PM-22 Carga |       |       |       |       |       |       |       |       | ████  | ████  |       |
PM-23 Usab. |       |       |       |       |       |       |       |       |       | ████  | ████  |
PM-24 RBAC  |       |       |       |       |       |       |       |       |       |       | ████  | ████

Leyenda: ████ = trabajo activo  ░░░░ = verificación/ajuste
```

### 4.2 Hitos Clave

| Hito | Fecha | Descripción | Criterio de aceptación |
|---|---|---|---|
| **H1 — Sistema seguro para despliegue** | 31 Ago 2026 | TLS, RSA persistente, SMTP, CSP, restart policy | PM-01, PM-02, PM-05, PM-06, PM-07 completados y verificados |
| **H2 — Funcionalidad completa** | 30 Sep 2026 | CV experiencia, NLP correcto, sin enumeración | PM-03, PM-04, PM-10 completados |
| **H3 — Calidad de pruebas** | 31 Dic 2026 | Tests frontend, cobertura backend ≥ 70%, WCAG | PM-13, PM-14, PM-16 completados |
| **H4 — Performance y resiliencia** | 28 Feb 2027 | Refresh token, CV async, backups, circuit breaker | PM-11, PM-12, PM-17, PM-21 completados |
| **H5 — ML operativo** | 31 Mar 2027 | Modelo ML entrenado con F1 ≥ 0.70 | PM-19 completado |
| **H6 — Validación con usuarios reales** | 31 May 2027 | SUS ≥ 70, pruebas de carga exitosas | PM-22, PM-23 completados |
| **H7 — Auditoría de cierre** | 30 Jun 2027 | Re-auditoría ISO/IEC 25010 con cumplimiento ≥ 88% | Nueva auditoría formal con todos los PMs verificados |

---

## 5. INDICADORES SMART CONSOLIDADOS

### 5.1 Dashboard de Seguimiento del Plan de Mejora

| ID | Indicador | Fórmula de medición | Herramienta | Frecuencia | Línea base actual | Meta |
|---|---|---|---|---|---|---|
| KPI-01 | Cumplimiento ISO 25010 global | Promedio ponderado de subcaracterísticas evaluadas | Re-auditoría manual | Semestral | 76% | ≥ 88% |
| KPI-02 | % requests HTTPS | (Requests HTTPS / Total requests) × 100 | Nginx logs + Grafana | Diaria | 0% | 100% |
| KPI-03 | Tasa de entrega de emails | (Emails entregados / Emails enviados) × 100 | Proveedor SMTP | Semanal | 0% | ≥ 95% |
| KPI-04 | CVs con contenido válido (tipo experiencia) | (CVs con tamaño > 5KB / Total CVs tipo experiencia) × 100 | Logs de cv.py | Por sprint | 0% | 100% |
| KPI-05 | Cobertura de pruebas backend | % líneas cubiertas en SonarQube | SonarQube + pytest-cov | Semanal (CI) | Desconocida | ≥ 70% |
| KPI-06 | Cobertura de pruebas frontend | % líneas cubiertas en Vitest | Vitest coverage | Semanal (CI) | 0% | ≥ 60% |
| KPI-07 | Latencia API P95 | P95 de `http_request_duration_seconds` | Grafana / Prometheus | Continua | Sin SLO | ≤ 500ms |
| KPI-08 | Latencia matching P95 | P95 de `GET /match/*` | Grafana | Continua | Sin SLO | ≤ 2000ms |
| KPI-09 | Uptime mensual API | (Minutos UP / Total minutos mes) × 100 | Prometheus + UptimeRobot | Mensual | Sin SLO | ≥ 99% |
| KPI-10 | Score Lighthouse Accesibilidad | Puntuación 0-100 en rutas críticas | Lighthouse CI | Por sprint | Desconocida | ≥ 85 |
| KPI-11 | SUS (System Usability Scale) | Promedio de 10 preguntas escala Likert × usuarios | Test con usuarios reales | Semestral | Sin línea base | ≥ 70 |
| KPI-12 | F1-score del modelo ML | F1 en conjunto de validación | MLflow experiments | Por entrenamiento | N/A (stub) | ≥ 0.70 |
| KPI-13 | Hotspots de seguridad en SonarQube | Número de hotspots no revisados | SonarQube | Semanal | 1 (SONAR-2) | 0 |
| KPI-14 | No conformidades abiertas | Número de NCs del plan sin cerrar | Este documento | Mensual | 15 | 0 al final del plan |
| KPI-15 | Backups exitosos | (Backups completados / Backups programados) × 100 | Celery Flower | Diaria | 0% | 100% |
| KPI-16 | Sesiones interrumpidas por token expirado | Conteo de 401 en requests autenticados sin refresh | Structlog / Grafana | Semanal | Sin medición | 0 |
| KPI-17 | Errores NLP en wizard Step 3 | Conteo de 404/422 en `/nlp/extract-skills/*` | Nginx logs | Por sprint | Sin medición | 0 |

---

## 6. MATRIZ DE RIESGOS DEL PLAN DE MEJORA

> Riesgos que pueden impedir la implementación exitosa de este plan.

| Riesgo del plan | Probabilidad | Impacto | Acciones de mitigación |
|---|---|---|---|
| Falta de recursos humanos dedicados al plan | Media | Alto | Priorizar PM-01 a PM-10 como bloqueantes; los demás como mejora continua |
| Dificultad para obtener certificado TLS institucional | Media | Alto | Usar Let's Encrypt como alternativa gratuita y automática |
| Dataset insuficiente para entrenar modelo ML (PM-19) | Alta | Medio | Usar técnicas de data augmentation; postergar si hay < 200 postulaciones históricas |
| Resistencia al cambio en procesos DRTPE para integración SMTP | Media | Medio | Usar SendGrid o Mailgun como alternativa sin dependencia de TI institucional |
| Falta de coordinación con DRTPE para pruebas de usuario (PM-23) | Media | Medio | Planificar con 2 meses de anticipación; tener lista alternativa con usuarios del campus universitario |
| Aumento del scope durante implementación | Alta | Medio | Aplicar timeboxing estricto por sprint; cualquier nueva NC espera la próxima iteración del plan |

---

## 7. ESTRUCTURA DE GOBERNANZA DEL PLAN

### 7.1 Roles y Responsabilidades

| Rol | Responsabilidad en el plan |
|---|---|
| **Responsable del Plan (Plan Owner)** | Supervisar el avance global; aprobar cambios de prioridad; reportar a DRTPE-Junín |
| **Líder Técnico Backend** | Responsable de PM-01, PM-02, PM-03, PM-05, PM-06, PM-07, PM-08, PM-10, PM-15, PM-17, PM-21 |
| **Desarrollador Frontend** | Responsable de PM-11, PM-13, PM-14, PM-18 |
| **Data Scientist / ML Engineer** | Responsable de PM-19; apoyo en PM-15 |
| **DevOps / Infraestructura** | Responsable de PM-01 (Nginx), PM-07, PM-22 |
| **QA / Calidad** | Responsable de medición de KPIs, ejecución de pruebas, validación de criterios de aceptación |
| **Coordinador DRTPE** | Facilitación de PM-23 (pruebas con usuarios reales); aprobación de PM-20 (arquitectura) |

### 7.2 Frecuencia de Revisión

| Revisión | Frecuencia | Participantes | Entregable |
|---|---|---|---|
| **Sprint Review del Plan** | Mensual | Equipo técnico completo | Actualización de KPIs; NCs cerradas vs. pendientes |
| **Comité de Calidad** | Trimestral | Responsable del Plan + DRTPE | Reporte de avance; ajuste de prioridades |
| **Re-auditoría ISO 25010** | Semestral (Dic 2026 y Jun 2027) | Auditor externo o equipo de QA | Nuevo informe de auditoría con cumplimiento actualizado |

---

## 8. ANÁLISIS DE IMPACTO POR CARACTERÍSTICA ISO 25010

### Antes vs. Después de implementar el Plan de Mejora

| Característica | Calificación actual | Acciones del plan | Calificación esperada | Δ |
|---|---|---|---|---|
| Adecuación Funcional | 3.67 | PM-03, PM-04, PM-05, PM-08, PM-19 | 4.50 | +0.83 |
| Eficiencia del Desempeño | 3.33 | PM-12, PM-15, PM-22 | 4.00 | +0.67 |
| Compatibilidad | 4.00 | PM-20 (docs integración) | 4.20 | +0.20 |
| Usabilidad | 3.40 | PM-11, PM-14, PM-18, PM-23 | 4.00 | +0.60 |
| Fiabilidad | 3.50 | PM-07, PM-10, PM-16, PM-17, PM-21 | 4.20 | +0.70 |
| Seguridad | 4.00 | PM-01, PM-06, PM-08, PM-09, PM-10, PM-13 | 4.70 | +0.70 |
| Mantenibilidad | 4.20 | PM-13, PM-16, PM-20, PM-24 | 4.60 | +0.40 |
| Portabilidad | 4.33 | PM-02, PM-21 | 4.50 | +0.17 |
| **PROMEDIO** | **3.80** | | **4.46** | **+0.66** |
| **% CUMPLIMIENTO** | **76%** | | **≈ 89%** | **+13%** |

---

## 9. CONCLUSIONES

### 9.1 Viabilidad del Plan

El Plan de Mejora es **técnicamente viable** en su totalidad. Las acciones de corto plazo (PM-01 a PM-10) no requieren recursos externos significativos: la mayoría son cambios de configuración, correcciones de código y adición de tests que pueden ser ejecutados por el equipo actual del proyecto. Las acciones de largo plazo (PM-19, PM-22, PM-23) requieren datos históricos y coordinación institucional que deben planificarse con anticipación.

### 9.2 Criterio de Éxito del Plan

El plan se considerará **exitoso** cuando:

1. Todos los KPIs de la sección 5 hayan alcanzado su meta definida.
2. La re-auditoría ISO/IEC 25010 programada para **Junio 2027** arroje un cumplimiento **≥ 88%**.
3. El sistema esté desplegado en producción con **TLS activo**, **0 NCs mayores abiertas** y **SUS ≥ 70** verificado con usuarios reales de DRTPE-Junín.
4. El Quality Gate de SonarQube sea **OK** con cobertura de código ≥ 70% en el backend.

### 9.3 Relación con la Mejora Continua

Este plan no es un evento único sino el inicio de un ciclo de mejora continua (PDCA) en el sistema Linku. Se recomienda:

- Mantener el ciclo de auditoría interna semestral como proceso permanente.
- Incorporar la medición de KPIs como un artefacto del sprint review.
- Actualizar `CLAUDE.md` y este plan con cada hallazgo nuevo, siguiendo el principio de "fuente única de verdad" ya establecido en el proyecto.
- Considerar la certificación ISO/IEC 25040 formal ante un organismo acreditado al alcanzar el cumplimiento del 90%+.

---

## 10. REFERENCIAS NORMATIVAS

| Norma | Título | Aplicación en este plan |
|---|---|---|
| ISO/IEC 25010:2011 | Systems and software Quality Requirements and Evaluation — System and software quality models | Marco de características y subcaracterísticas para clasificar hallazgos |
| ISO/IEC 25040:2011 | Systems and software Quality Requirements and Evaluation — Evaluation process | Proceso de evaluación y re-auditoría |
| ISO/IEC 25041:2012 | Evaluation guide for developers, acquirers and independent evaluators | Guía para la implementación de mejoras |
| OWASP Top 10:2021 | Open Web Application Security Project — Top 10 Web Application Security Risks | Referencia para acciones PM-01, PM-06, PM-10, PM-13 |
| WCAG 2.1 (W3C) | Web Content Accessibility Guidelines | Referencia para PM-14 |
| Ley N° 29733 (Perú) | Ley de Protección de Datos Personales | Marco legal para NC-01 (TLS) y gestión de PII |

---

*Plan de Mejora elaborado el 2026-06-23 como respuesta a la Auditoría ISO/IEC 25010 del Sistema Linku.*
*Próxima revisión del plan: 2026-09-30 (revisión trimestral de hito H1).*
*Norma de referencia: ISO/IEC 25000 SQuaRE — Systems and software Quality Requirements and Evaluation.*
