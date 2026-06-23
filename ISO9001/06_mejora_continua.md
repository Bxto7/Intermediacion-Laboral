# ISO 9001:2015 — Cláusula 10
## Mejora Continua — Hallazgos de Auditoría y Plan de Acción

**Sistema:** Linku — Sistema de Intermediación Laboral DRTPE-Junín
**Revisión:** 1.0 | Fecha: 2026-06-23
**Fuentes:** Auditoría FURPS+ (Sprint 5), Auditoría OWASP (Sprint 5), SonarQube

---

## 10.1 No conformidades y acciones correctivas

Las no conformidades se gestionan a través de la tabla de Bugs/Deuda del `CLAUDE.md` y se priorizan para corrección en los sprints siguientes.

### Tabla de No Conformidades Activas

| ID | Hallazgo | Categoría FURPS+ | Severidad | Estado | Sprint Objetivo |
|----|---------|-----------------|-----------|--------|----------------|
| **NCI-001** | Motor de matching calcula coseno en Python (numpy) en lugar de usar operador `<=>` de pgvector con índice HNSW | Performance (P1) | Alta | Pendiente | Sprint 6 |
| **NCI-002** | WeasyPrint síncrono en `GET /cv/download` bloquea el event loop async | Reliability/Performance (R2, P2) | Alta | Pendiente | Sprint 6 |
| **NCI-003** | Frontend (~9.039 LOC) sin pruebas automatizadas — 0 archivos `*.test.*` | Supportability (S1) | Alta | Pendiente | Sprint 6 |
| **NCI-004** | `except Exception: pass` en matching.py silencia errores de embedding y de persistencia de MatchEvent | Reliability (R1) | Alta | Pendiente | Sprint 6 |
| **NCI-005** | CV tipo `experiencia` sale sin experiencias/educación/skills (datos parseados no cableados) | Functionality (F2) | Media | Pendiente | Sprint 6 |
| **NCI-006** | `ml_score` fijo en 0.5 (modelo ML no entrenado) | Functionality (F1) | Alta | Pendiente | Sprint 6+ |
| **NCI-007** | Texto libre (bio, portafolio) sin verificación de autoescape HTML en portafolio público | Plus/Seguridad (+2) | Media | Verificar | Sprint 6 |
| **NCI-008** | No hay refresh automático del access token en el interceptor Axios | Reliability (R3) | Media | Pendiente | Sprint 6 |
| **NCI-009** | Imports diferidos dentro de funciones y loops en matching.py y pdf_generator.py | Supportability (S2) | Media | Pendiente | Sprint 6 |
| **NCI-010** | Lógica de negocio del matching en el router (no en servicio de dominio) | Plus (+3) | Media | Pendiente | Sprint 6 |
| **NCI-011** | Desajuste ruta/payload NLP wizard front (`/nlp/extract-skills`) vs back (`/nlp/extract-skills/wizard`) | Functionality (F3) | Media | Verificar | Sprint 6 |

---

## 10.2 Plan de Acciones Correctivas Priorizadas

### Prioridad 1 — Alta (Sprint 6)

#### NCI-001: Migrar matching a pgvector `<=>`
```python
# ANTES (Python/numpy):
cosine = np.dot(worker_emb, offer_emb) / (np.linalg.norm(worker_emb) * np.linalg.norm(offer_emb))

# DESPUÉS (pgvector — usar el índice HNSW):
SELECT id, title, 1 - (embedding <=> :worker_embedding) AS cosine_sim
FROM job_offers
WHERE is_active = true AND (expires_at IS NULL OR expires_at > now())
ORDER BY embedding <=> :worker_embedding
LIMIT :top_k
```
**Impacto:** Habilita el índice HNSW ya creado; escala a miles de ofertas sin degradación lineal.
**Archivo:** `backend/app/api/v1/matching.py` líneas 101-114.

#### NCI-002: Mover WeasyPrint a executor
```python
# DESPUÉS (offload CPU-bound):
import asyncio
loop = asyncio.get_event_loop()
pdf_bytes = await loop.run_in_executor(None, generate_cv_pdf_sync, worker_id)
```
**Impacto:** El event loop async no se bloquea durante el render del PDF.
**Archivo:** `backend/app/api/v1/cv.py` (endpoint `download`).

#### NCI-003: Pruebas frontend
```
Tecnología: Vitest + React Testing Library
Cobertura mínima inicial: 50% de componentes críticos
Componentes prioritarios:
  - LoginPage (flujo de login)
  - wizard/Step3 (extracción NLP)
  - AuthGuard (redirección)
  - MatchesPage (renderizado de resultados)
```

