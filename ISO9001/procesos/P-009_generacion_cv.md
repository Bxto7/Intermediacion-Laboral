# P-009 — Generación Automática de CV / Hoja de Vida
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M06 — Asistente de Identidad Laboral
**RF Cubiertos:** RF096–RF110
**Sprint de implementación:** Sprint 3
**Componentes clave:**
- `backend/app/services/cv_builder/pdf_generator.py`
- `backend/app/api/v1/cv.py`
- `backend/app/tasks/cv_generator.py`
- `backend/app/utils/cv_templates/primer_empleo.html`
- `backend/app/utils/cv_templates/oficio.html`
- `backend/app/utils/cv_templates/experiencia.html`

---

## 1. Propósito

Generar automáticamente una Hoja de Vida (CV) en formato PDF personalizada según el tipo de trabajador, usando los datos del perfil construido en los flujos P-003, P-004 o P-005, a través de plantillas HTML diferenciadas renderizadas con WeasyPrint + Jinja2.

---

## 2. Plantillas por Tipo de Trabajador

| `worker_type` | Plantilla | Contenido principal |
|---------------|-----------|---------------------|
| `primer_empleo` | `primer_empleo.html` | Datos básicos, nivel educativo, habilidades blandas extraídas del wizard, intereses laborales, sectores sugeridos |
| `oficio` | `oficio.html` | Datos básicos, categoría de oficio, años de experiencia, calificación promedio, hasta 6 trabajos del portafolio con skills, slug público del portafolio |
| `experiencia` | `experiencia.html` | Datos básicos, cargo (job_title), bio profesional, años de experiencia |

---

## 3. Entradas del Proceso

| Entrada | Fuente | Condición |
|---------|--------|-----------|
| `worker_id` | Path param | UUID del trabajador |
| `worker.worker_type` | BD | Determina template y datos a cargar |
| `worker.full_name` | BD (BYTEA cifrado) | Se descifra en memoria antes del render |
| `worker.phone` | BD (BYTEA cifrado) | Se descifra en memoria |
| `user.email` | BD `users` | Join por `user_id` |
| Datos específicos por tipo | BD | wizard_progress (primer_empleo), portfolio_entries (oficio), bio/job_title (experiencia) |

---

## 4. Salidas del Proceso

| Salida | Destino | Contenido |
|--------|---------|-----------|
| PDF bytes | HTTP response / GCS | Archivo PDF válido (`%PDF-` header) |
| `generated_cvs` | BD | Registro de generación: worker_id, template_used, generated_at |
| Tarea Celery (modo async) | Cola `cv_generation` | `{task_id, status: "processing"}` |
| Notificación WebSocket | Canal Redis | `type: "cv_ready"` |

---

## 5. Flujo del Proceso

```
[Trabajador autenticado]
    │
    ├─► POST /api/v1/cv/generate/{worker_id}   [ASÍNCRONO]
    │       │
    │       ├─► Verificar rol WORKER + worker.user_id == token.sub (403 si no)
    │       ├─► Encolar generate_cv_task(worker_id) en cola "cv_generation"
    │       └─► Retornar {task_id, status: "processing"}
    │
    └─► GET /api/v1/cv/download/{worker_id}    [SÍNCRONO — dev/testing]
            │
            ├─► Verificar rol WORKER + ownership (403 si otro worker)
            └─► generate_cv_pdf(worker_id, db) → bytes

generate_cv_pdf(worker_id, db):
    │
    ├─► Cargar worker de BD
    ├─► Seleccionar template: TEMPLATE_MAP[worker.worker_type]
    │       ├─► "primer_empleo" → primer_empleo.html
    │       ├─► "oficio"        → oficio.html
    │       └─► "experiencia"   → experiencia.html (fallback si tipo desconocido)
    │
    ├─► _build_template_context(worker, db):
    │       │
    │       ├─► Descifrar full_name: decrypt_field(worker.full_name)
    │       ├─► Descifrar phone: decrypt_field(worker.phone)
    │       ├─► Obtener email desde users (JOIN por user_id)
    │       │
    │       ├─► [primer_empleo]:
    │       │       ├─► wizard_progress.extracted_skills → skills del CV
    │       │       ├─► wizard_progress.answers["education"] → educación
    │       │       └─► wizard_progress.answers["job_interests"] → intereses
    │       │
    │       ├─► [oficio]:
    │       │       ├─► portfolio_entries (is_public=True, limit=6) → trabajos
    │       │       ├─► trade_category, avg_rating
    │       │       └─► username → slug del portafolio público
    │       │
    │       └─► [experiencia]:
    │               ├─► job_title, bio, years_experience
    │               ├─► NOTA: languages/additional_info → [] (deuda CV-EXP-VACIO)
    │               └─► photo_url → None (no implementado)
    │
    ├─► Jinja2 Template.render(context)
    ├─► WeasyPrint HTML(string=html_string).write_pdf()
    └─► Retornar bytes (application/pdf)
```

