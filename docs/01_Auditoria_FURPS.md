# Informe de Auditoría FURPS+

> Proyecto: **Linku — Sistema de Intermediación Laboral DRTPE-Junín**
> Tipo: Auditoría estática, solo lectura, basada en evidencia.
> Fecha: 2026-06-13 · Rama auditada: `AUDITORIAS`
> Alcance medido: backend ~9.105 LOC Python · frontend ~9.039 LOC TS/TSX · 18 routers · 24 modelos · 45 archivos de test backend · 0 tests frontend.

## 1. Resumen Ejecutivo

* **Estado general:** El proyecto está en un nivel **Bueno** de madurez. La cobertura funcional del dominio es amplia y la postura de **seguridad es la mayor fortaleza** (JWT RS256, cifrado AES-256-GCM de PII con nonce aleatorio, bcrypt cost 12, blacklist de tokens y rate-limiting real). La estructura por capas es clara y existe una suite de pruebas backend considerable. Las debilidades se concentran en **Performance** y **Reliability**: el motor de matching no usa el índice de pgvector (calcula coseno en Python), la generación de PDF corre síncrona dentro del event loop, hay bloques `except: pass` que silencian errores, y el frontend no tiene pruebas automatizadas.

* **Fortalezas principales:**
  * Seguridad de autenticación y datos de nivel sólido (RS256, AES-GCM, bcrypt 12, blacklist por `jti` y por usuario, rate-limiting Redis).
  * Cobertura de dominio amplia: 18 routers y 24 modelos cubren auth, onboarding, wizard, portafolio, CV, matching, marketplace, postulaciones, contratos y encuestas.
  * Arquitectura por capas consistente (`api / core / models / schemas / services / nlp / ml / tasks`) y logging estructurado (`structlog`).
  * Suite de pruebas backend amplia (45 archivos unit + integration).

* **Debilidades principales:**
  * **Performance:** el matching calcula similitud coseno en Python (numpy) en lugar de usar el operador `<=>` de pgvector → el índice vectorial declarado queda sin uso.
  * **Reliability:** WeasyPrint se ejecuta de forma síncrona dentro de un `async def` (bloquea el event loop); existen `except Exception: pass` que tragan errores.
  * **Supportability:** 0 pruebas en el frontend (~9.000 LOC sin red de seguridad); cobertura backend real no verificable en esta auditoría.
  * **Functionality:** `ml_score` está fijo en 0.5 (modelo ML no entrenado) — el matching diferenciado depende casi solo del coseno.

## 2. Scorecard FURPS+ y Puntaje Global

| Categoría | Puntaje | Nivel de Madurez |
| :--- | :--- | :--- |
| **Functionality (F)** | 80/100 | Bueno |
| **Usability (U)** | 88/100 | Excelente |
| **Reliability (R)** | 75/100 | Bueno |
| **Performance (P)** | 75/100 | Bueno |
| **Supportability (S)** | 80/100 | Bueno |
| **Plus (+)** | 84/100 | Excelente |
| **GLOBAL** | **80/100** | **Bueno** |

> Método: cada categoría parte de 100 y descuenta por hallazgo (Crítico -20, Alto -10, Medio -5, Bajo -2). Global = promedio simple de las seis categorías.

## 3. Hallazgos Detallados