#### NCI-004: Eliminar errores silenciados
```python
# ANTES:
except Exception: pass   # en matching.py:113-114

# DESPUÉS:
except Exception as e:
    logger.error("cosine_calculation_failed", error=str(e), offer_id=str(offer.id))
    # decidir: continuar con score=0 o propagar
```
**Archivo:** `backend/app/api/v1/matching.py` líneas 113-114 y 161-164.

---

### Prioridad 2 — Media (Sprint 6)

#### NCI-005: Cablear datos parseados al CV experiencia
```python
# En _build_template_context para worker_type == "experiencia":
# Obtener los campos parseados más recientes de la tabla
# (necesita nueva tabla parsed_cv_data o campo en workers)
context["work_experiences"] = worker.parsed_work_experiences or []
context["education"] = worker.parsed_education or []
context["skills"] = worker.parsed_skills or []
```
**Archivo:** `backend/app/services/cv_builder/pdf_generator.py` líneas 152-168.

#### NCI-007: Verificar autoescape Jinja2
```python
# Verificar en pdf_generator.py y en el endpoint de portafolio público:
env = jinja2.Environment(autoescape=True)  # debe ser True
# Para texto libre del usuario (bio, description) aplicar:
# {{ description | e }}  en las plantillas HTML
```

#### NCI-008: Refresh automático en Axios
```typescript
// En frontend/src/api/client.ts — interceptor 401:
// Si el error es 401 Y tenemos refresh_token:
//   1. POST /auth/refresh
//   2. Guardar nuevos tokens
//   3. Reintentar el request original
// Si el refresh también falla → limpiar sesión → /login
```

#### NCI-011: Alinear ruta NLP wizard
```typescript
// frontend/src/modules/primer-empleo/wizard/steps/Step3.tsx
// Verificar que llama a:
//   POST /api/v1/nlp/extract-skills/wizard  (no /nlp/extract-skills)
//   body: {step: 3, text: "..."}            (no {user_text: "...", worker_type: "..."})
```

---

## 10.3 Mejoras de Proceso Continuo

| Mejora | Descripción | Beneficio |
|--------|-------------|-----------|
| CI/CD con pytest automático | Ejecutar `pytest --cov=app --cov-fail-under=80` en cada PR | Prevenir regresiones |
| SonarQube en CI | Ejecutar análisis SonarQube en cada PR (falla si Quality Gate falla) | Mantener rating A |
| Rotación programada de AES_KEY | Script `rotate_aes_key.py` ejecutado semestralmente | Reducir riesgo de compromiso de clave |
| Dataset de investigación automático | Tarea Celery semanal para dataset CSV anonimizado | Datos actualizados para análisis |
| Monitoreo de DI (disparate impact) | Alerta automática si DI < 0.70 (umbral de emergencia) | Detección temprana de sesgo |

---

## 10.4 Deuda Técnica Resuelta por Sprint

| Sprint | Deuda resuelta |
|--------|---------------|
| Sprint 2 | Issue CRÍTICO: AES_KEY placeholder; Issue ALTO: reset contraseña no invalidaba todos los tokens; Rate limiting con IP proxy; 3 schemas sin validación Pydantic |
| Sprint 3 | CV PDF generado como bytes reales (WeasyPrint real); Celery multi-worker; Equity ranker implementado; WebSocket con límite de conexiones |
| Sprint 4 | consent_records Ley 29733; Rate limiting global 1000 req/min; Panel admin RBAC; Encuestas económicas cifradas |
| Sprint 5 | Moderación de marketplace; RF023 cambio de tipo con confirmación; RF034 soft-delete de cuenta; RF150 equidad visible al usuario; Seed de 60 trabajadores realistas |

---

## 10.5 Ciclo PDCA del Sistema

```
PLANIFICAR (P)                    HACER (H)
─────────────────────────        ─────────────────────────
Definir RF/RNF por sprint        Implementar en sprints 1–5
Identificar riesgos (§6.1)       Pruebas: pytest ≥80%
Establecer objetivos (§6.2)      Linting: ruff check
Diseñar procesos P-001..P-020    SonarQube analysis

ACTUAR (A)                        VERIFICAR (V)
─────────────────────────        ─────────────────────────
Aplicar correcciones (§10.1)     Auditoría FURPS+ (80/100)
Actualizar CLAUDE.md             Auditoría OWASP
Actualizar ISO 9001 docs         Revisión por sprint (§9.3)
Priorizar NCI en próximo sprint  Dashboard KPIs (§9.1)
```

---

*Linku — DRTPE-Junín · ISO 9001:2015 Cláusula 10 · Huancayo 2026*
