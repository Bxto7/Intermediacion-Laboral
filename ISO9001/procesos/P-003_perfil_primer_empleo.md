# P-003 — Construcción de Perfil — Tipo Primer Empleo
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M02 / M06 — Perfil del Trabajador / Asistente de Identidad Laboral
**RF Cubiertos:** RF023–RF035, RF096–RF105
**Sprint de implementación:** Sprint 2 (wizard backend) + Sprint 3 (CV PDF)
**Componentes clave:**
- `backend/app/api/v1/wizard.py`
- `backend/app/services/cv_builder/wizard_service.py`
- `backend/app/nlp/skill_extractor/first_job_extractor.py`
- `backend/app/utils/cv_templates/primer_empleo.html`

---

## 1. Propósito

Guiar a jóvenes sin historial laboral formal a través de un wizard de 6 pasos asistido por NLP para construir su perfil digital y generar su primera hoja de vida, transformando lenguaje coloquial y experiencias informales en competencias estandarizadas.

---

## 2. Alcance

Aplica exclusivamente a trabajadores con `worker_type = "primer_empleo"`. El wizard recoge información en 6 pasos secuenciales y no permite saltar pasos. La extracción de skills ocurre automáticamente en los pasos 3 y 4.

---

## 3. Estructura del Wizard — 6 Pasos

| Paso | Contenido | Extracción NLP |
|------|-----------|----------------|
| 1 | Datos básicos (nombre, DNI, distrito, nivel educativo) | No |
| 2 | Objetivos y aspiraciones laborales | No |
| 3 | Habilidades blandas (lenguaje coloquial) | Sí → `extract_skills_from_wizard_answer` |
| 4 | Actividades previas (ayudo en casa, vendo en mercado...) | Sí → skills acumuladas |
| 5 | Intereses laborales y sectores | No (selección UI) |
| 6 | Preview y generación de CV | No — trigger P-009 |

---

## 4. Entradas del Proceso

| Entrada | Fuente | Validación |
|---------|--------|------------|
| Texto libre del usuario (paso 3 y 4) | Frontend wizard | min 10 chars, max 2000 chars |
| Selección de distrito | Frontend | `District` enum (Huancayo/El Tambo/Chilca/Otro) |
| Nivel educativo | Frontend | `education_level` enum |
| Sectores de interés | Frontend (paso 5) | Lista hasta 3 sectores |
| `worker_id` del token | JWT payload | `require_role(WORKER)` + `worker_type == primer_empleo` |

---

## 5. Salidas del Proceso

| Salida | Destino | Contenido |
|--------|---------|-----------|
| `wizard_progress.answers` actualizado | BD (JSONB) | Respuestas por paso {step_1: {...}, step_3: {...}} |
| `wizard_progress.extracted_skills` | BD (JSONB) | Lista deduplicada de skills estandarizadas |
| `wizard_progress.current_step` | BD | Número de paso alcanzado (1–6) |
| `workers.profile_completeness` | BD | +40 al completar paso 6 |
| Tarea Celery `generate_worker_embedding` | Cola `embeddings` | Trigger de vectorización del perfil |

---

## 6. Flujo del Proceso

```
[Trabajador PRIMER_EMPLEO]
    │
    ▼
GET /api/v1/wizard/progress
    └─► Retorna estado actual del wizard (paso actual + skills extraídas)

POST /api/v1/wizard/step {step, data}
    │
    ├─► Validar que step ≤ current_step + 1 (no saltar pasos)
    │
    ├─► [Paso 3 — Habilidades blandas]
    │       │
    │       └─► extract_skills_from_wizard_answer(text, step=3)
    │               │
    │               ├─► normalize_text(text) → lowercase + ftfy + stopwords
    │               ├─► apply_local_dictionary(text) → huancayo_trades.json
    │               ├─► Buscar en soft_skills_map (~40 términos peruanos)
    │               ├─► spaCy NER → entidades MISC/PER como skills adicionales
    │               └─► Acumular en wizard_progress.extracted_skills
    │
    ├─► [Paso 4 — Actividades previas] → mismo proceso NLP
    │
    ├─► [Paso 5 — Intereses] → guardar en wizard_progress.job_interests
    │
    ├─► [Paso 6 — Completado]
    │       ├─► profile_completeness += 40
    │       └─► Encolar generate_worker_embedding(worker_id)
    │
    └─► Retornar WizardStepResponse {current_step, is_complete, extracted_skills, next_step_hint}

GET /api/v1/wizard/summary (solo si current_step == 6)
    └─► Retornar {full_name, district, education, skills, interests, suggested_sectors}
```

---

## 7. Extracción NLP de Competencias Coloquiales

El proceso de extracción es el núcleo diferencial del tipo `primer_empleo`:

### Diccionario de Skills Coloquiales (muestra)
```python
soft_skills_map = {
    "puntual"              → "puntualidad",
    "responsable"          → "responsabilidad",
    "trabajo en equipo"    → "trabajo colaborativo",
    "aprendo rápido"       → "aprendizaje rápido",
    "ayudo en casa"        → "gestión doméstica",
    "vendo en el mercado"  → "ventas informales",
    "manejo caja"          → "manejo de efectivo",
    "atiendo clientes"     → "atención al cliente",
    "cocino"               → "preparación de alimentos",
    ...  # ~40 términos coloquiales peruanos
}
```

### Sugerencia de Sectores
Función `suggest_job_sectors(skills) → list[str]` retorna hasta 5 sectores compatibles (Comercio, Gastronomía, Construcción, Tecnología, Cuidado de personas, Manufactura, Transporte, Servicios).

---

## 8. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Secuencialidad del wizard | `step ≤ current_step + 1` → error 400 si intenta saltar pasos |
| Persistencia de estado | `wizard_progress` persiste entre sesiones; el trabajador puede retomar donde dejó |
| Deduplicación de skills | La lista acumulada no contiene duplicados |
| Profile completeness | Se recalcula en cada actualización; máximo 100% para primer_empleo |
| Tipo de trabajador forzado | El endpoint verifica `worker.worker_type == "primer_empleo"` (403 si no coincide) |

---

## 9. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Tasa de completitud del wizard | > 60% de usuarios llegan al paso 6 | `wizard_progress.current_step == 6` |
| Skills promedio extraídas por usuario | ≥ 3 skills al completar paso 3+4 | `len(wizard_progress.extracted_skills)` |
| Tiempo promedio de completitud del wizard | < 15 minutos | `wizard_progress.last_saved_at - workers.created_at` |

---

## 10. Pruebas Automatizadas

Archivo: `backend/tests/integration/test_api_wizard.py`
- `test_wizard_step_1_saves_progress`
- `test_wizard_step_3_extracts_skills`
- `test_wizard_cannot_skip_steps`
- `test_wizard_summary_requires_step_6_complete`
- `test_wizard_requires_primer_empleo_type`

---

*P-003 | Linku DRTPE-Junín · Implementado Sprint 2–3 · RF096–RF105*
