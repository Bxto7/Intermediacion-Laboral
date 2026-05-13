# Sprint 3 — Resumen de Implementación
**Sistema de Intermediación Laboral DRTPE-Junín**
**Fecha de cierre:** 2026-05-05
**Investigadores:** Rojas Peña W. / Tovar Sanchez C.

---

## Estado general

| Métrica | Resultado |
|---------|-----------|
| Tests totales | **266 pasando** |
| Cobertura de código | **80%** (umbral mínimo cumplido) |
| Errores de linting (ruff) | **0** |
| Docker Compose | ✅ Multi-worker + Beat + Grafana |

---

## Módulos implementados en Sprint 3

### M06 — Asistente de Identidad Laboral (RF096–RF110)

**CV PDF Generation** (`app/services/cv_builder/pdf_generator.py`)
- Generación de CVs en PDF usando Jinja2 + WeasyPrint
- 3 plantillas HTML diferenciadas por `worker_type`:
  - `primer_empleo.html` — diseño amigable, muestra habilidades del wizard y actividades
  - `oficio.html` — muestra portfolio visual, categoría de oficio y calificación
  - `experiencia.html` — formato profesional con experiencia laboral y educación
- Fallback a HTML bytes si WeasyPrint no está instalado (para tests)
- Cifrado AES-256: `decrypt_field` para `full_name` y `phone` antes de insertar en template

**Endpoints CV** (`app/api/v1/cv.py`)
- `POST /api/v1/cv/generate/{worker_id}` → encola tarea Celery `tasks.generate_cv`
- `GET /api/v1/cv/download/{worker_id}` → generación síncrona para desarrollo/testing
- Requiere `UserRole.WORKER` + verificación de propiedad

**Celery Task** (`app/tasks/cv_generator.py`)
- Cola dedicada: `cv_generation`
- Reintentos: máximo 3, backoff de 60s × (intento + 1)

---

### M05 — Motor ML de Emparejamiento (RF076–RF095)

**Matching Engine** (`app/api/v1/matching.py`)
- `GET /api/v1/match/{worker_id}` → retorna top-K ofertas con score y explicación
- Fórmula `combined_score` diferenciada por `worker_type`:
  - `primer_empleo`: (cosine=0.65, ml=0.35, reputation=0.00)
  - `experiencia`: (cosine=0.50, ml=0.30, reputation=0.20)
  - `oficio`: (cosine=0.45, ml=0.25, reputation=0.30)
- Cosine similarity desde embeddings pgvector cuando disponibles
- Skills del worker desde `WizardProgress` (primer_empleo) o `PortfolioEntry` (oficio)
- Auditoría: persiste `MatchEvent` por cada match procesado

**Cold-Start** (`app/ml/cold_start/resolver.py`)
- `resolve_cold_start(worker, db)` → genera embedding inicial sin historial
- Texto de perfil sintético diferenciado:
  - `primer_empleo`: desde respuestas del wizard (skills + intereses)
  - `oficio`: desde portfolio entries (skills + categoría + años)
  - `experiencia`: desde bio, job_title, años de experiencia

---

### M10 — Equidad y Explicabilidad (RF146–RF155)

**Equity Ranker** (`app/ml/equity_ranker/ranker.py`)
- `compute_disparate_impact(scores_a, scores_b)` → ratio entre grupos
- `apply_equity_reranking(matches, group_field)` → boost a grupos sub-representados
- Umbral: disparate impact < 0.80 activa re-ranking automático
- `log_equity_audit(worker_id, worker_type, di, applied)` → log estructurado

**Match Explainer** (`app/ml/explainer/explainer.py`)
- `explain_match(combined_score, worker_skills, offer_skills, worker_type)` → dict
- Labels de compatibilidad: `Alta` (≥0.70), `Media` (0.45–0.70), `Baja` (<0.45)
- Retorna: `matching_skills`, `missing_skills`, `extra_skills`, `message` en español

---

### M08 — Notificaciones (RF126–RF135)

