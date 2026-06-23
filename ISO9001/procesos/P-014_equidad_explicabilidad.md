# P-014 — Equidad Algorítmica y Explicabilidad del Matching
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M10 — Equidad y Explicabilidad
**RF Cubiertos:** RF146–RF155
**Sprint de implementación:** Sprint 3 (ranker/explainer) + Sprint 5 (visible al usuario)
**Componentes clave:**
- `backend/app/ml/equity_ranker/ranker.py`
- `backend/app/ml/explainer/explainer.py`
- `backend/app/api/v1/matching.py` (integración)

---

## 1. Propósito

Garantizar que el motor de matching no discrimine sistemáticamente a trabajadores por razones geográficas (distrito) u otras características del grupo, y proporcionar al trabajador una explicación comprensible de por qué fue emparejado con cada oferta.

---

## 2. Equidad Algorítmica — Disparate Impact

### Concepto
El **Disparate Impact (DI)** mide si un grupo recibe scores de matching significativamente menores que otro grupo. Un DI < 0.80 (el "80% rule" estándar en IA equitativa) indica discriminación estadística que activa el re-ranking.

### Fórmula
```
DI = avg_score(grupo_desfavorecido) / avg_score(grupo_favorecido)

Umbral: DI < 0.80 → re-ranking aplicado
```

### Grupos monitoreados
- **Geográfico:** Huancayo vs El Tambo/Chilca (El Tambo y Chilca históricamente tienen menor visibilidad)
- **Por tipo:** `primer_empleo` vs `experiencia` (los primeros tienen embeddings más débiles)

---

## 3. Re-ranking de Equidad

```python
apply_equity_reranking(matches: list[Match], group_field: str = "district") -> list[Match]:
    │
    ├─► compute_disparate_impact(scores_A, scores_B)
    │
    ├─► [Si DI < 0.80]:
    │       ├─► Identificar grupo sub-representado
    │       ├─► Boost a matches del grupo desfavorecido:
    │       │       adjusted_score = score × (1 + boost_factor)
    │       └─► Re-ordenar lista por adjusted_score
    │
    └─► log_equity_audit(worker_id, worker_type, DI, applied=True/False)
            └─► Tabla equity_audit_log: auditoría inmutable
```

---

## 4. Estado de Equidad Visible al Usuario (RF150)

```python
GET /api/v1/match/{worker_id}/equity-status

# Respuesta al usuario (lenguaje positivo y explicativo):
{
    "equity_adjustments_applied": 2,
    "total_searches_analyzed": 10,
    "message": "El sistema aplicó ajustes de visibilidad en 2 de tus 10 últimas búsquedas 
                para garantizar que trabajadores de todos los distritos tengan igualdad 
                de oportunidades.",
    "disparate_impact_avg": 0.83,
    "explanation": "El sistema de equidad garantiza que trabajadores de El Tambo y Chilca 
                   tengan la misma visibilidad que los de Huancayo central."
}
```

---

## 5. Explicabilidad del Match (`explain_match`)

```python
explain_match(combined_score, worker_skills, offer_skills, worker_type) -> dict:

# Retorna:
{
    "matching_skills": ["atención al cliente", "trabajo en equipo"],
    "missing_skills": ["Excel avanzado"],
    "extra_skills": ["ventas informales"],
    "compatibility_label": "Alta",   # Alta (≥0.70) / Media (0.45–0.70) / Baja (<0.45)
    "message": "Tu perfil es muy compatible: tienes 2 de las 3 habilidades requeridas."
}
```

Los labels de compatibilidad se muestran en la UI del trabajador en la lista de matches.

---

## 6. Modelo de Datos — `equity_audit_log`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador |
| `worker_id` | UUID | Trabajador evaluado |
| `worker_type` | VARCHAR(20) | Tipo del trabajador |
| `disparate_impact` | DECIMAL(5,4) | Valor DI calculado |
| `reranking_applied` | BOOLEAN | Si se aplicó el re-ranking |
| `group_field` | VARCHAR(50) | Campo evaluado (district, worker_type) |
| `created_at` | TIMESTAMPTZ | Timestamp del cálculo |

---

## 7. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Umbral explícito | DI < 0.80 está codificado como constante — no configurable sin revisión del equipo investigador |
| Audit log inmutable | `equity_audit_log` no tiene UPDATE/DELETE — trazabilidad completa |
| Lenguaje no alarmante | El mensaje al usuario es positivo y educativo, no técnico |
| Re-ranking no degrada calidad total | El boost es moderado; el score base sigue siendo el dominante |
| Autorización | Solo el propio worker puede ver su estado de equidad (`worker.user_id == token.sub`) |

---

## 8. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Disparate impact promedio | ≥ 0.80 entre distritos | `equity_audit_log.disparate_impact` media móvil |
| Frecuencia de re-ranking activado | < 30% de las búsquedas | `COUNT WHERE reranking_applied=True / COUNT total` |
| Distribución de matches por distrito | Desviación < 10% entre Huancayo y El Tambo/Chilca | Análisis de `match_events` por district |

---

## 9. Pruebas Automatizadas

Archivo: `backend/tests/unit/test_cv_generator.py` (incluye equity ranker)
- `test_compute_disparate_impact_below_threshold`
- `test_apply_equity_reranking_boosts_subgroup`
- `test_log_equity_audit_records_event`
- `test_equity_status_positive_message`

---

*P-014 | Linku DRTPE-Junín · Implementado Sprint 3–5 · RF146–RF155*