---

## 6. Worker Celery Dedicado

| Atributo | Valor |
|----------|-------|
| Cola | `cv_generation` |
| Contenedor | `worker-cv` (imagen del API con WeasyPrint instalado) |
| Reintentos | Máximo 3, backoff 60s × (intento + 1) |
| Dependencia del SO | libpango, libcairo, libgdk-pixbuf (Debian bookworm) |

---

## 7. Criterios de Aceptación del PDF Generado

```bash
# 1. HTTP 200
# 2. Content-Type: application/pdf
# 3. Primeros 5 bytes del archivo: %PDF-
# 4. Tamaño > 1 KB
# 5. Se abre sin corrupción en un lector PDF
head -c 5 /tmp/cv.pdf   # debe imprimir: %PDF-
```

---

## 8. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Autorización estricta | `worker.user_id == token.sub` — un worker solo genera su propio CV |
| PII descifrada solo en memoria | `full_name` y `phone` se descifran durante el render, nunca se almacenan en texto |
| WeasyPrint verificado al inicio | Si faltan libs del SO, se lanza `RuntimeError` inmediato con mensaje descriptivo |
| Plantillas con `<title>` | Bug SONAR-1 corregido (2026-05-31): las 3 plantillas tienen `<title>` |
| Perfiles incompletos no rompen | Contexto usa `getattr(..., default)` para campos opcionales |
| Registro de generación | Cada PDF generado queda en `generated_cvs` (trazabilidad) |

---

## 9. Deudas Técnicas Conocidas

| ID | Descripción | Impacto |
|----|-------------|---------|
| CV-EXP-VACIO | CV tipo `experiencia` no cablea datos parseados de `/nlp/parse-cv` | CV de profesionales sale sin experiencias/educación/skills |
| PDF-SYNC | `download` ejecuta WeasyPrint síncrono en el event loop async | Bloqueo bajo carga (ver R2/P2 auditoría FURPS+) |

---

## 10. Indicadores de Desempeño

| Indicador | Objetivo (KPI: TCC) | Fuente |
|-----------|---------------------|--------|
| Tasa de Completitud de CV (TCC) | > 50% para primer_empleo y oficio | `COUNT(DISTINCT generated_cvs.worker_id) / COUNT(workers WHERE type IN (pe, of))` |
| Tiempo de generación del PDF | < 5 segundos | Celery task duration |
| CVs generados por tipo | Distribución por `worker_type` | `generated_cvs.template_used` |

---

## 11. Pruebas Automatizadas

Archivo: `backend/tests/unit/test_cv_generator.py`
- 33 tests cubriendo: generador PDF, contexto por tipo, cifrado/descifrado PII
- `test_primer_empleo_cv_includes_skills`
- `test_oficio_cv_includes_portfolio`
- `test_cv_requires_worker_ownership`

---

*P-009 | Linku DRTPE-Junín · Implementado Sprint 3 · RF096–RF110*
