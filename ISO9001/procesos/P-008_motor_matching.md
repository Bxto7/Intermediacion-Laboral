# P-008 — Motor de Emparejamiento (Matching)
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M05 — Motor ML de Emparejamiento
**RF Cubiertos:** RF080–RF095
**Sprint de implementación:** Sprint 3
**Componentes clave:**
- `backend/app/api/v1/matching.py`
- `backend/app/ml/matching_engine/scorer.py`
- `backend/app/ml/equity_ranker/ranker.py`
- `backend/app/ml/explainer/explainer.py`

---

## 1. Propósito

Calcular el grado de compatibilidad entre el perfil de un trabajador y las ofertas de empleo activas, ordenar los resultados de mayor a menor compatibilidad y aplicar re-ranking de equidad para garantizar que trabajadores de todos los distritos tengan igualdad de oportunidades.

---

## 2. Fórmula de Score Combinado

```
combined_score = α × cosine_similarity + β × ml_score + γ × (avg_rating / 5.0)
```

### Pesos por tipo de trabajador

| `worker_type` | α (coseno) | β (ML) | γ (reputación) | Justificación |
|---------------|-----------|--------|----------------|---------------|
| `primer_empleo` | 0.65 | 0.35 | 0.00 | Sin historial laboral → reputación irrelevante |
| `experiencia` | 0.50 | 0.30 | 0.20 | Balance entre semántica, ML e historial |
| `oficio` | 0.45 | 0.25 | 0.30 | Reputación (avg_rating) es señal fuerte en oficios |

> **Estado actual del ml_score:** Fijo en 0.5 (stub). El modelo ML supervisado no está entrenado. El ranking efectivo lo domina la similitud coseno. Ver deuda técnica ML-STUB en CLAUDE.md.

---

## 3. Cálculo de Similitud Coseno

```python
# Implementación actual (Python/numpy — deuda técnica P1):
cosine_similarity = np.dot(worker_emb, offer_emb) / (
    np.linalg.norm(worker_emb) * np.linalg.norm(offer_emb)
)

# Implementación objetivo (pgvector — pendiente):
# SELECT id, 1 - (embedding <=> :worker_embedding) AS cosine_sim
# FROM job_offers
# WHERE is_active = true AND (expires_at IS NULL OR expires_at > now())
# ORDER BY embedding <=> :worker_embedding
# LIMIT :top_k
```

---

## 4. Entradas del Proceso

| Entrada | Fuente | Condición |
|---------|--------|-----------|
| `worker_id` | Path param | UUID del trabajador |
| `workers.embedding` | BD | vector(384); si NULL → cold start resolver |
| `job_offers.embedding` | BD | vector(384) de ofertas activas |
| `workers.worker_type` | BD | Determina pesos α, β, γ |
| `workers.avg_rating` | BD | Solo relevante si γ > 0 |
| `workers.extracted_skills` | BD (JSONB) | Para explicabilidad del match |
| `job_offers.required_skills` | BD (JSONB) | Para explicabilidad del match |

---

## 5. Salidas del Proceso

| Salida | Destino | Contenido |
|--------|---------|-----------|
| Lista top-K matches | Frontend (JSON) | `[{job_id, score, explanation, match_label}]` |
| `MatchEvent` | BD | Registro auditable de cada match procesado |
| `equity_audit_log` | BD | Disparate impact calculado y si se aplicó re-ranking |
| Notificación WebSocket | Canal Redis | `type: "new_match"` si hay matches nuevos |

---

## 6. Flujo del Proceso

```
[Trabajador autenticado] GET /api/v1/match/{worker_id}
    │
    ├─► Cargar worker de BD (verificar autorización)
    │
    ├─► [Si worker.embedding IS NULL]
    │       └─► resolve_cold_start(worker, db) → embedding sintético temporal
    │
    ├─► Cargar top_k × 5 ofertas activas con embedding
    │
    ├─► Por cada oferta:
    │       │
    │       ├─► cosine_similarity = np.dot/norm (deuda: debería ser pgvector <=>)
    │       ├─► ml_score = 0.5 (stub)
    │       ├─► reputation = worker.avg_rating / 5.0
    │       ├─► combined_score = α×coseno + β×ml + γ×reputación
    │       └─► explain_match(score, worker_skills, offer_skills, worker_type)
    │               └─► {matching_skills, missing_skills, extra_skills, message, label}
    │               └─► Labels: "Alta" (≥0.70) / "Media" (0.45–0.70) / "Baja" (<0.45)
    │
    ├─► Ordenar por combined_score DESC → top_K resultados
    │
    ├─► apply_equity_reranking(matches, group_field="district")
    │       │
    │       ├─► compute_disparate_impact(scores_grupo_A, scores_grupo_B)
    │       ├─► [Si DI < 0.80] → boost a grupos sub-representados
    │       └─► log_equity_audit(worker_id, worker_type, DI, applied)
    │
    ├─► Persistir MatchEvent por cada match (audit)
    │
    └─► Retornar top-K con scores, explicaciones y labels
```

---

## 7. Explicabilidad del Match

```python
explain_match(combined_score, worker_skills, offer_skills, worker_type) → dict

# Retorna:
{
    "matching_skills": ["atención al cliente", "trabajo en equipo"],  # skills en común
    "missing_skills": ["Excel avanzado"],                             # skills que le faltan
    "extra_skills": ["ventas informales"],                            # skills extra del worker
    "compatibility_label": "Alta",                                    # Alta/Media/Baja
    "message": "Tu perfil es muy compatible con esta oferta..."       # mensaje en español
}
```

---

## 8. Equidad Algorítmica (integración con P-014)

El motor de matching incluye un paso de re-ranking para reducir el sesgo geográfico:

```
compute_disparate_impact(scores_Huancayo, scores_El_Tambo_Chilca)
    = avg(scores_grupo_menor) / avg(scores_grupo_mayor)

Si DI < 0.80:
    → apply_equity_reranking → boost a workers de El Tambo y Chilca
    → log_equity_audit(applied=True)
```

Ver proceso detallado en [P-014](P-014_equidad_explicabilidad.md).

---

## 9. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Score en rango [0, 1] | Validar que combined_score no supere 1.0 |
| Autorización por ownership | Un worker solo puede ver sus propios matches |
| Cold start cubierto | Perfiles sin embedding tienen fallback sintético |
| Audit inmutable | `MatchEvent` registra cada cálculo para análisis retrospectivo |
| Errores no silenciados | `except Exception: pass` identificado como deuda (R1 FURPS+); pendiente de corrección |

---

## 10. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Tasa de matching exitoso (TCSS) | > 70% de usuarios primer_empleo/oficio con ≥1 match | `match_events` |
| Tiempo de respuesta del endpoint | < 2 segundos | Header `X-Process-Time` |
| Disparate impact promedio | ≥ 0.80 entre distritos | `equity_audit_log` |
| Cobertura de embeddings en ofertas activas | > 90% con embedding generado | `job_offers WHERE embedding IS NOT NULL` |

---

## 11. Pruebas Automatizadas

Archivo: `backend/tests/integration/test_api_matching.py`
- `test_combined_score_weights_primer_empleo` → α=0.65
- `test_combined_score_weights_oficio` → γ=0.30
- `test_matching_endpoint_requires_auth`
- `test_cold_start_generates_embedding`

---

*P-008 | Linku DRTPE-Junín · Implementado Sprint 3 · RF080–RF095*