### Functionality (F) — 80/100
* **Hallazgo F1 (debilidad):** `ml_score` está fijo en `0.5`; el modelo ML supervisado no está entrenado ni cargado.
  * **Evidencia/Ubicación:** [matching.py:103](backend/app/api/v1/matching.py#L103) (`ml_score = 0.5`); se combina en `combined_score` pesando β por tipo de trabajador.
  * **Severidad:** Alta
  * **Impacto Técnico:** El "matching diferenciado por `worker_type`" — núcleo del producto — queda dominado por la similitud coseno; el componente ML no aporta señal real.
* **Hallazgo F2 (debilidad):** El contexto del CV tipo `experiencia` no se cablea con datos parseados; campos estructurados (`languages`, `additional_info`, foto) quedan vacíos por falta de fuente de datos.
  * **Evidencia/Ubicación:** [pdf_generator.py:144-150](backend/app/services/cv_builder/pdf_generator.py#L144) (`"languages": []`, `"additional_info": []`, `"photo_url": None`); la rama `experiencia` no consume el resultado de `/nlp/parse-cv`.
  * **Severidad:** Media
  * **Impacto Técnico:** El CV de profesionales con experiencia sale empobrecido; degrada el valor del flujo `experiencia`.
* **Hallazgo F3 (riesgo a verificar):** Posible desajuste de ruta/payload entre frontend (`/nlp/extract-skills`) y backend (`/nlp/extract-skills/wizard`).
  * **Evidencia/Ubicación:** Documentado en `CLAUDE.md` (INT-NLP); el router expone `nlp.py`. No verificable de forma concluyente sin trazar la llamada del Step3 del wizard.
  * **Severidad:** Media
  * **Impacto Técnico:** Si la ruta no coincide, la extracción NLP de skills en el wizard falla silenciosamente.
* **Hallazgo F4 (fortaleza):** Cobertura de dominio amplia y coherente con el modelo de negocio (3 `worker_type`, roles, ciclo completo).
  * **Evidencia/Ubicación:** 18 routers en [api/v1/](backend/app/api/v1/), 24 modelos en [models/](backend/app/models/).
  * **Severidad:** Positiva
  * **Impacto Técnico:** Base funcional madura para la operación end-to-end.

### Usability (U) — 88/100
* **Hallazgo U1 (fortaleza):** Validación de entrada robusta y mensajes de error específicos en español.
  * **Evidencia/Ubicación:** Pydantic v2 (`schemas/`), Zod en frontend; errores tipados como 409 "Email ya registrado", 401 "Credenciales invalidas", 422 con nombre de archivo y límite en [portfolio.py:306-315](backend/app/api/v1/portfolio.py#L306).
  * **Severidad:** Positiva
  * **Impacto Técnico:** Respuestas claras y accionables; reduce fricción en UX de baja alfabetización digital.
* **Hallazgo U2 (fortaleza):** `forgot-password` no revela existencia de cuentas ("Si el email existe, recibiras un enlace").
  * **Evidencia/Ubicación:** [auth.py:265-267](backend/app/api/v1/auth.py#L265).
  * **Severidad:** Positiva
  * **Impacto Técnico:** Evita enumeración de usuarios sin sacrificar UX.
* **Hallazgo U3 (debilidad):** No hay un envelope de error estandarizado a nivel de API; las respuestas de error son `{"detail": <string>}` con forma variable según el endpoint.
  * **Evidencia/Ubicación:** `HTTPException(detail=...)` disperso por routers; handler global devuelve `{"detail": ...}` en 500 ([main.py:74-78](backend/app/main.py#L74)).
  * **Severidad:** Media
  * **Impacto Técnico:** Dificulta el manejo uniforme de errores en el cliente y la i18n de mensajes.

### Reliability (R) — 75/100
* **Hallazgo R1 (debilidad):** Bloques `except Exception: pass` / rollback silencioso tragan errores en el flujo de matching.
  * **Evidencia/Ubicación:** [matching.py:113-114](backend/app/api/v1/matching.py#L113) (`except Exception: pass` en cálculo de coseno) y [matching.py:161-164](backend/app/api/v1/matching.py#L161) (`except: rollback` sin log al persistir `MatchEvent`).
  * **Severidad:** Alta
  * **Impacto Técnico:** Fallos de embeddings o de persistencia se ocultan; degradan el ranking sin trazabilidad ni alerta.
* **Hallazgo R2 (debilidad):** Generación de PDF síncrona dentro del request `download`.
  * **Evidencia/Ubicación:** Flujo `GET /cv/download/{id}` (síncrono, descrito en `CLAUDE.md`) ejecuta WeasyPrint en el path del request; el generador es `generate_cv_pdf(...) -> bytes`.
  * **Severidad:** Alta
  * **Impacto Técnico:** Bajo carga puede causar timeouts; ver también P2 (bloqueo del event loop).
* **Hallazgo R3 (debilidad):** No hay refresh automático del access token en el cliente; un 401 limpia sesión abruptamente.
  * **Evidencia/Ubicación:** [client.ts:39-45](frontend/src/api/client.ts#L39) — el interceptor 401 borra tokens; no intenta `/auth/refresh`.
  * **Severidad:** Media
  * **Impacto Técnico:** Sesiones expiradas interrumpen al usuario en medio de un flujo (p. ej. wizard) sin recuperación transparente.
* **Hallazgo R4 (fortaleza):** Handler global de excepciones que oculta el detalle en producción y registra `exc_info`.
  * **Evidencia/Ubicación:** [main.py:74-78](backend/app/main.py#L74).
  * **Severidad:** Positiva
  * **Impacto Técnico:** Evita filtrado de stack traces en prod y centraliza el logging de fallos no controlados.

### Performance (P) — 75/100
* **Hallazgo P1 (debilidad):** La similitud coseno se calcula en Python con numpy en un loop, en lugar de usar el operador de distancia de pgvector (`<=>`) y su índice.
  * **Evidencia/Ubicación:** [matching.py:101-114](backend/app/api/v1/matching.py#L101) — itera ofertas y hace `np.dot/np.linalg.norm` por cada una; la columna `embedding Vector(384)` y su índice no participan en el ranking.
  * **Severidad:** Alta
  * **Impacto Técnico:** No escala: el ordenamiento vectorial debería resolverse en la BD con índice (HNSW/IVFFlat). Hoy se traen `top_k*5` ofertas y se computa en app.
* **Hallazgo P2 (debilidad):** WeasyPrint (CPU-bound, síncrono) se invoca dentro de una ruta `async`, bloqueando el event loop durante el render.
  * **Evidencia/Ubicación:** `generate_cv_pdf` síncrono consumido por el endpoint `download` (sección PDF de `CLAUDE.md`); no hay `run_in_executor`/offload.
  * **Severidad:** Alta
  * **Impacto Técnico:** Mientras se genera un PDF, el worker no atiende otras peticiones → degradación global de latencia.
* **Hallazgo P3 (debilidad):** Embeddings cargados íntegros en memoria de la app para el cálculo por petición.
  * **Evidencia/Ubicación:** [matching.py:108-112](backend/app/api/v1/matching.py#L108) (`np.array(worker.embedding)` / `np.array(offer.embedding)`).
  * **Severidad:** Media
  * **Impacto Técnico:** Uso de memoria y CPU proporcional al número de ofertas por request; redundante frente a pgvector.

### Supportability (S) — 80/100
* **Hallazgo S1 (debilidad):** El frontend (~9.039 LOC) no tiene pruebas automatizadas.
  * **Evidencia/Ubicación:** 0 archivos `*.test.*`/`*.spec.*` bajo [frontend/src/](frontend/src/).
  * **Severidad:** Alta
  * **Impacto Técnico:** Cambios en wizard, guards y contextos no tienen red de seguridad; alto riesgo de regresión en la UI.
* **Hallazgo S2 (debilidad):** Imports diferidos dentro de funciones y loops (acoplamiento implícito, code smell).
  * **Evidencia/Ubicación:** [matching.py:86](backend/app/api/v1/matching.py#L86), [matching.py:92](backend/app/api/v1/matching.py#L92), [matching.py:108](backend/app/api/v1/matching.py#L108), [matching.py:148-150](backend/app/api/v1/matching.py#L148); también `import ... inside function` en `pdf_generator` y `portfolio`.
  * **Severidad:** Media
  * **Impacto Técnico:** Oculta dependencias reales del módulo, complica el análisis estático y el testing.
* **Hallazgo S3 (fortaleza):** Suite de pruebas backend amplia (unit + integration) y estructura modular limpia.
  * **Evidencia/Ubicación:** 45 archivos en [backend/tests/](backend/tests/) (incluye `test_security`, `test_matching_engine`, `test_api_auth`, `test_cv_generator`).
  * **Severidad:** Positiva
  * **Impacto Técnico:** Buena base de regresión en el backend.
* **Hallazgo S4 (no verificable):** Cobertura real de pruebas no medida en esta auditoría (no se ejecutó `pytest --cov`); excluida del puntaje.

### Plus (+) — 84/100
* **Hallazgo +1 (fortaleza):** Postura de seguridad sólida y consistente.
  * **Evidencia/Ubicación:** RS256 con par RSA auto-generado ([security.py:33-57](backend/app/core/security.py#L33)); AES-256-GCM con nonce aleatorio de 12 bytes ([security.py:80-91](backend/app/core/security.py#L80)); bcrypt cost 12 ([security.py:72-73](backend/app/core/security.py#L72)); blacklist por `jti` y por usuario ([security.py:123-137](backend/app/core/security.py#L123)); rate-limiting Redis ([auth.py:57](backend/app/api/v1/auth.py#L57)); `SecurityHeadersMiddleware` y CORS restringido ([main.py:53-62](backend/app/main.py#L53)).
  * **Severidad:** Positiva
  * **Impacto Técnico:** Mitiga los riesgos OWASP más comunes en auth y manejo de PII.
* **Hallazgo +2 (debilidad):** Texto libre (bio, portafolio) se renderiza en portafolio público y PDF sin sanitización HTML explícita observable.
  * **Evidencia/Ubicación:** `bio`/`extracted_skills`/`description` de `portfolio_entries` y `Worker` fluyen al contexto de plantillas Jinja2 en [pdf_generator.py](backend/app/services/cv_builder/pdf_generator.py) y a la página pública. No verificable si Jinja autoescapa en todos los puntos del flujo público.
  * **Severidad:** Media
  * **Impacto Técnico:** Riesgo potencial de XSS almacenado si el autoescape no cubre la ruta pública; requiere verificación.
* **Hallazgo +3 (debilidad):** Arquitectura por capas, pero con lógica de negocio dentro de los routers (sin puertos/adaptadores ni separación dominio/infraestructura).
  * **Evidencia/Ubicación:** `matching.py` orquesta acceso a BD, scoring, equidad y persistencia de eventos en el propio endpoint ([matching.py:49-190](backend/app/api/v1/matching.py#L49)).
  * **Severidad:** Media
  * **Impacto Técnico:** Acoplamiento del transporte (HTTP) con la lógica; dificulta reuso y pruebas unitarias del dominio.
* **Hallazgo +4 (debilidad menor):** Escritura a directorio `/tmp` (security hotspot SonarQube), acotada a `development`.
  * **Evidencia/Ubicación:** [portfolio.py:319-324](backend/app/api/v1/portfolio.py#L319) (`Path(f"/tmp/portfolio_photos/{entry_id}")`, `# noqa: S108`); en prod usa storage con signed URL.
  * **Severidad:** Baja
  * **Impacto Técnico:** Aceptable en dev; el hotspot está controlado por `ENVIRONMENT`.
* **Hallazgo +5 (debilidad menor):** Valores por defecto sensibles embebidos en código (AES key placeholder, credenciales `postgres:postgres`).
  * **Evidencia/Ubicación:** [config.py:12](backend/app/core/config.py#L12) y [config.py:23](backend/app/core/config.py#L23); mitigado por validador que prohíbe el placeholder en producción ([config.py:58-59](backend/app/core/config.py#L58)).
  * **Severidad:** Baja
  * **Impacto Técnico:** Riesgo bajo gracias al guard de producción; conviene externalizar también los defaults de BD.

## 4. Deuda Técnica y Riesgos Arquitectónicos

1. **pgvector subutilizado (P1):** el índice vectorial existe pero el ranking se computa en Python — deuda de performance que bloquea el escalado del matching.
2. **PDF síncrono en el event loop (P2/R2):** acopla render CPU-bound al ciclo de petición async; deuda de fiabilidad bajo carga.
3. **Errores silenciados (R1):** `except Exception: pass` y rollback sin log erosionan la observabilidad del flujo crítico de matching.
4. **Frontend sin pruebas (S1):** ~9.000 LOC de UI sin regresión automatizada.
5. **Lógica de negocio en routers (+3) e imports diferidos (S2):** acoplamiento transporte↔dominio; reduce testabilidad unitaria y claridad de dependencias.
6. **`ml_score` stub (F1):** el componente ML del matching diferenciado no es funcional aún.
7. **Riesgos a verificar:** desajuste ruta NLP wizard (F3) y autoescape en portafolio público/PDF (+2).

## 5. Recomendaciones de Alto Nivel

| Prioridad | Categoría | Recomendación | Beneficio Esperado |
| :--- | :--- | :--- | :--- |
| Alta | P | Mover el ranking de similitud al operador `<=>` de pgvector con índice (HNSW/IVFFlat) y `ORDER BY ... LIMIT` en BD | Escalabilidad del matching, menor CPU/memoria en la app |
| Alta | R/P | Servir el PDF desde el resultado de la tarea Celery o, mínimo, ejecutar WeasyPrint en executor (`run_in_executor`) | Evita bloqueo del event loop y timeouts bajo carga |
| Alta | S | Introducir pruebas de frontend (componentes y flujos críticos: login, wizard, guards) | Red de seguridad ante regresiones de UI |
| Media | R | Eliminar `except: pass`: registrar y propagar/medir los fallos en el flujo de matching | Observabilidad y diagnóstico de degradaciones |
| Media | F | Cablear datos parseados de `/nlp/parse-cv` al contexto del CV `experiencia` | CV de profesionales completo y útil |
| Media | + | Verificar autoescape en portafolio público/PDF y sanitizar texto libre | Cierra riesgo potencial de XSS almacenado |
| Media | + | Extraer la lógica de matching a un servicio de dominio; routers solo orquestan HTTP | Testabilidad y reuso; menor acoplamiento |
| Media | U | Estandarizar un envelope de error de API (código, mensaje, detalles) | Manejo de errores e i18n uniformes en el cliente |
| Media | R | Implementar refresh automático del access token en el interceptor Axios | Continuidad de sesión sin cortes abruptos |
| Baja | F | Confirmar y alinear ruta/payload de extracción NLP del wizard (front vs back) | Evita fallo silencioso de extracción de skills |
| Baja | + | Externalizar defaults de BD y reforzar guards de secretos | Reduce riesgo de credenciales por defecto |

## 6. Conclusión Final

**Dictamen:** **Bueno** (80/100).

**Justificación:** La evidencia estática muestra un sistema funcionalmente amplio y con una base de seguridad de calidad por encima del promedio: cifrado de PII con AES-GCM y nonce aleatorio, JWT RS256, bcrypt 12, blacklist de tokens y rate-limiting son prácticas correctas y verificables en `core/security.py` y `api/v1/auth.py`. La estructura por capas y la suite de pruebas backend (45 archivos) sostienen la mantenibilidad del servidor.

El proyecto no alcanza un nivel superior por debilidades concretas y medibles en **Performance** y **Reliability**: el motor de matching ignora el índice de pgvector y calcula el coseno en Python ([matching.py:101-114](backend/app/api/v1/matching.py#L101)), la generación de PDF es síncrona dentro del event loop, hay errores silenciados con `except: pass`, y el frontend carece por completo de pruebas. Resueltas estas, especialmente el uso de pgvector y el offload del PDF, el sistema puede moverse con solidez al rango "Excelente". El componente ML del matching (`ml_score` stub) sigue siendo la principal brecha funcional pendiente.
