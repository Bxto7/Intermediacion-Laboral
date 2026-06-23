# P-011 — Sistema de Alertas de Empleo
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M07 — Alertas de Empleo
**RF Cubiertos:** RF111–RF117
**Sprint de implementación:** Sprint 3
**Componentes clave:**
- `backend/app/api/v1/alerts.py`
- `backend/app/services/matching/job_alerts.py`

---

## 1. Propósito

Notificar proactivamente a los trabajadores cuando se publiquen ofertas de empleo que coincidan con sus preferencias de búsqueda (keywords, distritos, categorías de oficio, salario mínimo), sin que el trabajador deba buscar activamente.

---

## 2. Estructura de una Alerta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `keywords` | list[str] | Palabras clave a monitorear en títulos/descripciones de ofertas |
| `districts` | list[District] | Distritos de interés (Huancayo/El Tambo/Chilca) |
| `trade_categories` | list[TradeCategory] | Categorías de oficio (solo para tipo `oficio`) |
| `salary_min` | Decimal | Salario mínimo deseado |
| `worker_type` | WorkerType | Tipo del trabajador (para filtro de ofertas compatibles) |
| `is_active` | bool | Las alertas se desactivan con DELETE (no se borran físicamente) |

---

## 3. Flujo del Proceso

### 3.1 Gestión de Alertas por el Trabajador
```
[Trabajador autenticado]
    │
    ├─► POST /api/v1/alerts {keywords, districts, trade_categories, salary_min}
    │       └─► Crear JobAlert; retornar 201
    │
    ├─► GET /api/v1/alerts
    │       └─► Listar alertas activas del trabajador
    │
    └─► DELETE /api/v1/alerts/{alert_id}
            └─► Desactivar alerta (is_active=False); retornar 204
```

### 3.2 Procesamiento Automático al Publicar una Oferta
```
[Sistema] Celery Beat o trigger al crear job_offer
    │
    └─► process_alerts_for_new_offer(offer, db, redis)
            │
            ├─► Obtener todas las alertas activas
            ├─► Por cada alerta:
            │       │
            │       ├─► _alert_matches_offer(alert, offer):
            │       │       ├─► keywords: full-text search en title/description
            │       │       ├─► districts: intersección con offer.district
            │       │       ├─► trade_categories: intersección con offer.worker_type_target
            │       │       └─► salary_min: offer.salary_min ≥ alert.salary_min
            │       │
            │       └─► [Si coincide] → publish_notification(user_id, "alert_job", ...)
            │               └─► Canal Redis pub/sub → WebSocket (P-012)
            │
            └─► Registrar matches en structlog
```

---

## 4. Lógica de Coincidencia Alerta–Oferta (`_alert_matches_offer`)

| Filtro | Condición de coincidencia |
|--------|--------------------------|
| Keywords | Al menos una keyword aparece en `offer.title` o `offer.description` (búsqueda full-text case-insensitive) |
| Districts | `offer.district IN alert.districts` (si alert.districts no es vacío) |
| Trade categories | `offer.worker_type_target IN alert.trade_categories` (si no es vacío) |
| Salary min | `offer.salary_min >= alert.salary_min` (si alert.salary_min no es None) |

Todos los filtros no vacíos deben cumplirse simultáneamente (AND lógico).

---

## 5. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Autorización por worker | Un trabajador solo gestiona sus propias alertas |
| Soft-delete de alertas | Desactivar no borra historial |
| Procesamiento asíncrono | `process_alerts_for_new_offer` no bloquea la creación de la oferta |
| Rate limiting | Las notificaciones de alerta usan el canal Redis pub/sub; no hay límite de envío (el trabajador controla sus alertas) |

---

## 6. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Alertas activas por trabajador | Media 1–3 alertas | `COUNT(*) FROM job_alerts WHERE is_active=True GROUP BY worker_id` |
| Tiempo de notificación tras publicación | < 60 segundos | Celery Beat corre cada hora; trigger inmediato al crear oferta |
| Tasa de conversión alerta → postulación | Objetivo de investigación | Correlación `job_alerts` vs `applications` |

---

## 7. Pruebas Automatizadas

Archivo: `backend/tests/integration/test_job_alerts.py`
- `test_create_alert_returns_201`
- `test_list_alerts`
- `test_delete_alert_returns_204`
- `test_alert_matches_offer_keywords`
- `test_alert_no_match_wrong_district`

---

*P-011 | Linku DRTPE-Junín · Implementado Sprint 3 · RF111–RF117*