**WebSocket** (`app/api/v1/ws_notifications.py`)
- `GET /ws/notifications/{user_id}?token=...` → conexión WebSocket autenticada
- Redis pub/sub en canal `notifications:{user_id}`
- `publish_notification(user_id, type, title, body, payload, redis)` → async
- Tipos soportados: `new_match`, `application_update`, `alert_job`, `message`, `cv_ready`
- Cierra con código 4001 si token inválido

**Modelos** (`app/models/notification.py`)
- `Notification`: user_id, worker_type, notification_type, title, body, payload (JSONB), is_read

---

### M07 — Alertas de Empleo (RF111–RF117)

**Job Alerts** (`app/services/matching/job_alerts.py`, `app/api/v1/alerts.py`)
- `POST /api/v1/alerts` → crea alerta (201)
- `GET /api/v1/alerts` → lista alertas del worker
- `DELETE /api/v1/alerts/{alert_id}` → desactiva (204)
- `process_alerts_for_new_offer(offer, db, redis)` → notifica a workers con alertas coincidentes
- Filtros: keywords (full-text), districts, trade_categories, salary_min
- Modelo `JobAlert`: keywords, districts, trade_categories, salary_min, worker_type

---

## Infraestructura

### Docker Compose multi-worker (`docker-compose.yml`)
- **4 workers Celery separados** por cola:
  - `worker-embeddings` → cola `embeddings`
  - `worker-cv` → cola `cv_generation`
  - `worker-notifications` → cola `notifications`
  - `worker-reports` → cola `reports`
- **Celery Beat** → scheduler de tareas periódicas
- **Flower** → monitoreo de tareas Celery (puerto 5555)
- **Prometheus** → scraping de métricas en `/metrics`
- **Grafana** → dashboards (puerto 3000), datasource Prometheus provisionado

### Celery Beat Schedule (`app/tasks/__init__.py`)
| Tarea | Frecuencia | Cola |
|-------|-----------|------|
| Regenerar embeddings | Diario 2:00 AM | embeddings |
| Procesar alertas | Cada hora | default |
| Calcular KPIs | Diario 6:00 AM | reports |
| Reindexar marketplace | Diario 3:00 AM | embeddings |
| Reentrenar modelo ML | Lunes 4:00 AM | default |
| Limpiar tokens expirados | Diario 1:00 AM | default |

### Monitoreo (`infra/`)
- `infra/prometheus/prometheus.yml` → scraping de API y Flower
- `infra/grafana/provisioning/datasources/prometheus.yml` → datasource automático

---

## Tests Sprint 3

| Archivo | Tests |
|---------|-------|
| `tests/unit/test_cv_generator.py` | 33 tests — PDF generator, equity ranker, explainer, job alerts unit |
| `tests/unit/test_cold_start.py` | 7 tests — cold-start por tipo, no PII en texto |
| `tests/unit/test_security.py` | Tests adicionales — file validator, resolve_cold_start |
| `tests/integration/test_job_alerts.py` | 6 tests — CRUD alertas, _alert_matches_offer |
| `tests/integration/test_websocket_notifications.py` | Tests — publish_notification, canales Redis |
| `tests/integration/test_api_matching.py` | Tests — combined_score weights, endpoints |

---

## Dependencias añadidas

```
weasyprint>=62.3          # Generación de PDFs
jinja2>=3.1.0             # Templates HTML para CVs
fakeredis[aioredis]>=2.20.0  # Redis mock para tests
aiosqlite>=0.20.0         # SQLite async para tests de integración
```

---

## RF cubiertos en Sprint 3

- **RF076–RF095** (M05): Motor de matching diferenciado por worker_type
- **RF096–RF110** (M06): CV automático desde wizard y portfolio
- **RF111–RF117** (M07): Alertas configurables de empleo
- **RF126–RF135** (M08): Notificaciones WebSocket en tiempo real
- **RF146–RF155** (M10): Equidad (disparate impact) y explicabilidad de matches

---

*Próximo: Sprint 4 — Búsqueda semántica marketplace, integración DRTPE, reportes admin*
