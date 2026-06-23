# P-007 — Generación Automática de Embeddings Vectoriales
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M04 / M05 — NLP / Motor de Emparejamiento
**RF Cubiertos:** RF076–RF079
**Sprint de implementación:** Sprint 2 (real) — Sprint 1 (stub)
**Componentes clave:**
- `backend/app/nlp/embeddings/generator.py`
- `backend/app/tasks/embeddings.py`
- `backend/app/ml/cold_start/resolver.py`

---

## 1. Propósito

Generar representaciones vectoriales densas de 384 dimensiones para perfiles de trabajadores y ofertas de empleo, habilitando el emparejamiento semántico mediante similitud coseno en PostgreSQL/pgvector. Estos embeddings son la base matemática del motor de matching.

---

## 2. Modelo NLP Utilizado

| Atributo | Valor |
|----------|-------|
| **Modelo** | `paraphrase-multilingual-MiniLM-L12-v2` |
| **Biblioteca** | sentence-transformers 3.3 |
| **Dimensión del vector** | 384 |
| **Soporte de idiomas** | Multilingüe (incluye español) |
| **Normalización** | L2 (normalize_embeddings=True) — norma del vector ≈ 1.0 |
| **Carga** | Singleton — una sola instancia al inicio de la app (startup event) |

---

## 3. Textos de Perfil por Tipo de Trabajador

La calidad del matching depende del texto construido antes de generar el embedding:

### Primer Empleo
```python
f"primer empleo | {district} | educación: {education_level} | "
f"habilidades: {', '.join(skills)} | intereses: {', '.join(interests)}"
```
Datos desde: `wizard_progress.extracted_skills` + `wizard_progress.answers` (intereses/educación).

### Oficio
```python
f"{trade_category} | {years_experience} años | {district} | "
f"{avg_rating:.1f}/5.0 | trabajos: {portfolio_count} | "
f"habilidades: {', '.join(portfolio_skills)}"
```
Datos desde: consolidación de `portfolio_entries.extracted_skills` (hasta 6 entradas públicas).

### Experiencia
```python
f"{job_title} | {years_experience} años | {district} | {bio}"
```
Datos desde: `workers.job_title`, `workers.bio`, `workers.years_experience`.

### Oferta de Empleo
```python
f"{title} | {modality} | {district} | "
f"skills requeridas: {', '.join(required_skills)} | {description[:500]}"
```
Datos desde: `job_offers` — normalizado antes del embedding.

---

## 4. Arquitectura de Generación (Celery Async)

```
[Evento trigger]
(perfil completado / oferta creada / paso 6 wizard)
    │
    ▼
Celery task encolada → cola "embeddings"
    │
    ▼
Worker: worker-embeddings (contenedor dedicado)
    │
    ├─► Abrir sesión BD síncrona (SQLAlchemy sync — Celery no es async)
    ├─► Cargar worker/oferta por ID
    ├─► Construir texto de perfil (build_*_profile_text)
    ├─► normalize_text(profile_text) → pipeline NLP completo
    ├─► generate_embedding(normalized_text) → list[float] 384 dims
    ├─► Actualizar workers.embedding / job_offers.embedding en BD
    └─► structlog "worker_embedding_generated" {worker_id, worker_type, profile_text_length}
```

---

## 5. Tareas Celery Disponibles

| Tarea | Cola | Descripción |
|-------|------|-------------|
| `generate_worker_embedding(worker_id)` | `embeddings` | Genera embedding individual para un trabajador |
| `generate_job_embedding(job_offer_id)` | `embeddings` | Genera embedding para una oferta de empleo |
| `generate_portfolio_entry_embedding(entry_id)` | `embeddings` | Genera embedding para una entrada de portafolio |
| `generate_listing_embedding(listing_id)` | `embeddings` | Genera embedding para un listing del marketplace |
| `regenerate_all_embeddings(worker_type)` | `embeddings` | Re-indexado masivo por tipo (batches de 50) |

---

## 6. Celery Beat — Re-indexado Automático

| Tarea | Frecuencia | Hora |
|-------|-----------|------|
| `regenerate_all_embeddings` | Diaria | 02:00 AM Lima |
| `reindex_marketplace` | Diaria | 03:00 AM Lima |
| `retrain_matching_model` | Semanal (lunes) | 04:00 AM Lima |

---

## 7. Cold Start — Perfiles sin Historial

Para trabajadores que inician sin suficiente información para un embedding de calidad, `ml/cold_start/resolver.py` genera un perfil sintético:

```python
# primer_empleo: desde respuestas básicas del wizard (pasos 1-2)
# oficio: desde trade_category + district (sin portfolio aún)
# experiencia: desde job_title + district (sin bio aún)
```
El embedding de cold start es reemplazado automáticamente cuando el perfil se completa (paso 6 del wizard o primera entrada de portafolio).

---

## 8. Almacenamiento e Índice pgvector

```sql
-- Columna en workers (y job_offers, portfolio_entries, service_listings)
embedding vector(384)

-- Índice HNSW para búsqueda aproximada eficiente
CREATE INDEX idx_workers_embedding ON workers
  USING hnsw (embedding vector_cosine_ops)
  WITH (m=16, ef_construction=64);
```

El operador de distancia coseno en pgvector es `<=>`.

> **Deuda técnica (P1 auditoría FURPS+):** El matching actual calcula similitud coseno en Python (numpy) en lugar de usar el operador `<=>` de pgvector con el índice HNSW. El índice existe pero no se usa. Ver [06_mejora_continua.md](../06_mejora_continua.md).

---

## 9. Fallback ante Fallo del Modelo

Si el modelo `paraphrase-multilingual-MiniLM-L12-v2` no puede cargarse (falta de memoria o error de instalación), el sistema usa un fallback SHA256 para no romper el flujo:

```python
# Fallback: hash SHA256 del texto → lista de 384 floats deterministas
```
El log registra `"embedding_fallback_used"`. Los matches con embeddings de fallback tienen menor calidad semántica pero no causan error.

---

## 10. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Trabajadores con embedding generado | > 80% del total | `COUNT(*) WHERE embedding IS NOT NULL / COUNT(*)` |
| Tasa de éxito de tareas Celery | > 99% | Flower → "Successful" tasks |
| Tiempo de generación por embedding | < 500ms por texto | Celery task duration |

---

## 11. Pruebas Automatizadas

Archivo: `backend/tests/unit/test_embeddings.py`
- `test_generate_embedding_returns_384_dims`
- `test_normalize_embeddings_unit_length` → norma L2 ≈ 1.0
- `test_generate_embeddings_batch_consistent`
- `test_local_dict_cache_loaded_once`

---

*P-007 | Linku DRTPE-Junín · Implementado Sprint 2 · RF076–RF079*
