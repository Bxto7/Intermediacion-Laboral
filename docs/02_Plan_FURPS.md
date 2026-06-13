# Plan de Mejora y Mitigación FURPS+

> Insumo: [01_Auditoria_FURPS.md](01_Auditoria_FURPS.md) (Global 80/100 — Bueno).
> Proyecto: **Linku — Sistema de Intermediación Laboral DRTPE-Junín**.
> Premisa: **el sistema está en producción**. Todo cambio es incremental, compatible hacia atrás y reversible.
> Fecha: 2026-06-13.

## 1. Estrategia de Preservación de Funcionalidad

El plan se ejecuta sin interrumpir la operación aplicando tres garantías transversales. **Primero, aislamiento por banderas de funcionalidad (feature flags):** cada cambio de comportamiento de riesgo (ranking de matching, render de PDF, refresh de token) se activa mediante una variable de entorno con _default_ en el comportamiento actual, de modo que el código nuevo convive con el viejo y se puede desactivar al instante sin redeploy de código. **Segundo, compatibilidad de contratos:** ningún endpoint, payload ni esquema de respuesta cambia de forma; las mejoras (p. ej. envelope de error) se introducen de manera _aditiva_ y los campos existentes se preservan. **Tercero, cambios de base de datos solo aditivos y reversibles:** los índices se crean con `CONCURRENTLY` (sin bloqueo de tabla), las migraciones Alembic siempre incluyen `downgrade`, y no se borra ni reescribe ninguna columna existente durante la transición. Cada tarea se valida de forma aislada (test unitario/integración nuevo verde antes de mergear) y se acompaña de un plan de rollback explícito a nivel de código, infraestructura o datos.

## 2. Roadmap de Ejecución

### Fase 1: Estabilización Inmediata (Corto Plazo)
*(Tareas Críticas y de Alto impacto / Bajo esfuerzo. Observabilidad, fiabilidad bajo carga y verificación de seguridad).*
* **Tarea 1.1:** Eliminar el silenciamiento de errores (`except: pass`) en el flujo de matching y añadir logging estructurado.
* **Tarea 1.2:** Desbloquear el event loop en la generación de PDF (offload de WeasyPrint a executor / entrega vía Celery).
* **Tarea 1.3:** Verificar y asegurar el autoescape de texto libre en portafolio público y plantillas de CV (riesgo XSS almacenado).
* **Tarea 1.4:** Confirmar y alinear ruta/payload de extracción NLP del wizard (front vs back).

### Fase 2: Refactorización y Deuda Técnica (Mediano Plazo)
*(Mejoras arquitectónicas, estructurales y de rendimiento).*
* **Tarea 2.1:** Migrar el ranking de similitud al operador `<=>` de pgvector con índice (HNSW/IVFFlat), bajo bandera.
* **Tarea 2.2:** Extraer la lógica de matching a un servicio de dominio; dejar el router como orquestador HTTP.
* **Tarea 2.3:** Implementar refresh automático del access token en el interceptor Axios.
* **Tarea 2.4:** Cablear los datos parseados de `/nlp/parse-cv` al contexto del CV tipo `experiencia`.
* **Tarea 2.5:** Estandarizar un envelope de error de API de forma aditiva.
* **Tarea 2.6:** Sanear imports diferidos dentro de funciones/loops.

### Fase 3: Evolución y Soporte (Largo Plazo)
*(Cobertura de pruebas extensa, modelo ML real y endurecimiento de configuración).*
* **Tarea 3.1:** Construir suite de pruebas del frontend (componentes y flujos críticos).
* **Tarea 3.2:** Entrenar/cargar el modelo ML supervisado para reemplazar el `ml_score` stub.
* **Tarea 3.3:** Externalizar defaults sensibles, endurecer almacenamiento de fotos y medir cobertura backend.

## 3. Detalle de Mejoras Priorizadas

### T1.1 - Observabilidad del flujo de matching
* **Categoría FURPS+:** R (Reliability)
* **Objetivo:** Reemplazar `except Exception: pass` por captura con logging estructurado y métricas, sin alterar la respuesta del endpoint.
* **Justificación:** Hallazgo R1 — [matching.py:113-114](backend/app/api/v1/matching.py#L113) y [matching.py:161-164](backend/app/api/v1/matching.py#L161) tragan fallos de embeddings y de persistencia.
* **Prioridad:** Crítica
* **Riesgo de Ejecución:** Bajo — solo se añade logging; el control de flujo (degradar a `cosine=0.5`, rollback de commit) se conserva idéntico.
* **Dependencias:** Ninguna.

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Unitaria | Test que fuerza excepción en el cálculo de coseno y en el commit; verifica que se loguea (`logger.warning`) y que la respuesta sigue siendo 200 con el fallback. |
| **Rollback** | Código | Cambio local en un solo archivo; revertir el commit restaura el comportamiento previo. |

### T1.2 - PDF sin bloqueo del event loop
* **Categoría FURPS+:** P / R (Performance, Reliability)
* **Objetivo:** Evitar que WeasyPrint (síncrono, CPU-bound) bloquee el event loop durante el render, manteniendo la URL de descarga actual.
* **Justificación:** Hallazgos P2 y R2 — `generate_cv_pdf` síncrono ejecutado dentro de la ruta `async` de `download`.
* **Prioridad:** Crítica
* **Riesgo de Ejecución:** Medio — cambia el modelo de ejecución; mitigado con bandera `CV_PDF_OFFLOAD` (default OFF = comportamiento actual).
* **Dependencias:** Ninguna para el offload a executor; la entrega vía Celery depende de `worker-cv` operativo.

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Integración | Prueba de carga concurrente: N descargas simultáneas no degradan la latencia de `/health`; el PDF sigue devolviendo `%PDF-`, `application/pdf`, 200. |
| **Rollback** | Código / Infraestructura | Bandera `CV_PDF_OFFLOAD=false` revierte a la ruta síncrona sin redeploy; ante incidente, rollback de imagen del contenedor `api` en el pipeline. |

### T1.3 - Verificación de autoescape (anti-XSS almacenado)
* **Categoría FURPS+:** + (Seguridad)
* **Objetivo:** Confirmar que Jinja2 autoescapa el texto libre (`bio`, `description`, skills) en portafolio público y CV, y sanitizar donde no aplique.
* **Justificación:** Hallazgo +2 — texto libre fluye a plantillas y a la página pública sin sanitización explícita observable.
* **Prioridad:** Alta
* **Riesgo de Ejecución:** Bajo — auditoría de plantillas + activación explícita de autoescape; sin cambio de contrato.
* **Dependencias:** Ninguna.

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Unitaria / Integración | Test con payload `<script>` en `bio`/`description` que verifica salida escapada en el HTML del portafolio público y del PDF. |
| **Rollback** | Código | Cambio acotado a plantillas/config Jinja; revertir commit. El escapado es seguro por defecto, sin impacto funcional. |

### T1.4 - Alineación de la extracción NLP del wizard
* **Categoría FURPS+:** F (Functionality)
* **Objetivo:** Confirmar la ruta/payload reales y alinear front y back (`/nlp/extract-skills` vs `/nlp/extract-skills/wizard`).
* **Justificación:** Hallazgo F3 (riesgo a verificar) — posible fallo silencioso de extracción de skills en el Step3.
* **Prioridad:** Alta
* **Riesgo de Ejecución:** Bajo — si hay desajuste, se corrige el cliente o se añade alias de ruta backward-compatible en el backend.
* **Dependencias:** Ninguna.

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Integración / E2E | Recorrer el Step3 del wizard y verificar 200 + skills devueltas; test de contrato front/back sobre el payload. |
| **Rollback** | Código | Si se añade alias de ruta en el router, es aditivo (no rompe la ruta vigente); revertir commit. |

### T2.1 - Ranking vectorial nativo con pgvector
* **Categoría FURPS+:** P (Performance)
* **Objetivo:** Resolver el ordenamiento por similitud en la BD con el operador `<=>` y un índice (HNSW/IVFFlat), en lugar de calcular coseno en Python.
* **Justificación:** Hallazgo P1 y P3 — [matching.py:101-114](backend/app/api/v1/matching.py#L101) itera ofertas con numpy e ignora el índice de la columna `Vector(384)`.
* **Prioridad:** Alta
* **Riesgo de Ejecución:** Medio/Alto — afecta el orden de resultados del flujo central. Se mitiga con patrón Estrangulador: bandera `MATCHING_USE_PGVECTOR` (default OFF) y fase de _shadow run_ comparando ambos rankings antes de conmutar.
* **Dependencias:** Índice creado vía migración Alembic (`CONCURRENTLY`); embeddings poblados (cola `embeddings` operativa).

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Unitaria / Integración | Test que compara top-K de la ruta pgvector contra la ruta Python sobre un dataset fijo (tolerancia de orden documentada); verifica que el re-ranking de equidad sigue aplicándose. |
| **Rollback** | Datos / Código | `MATCHING_USE_PGVECTOR=false` vuelve a la ruta Python (que permanece en el código durante la transición); `downgrade` de Alembic hace `DROP INDEX CONCURRENTLY`. El índice es aditivo: su presencia no afecta la ruta vieja. |

### T2.2 - Extracción del servicio de dominio de matching
* **Categoría FURPS+:** + (Arquitectura) / S
* **Objetivo:** Mover scoring, equidad y persistencia de eventos a un servicio (`services/matching/`), dejando el router como orquestador HTTP.
* **Justificación:** Hallazgo +3 — [matching.py:49-190](backend/app/api/v1/matching.py#L49) acopla transporte y lógica de negocio.
* **Prioridad:** Media
* **Riesgo de Ejecución:** Medio — refactor del flujo central; se hace _move, don't rewrite_ (extraer sin cambiar comportamiento), idealmente después de T2.1.
* **Dependencias:** Recomendable tras T1.1 (logging) y T2.1 (ranking estabilizado).

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Unitaria / Integración | Tests de integración existentes de `/match` deben pasar sin cambios; nuevos tests unitarios del servicio aislado (sin HTTP). |
| **Rollback** | Código | Refactor puro sin cambio de contrato; revertir el commit/PR restaura la versión inline. |

### T2.3 - Refresh automático de token
* **Categoría FURPS+:** R (Reliability) / U
* **Objetivo:** Que el interceptor Axios intente `/auth/refresh` ante un 401 antes de desloguear, evitando cortes en medio de un flujo.
* **Justificación:** Hallazgo R3 — [client.ts:39-45](frontend/src/api/client.ts#L39) borra tokens sin intentar refresh.
* **Prioridad:** Media
* **Riesgo de Ejecución:** Medio — manejar reintentos y evitar bucles de refresh; mitigado con cola de requests pendientes y un único refresh en vuelo.
* **Dependencias:** Endpoint `/auth/refresh` ya existe ([auth.py:143](backend/app/api/v1/auth.py#L143)).

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Unitaria (front) / E2E | Test del interceptor: 401 → refresh exitoso → reintento transparente; refresh fallido → logout actual. Cubre el caso de refresh expirado. |
| **Rollback** | Código | Cambio acotado a `client.ts`; revertir restaura el comportamiento de logout inmediato. |

### T2.4 - Cableado de datos del CV `experiencia`
* **Categoría FURPS+:** F (Functionality)
* **Objetivo:** Poblar el contexto del CV `experiencia` con los datos parseados de `/nlp/parse-cv` (experiencia, educación, skills, idiomas).
* **Justificación:** Hallazgo F2 — [pdf_generator.py:144-150](backend/app/services/cv_builder/pdf_generator.py#L144) deja campos vacíos por falta de fuente.
* **Prioridad:** Media
* **Riesgo de Ejecución:** Bajo — afecta solo la rama `experiencia` del generador; los otros tipos no se tocan.
* **Dependencias:** Persistencia de los campos parseados (puede requerir migración aditiva para almacenar el resultado de `parse-cv`).

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Integración | Generar CV `experiencia` con datos parseados y verificar que el PDF incluye las secciones; perfil incompleto sigue generando PDF sin romper. |
| **Rollback** | Código / Datos | Revertir commit del generador; migración aditiva con `downgrade` que elimina la columna nueva sin afectar datos existentes. |

### T2.5 - Envelope de error estandarizado (aditivo)
* **Categoría FURPS+:** U (Usability)
* **Objetivo:** Unificar la forma de los errores (`code`, `message`, `details`) preservando el campo `detail` actual.
* **Justificación:** Hallazgo U3 — respuestas de error con forma variable según endpoint.
* **Prioridad:** Media
* **Riesgo de Ejecución:** Bajo — aditivo; se conserva `detail` para no romper clientes existentes.
* **Dependencias:** Ninguna.

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Integración | Tests verifican que los errores incluyen los campos nuevos y mantienen `detail`; el frontend sigue leyendo `detail` sin cambios. |
| **Rollback** | Código | Handler centralizado; revertir commit restaura las respuestas previas. |

### T2.6 - Saneamiento de imports diferidos
* **Categoría FURPS+:** S (Supportability)
* **Objetivo:** Subir los imports dentro de funciones/loops al nivel de módulo donde no haya ciclos, documentando los que sí lo requieran.
* **Justificación:** Hallazgo S2 — imports en [matching.py:86](backend/app/api/v1/matching.py#L86), [matching.py:148-150](backend/app/api/v1/matching.py#L148), etc.
* **Prioridad:** Media
* **Riesgo de Ejecución:** Bajo — mecánico; cuidado con import circular (por eso algunos quedaron diferidos).
* **Dependencias:** Idealmente tras T2.2 (que reubica parte del código).

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Unitaria | La suite backend completa pasa; arranque de la app sin `ImportError`. |
| **Rollback** | Código | Revertir commit. |

### T3.1 - Suite de pruebas del frontend
* **Categoría FURPS+:** S (Supportability)
* **Objetivo:** Introducir testing de frontend (Vitest + Testing Library) cubriendo flujos críticos: login, guards, wizard, interceptor de token.
* **Justificación:** Hallazgo S1 — 0 pruebas en ~9.039 LOC de UI.
* **Prioridad:** Media (Alta dentro de Fase 3 por su impacto en regresión)
* **Riesgo de Ejecución:** Bajo — solo añade pruebas; no toca producción.
* **Dependencias:** Ninguna; T2.3 aporta el primer caso (interceptor).

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Unitaria / E2E | Cobertura inicial de flujos críticos; integrar `lcov.info` al pipeline y a SonarQube. |
| **Rollback** | Código | Solo archivos de test y config; sin riesgo para runtime. |

### T3.2 - Modelo ML supervisado real
* **Categoría FURPS+:** F (Functionality)
* **Objetivo:** Entrenar/cargar el modelo que reemplace el `ml_score` fijo en 0.5, integrado vía MLflow y versionado.
* **Justificación:** Hallazgo F1 — [matching.py:103](backend/app/api/v1/matching.py#L103) `ml_score = 0.5` stub.
* **Prioridad:** Media
* **Riesgo de Ejecución:** Medio — calidad del modelo depende de datos; se introduce bajo bandera con fallback a 0.5 y monitoreo de drift (ya existe `psi_drift_detector`).
* **Dependencias:** Dataset de entrenamiento (cola `reports`/`generate_research_dataset`); idealmente tras T2.1 y T2.2.

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Unitaria / Integración | Métricas offline del modelo (AUC/precision@k); comparación shadow contra el baseline coseno antes de activar en el `combined_score`. |
| **Rollback** | Código / Datos | Bandera que vuelve a `ml_score=0.5`; versionado de modelo en MLflow permite revertir a una versión previa. |

### T3.3 - Endurecimiento de configuración y cobertura
* **Categoría FURPS+:** + (Infra/Seguridad) / S
* **Objetivo:** Externalizar defaults sensibles (AES placeholder, credenciales BD), endurecer almacenamiento de fotos en dev y medir cobertura backend en el pipeline.
* **Justificación:** Hallazgos +5, +4 y S4 — defaults en [config.py:12](backend/app/core/config.py#L12)/[config.py:23](backend/app/core/config.py#L23), `/tmp` en [portfolio.py:319-324](backend/app/api/v1/portfolio.py#L319), cobertura no medida.
* **Prioridad:** Baja
* **Riesgo de Ejecución:** Bajo — los guards de producción ya existen; cambios mayormente de configuración/CI.
* **Dependencias:** Ninguna.

**Estrategias de Implementación:**
| Fase | Estrategia | Descripción |
| :--- | :--- | :--- |
| **Validación** | Integración / CI | Arranque en prod falla si faltan secretos reales; `pytest --cov` genera `coverage.xml` y se publica en SonarQube. |
| **Rollback** | Configuración | Variables de entorno; revertir cambios de CI sin afectar runtime. |

## 4. Riesgos Globales de Ejecución

1. **Cambio de orden de resultados del matching (T2.1).** Migrar a pgvector puede alterar sutilmente el ranking que los usuarios ya conocen y sobre el que se registran métricas (`MatchEvent`, equidad). _Mitigación:_ patrón Estrangulador con bandera `MATCHING_USE_PGVECTOR` en OFF, fase de _shadow run_ que compara ambos rankings sobre tráfico real, y conmutación solo tras validar paridad y umbral de equidad (disparate impact ≥ 0.80).

2. **Regresión por refactor del flujo central sin red de seguridad en el frontend (T2.2 + T2.3).** Tocar matching y el interceptor de auth mientras el frontend no tiene pruebas eleva el riesgo de regresión invisible. _Mitigación:_ adelantar la cobertura mínima de T3.1 para los flujos afectados (interceptor, guards) antes de mergear T2.3, y apoyarse en los tests de integración de `/match` ya existentes para T2.2.

3. **Bloqueo o degradación en el cambio del modelo de ejecución del PDF y del modelo ML (T1.2 y T3.2).** Ambos cambian cómo se ejecuta trabajo pesado (CPU-bound / inferencia) y dependen de infraestructura (`worker-cv`, MLflow). _Mitigación:_ banderas con default en el comportamiento actual, validación bajo carga antes de activar, fallback automático (PDF síncrono / `ml_score=0.5`) y rollback de imagen de contenedor en el pipeline ante cualquier incidente.
