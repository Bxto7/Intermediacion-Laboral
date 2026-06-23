# P-013 — Panel Administrativo DRTPE y KPIs de Investigación
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M09 — Reportes DRTPE
**RF Cubiertos:** RF136–RF145
**Sprint de implementación:** Sprint 4
**Componentes clave:**
- `backend/app/api/v1/admin/dashboard.py`
- `backend/app/services/reports/kpi_calculator.py`
- `frontend/src/admin/AdminDashboard.tsx`
- `frontend/src/admin/KPIGlobe.tsx` (Three.js)

---

## 1. Propósito

Proporcionar a los administradores de la DRTPE-Junín un panel de control con los 7 KPIs de la tesis calculados automáticamente desde los datos reales del sistema, permitiendo monitorear el impacto de la intervención tecnológica en la reducción de brechas de empleo.

---

## 2. KPIs de la Tesis (7 indicadores)

### KPI 1 — VIL: Velocidad de Inserción Laboral
```sql
SELECT worker_type,
    AVG(EXTRACT(EPOCH FROM (c.signed_at - w.created_at)) / 86400.0) AS avg_days,
    COUNT(*) AS n
FROM contracts c JOIN workers w ON c.worker_id = w.id
WHERE c.contract_number = 1 AND c.signed_at IS NOT NULL
GROUP BY worker_type
```
**Unidad:** días promedio desde registro hasta primer contrato, por tipo de trabajador.

---

### KPI 2 — IVP: Índice de Visibilidad de Perfil
```sql
SELECT worker_type,
    COUNT(sl.id) AS appearances,
    ROUND(100.0 * COUNT(sl.id) / (SELECT COUNT(*) FROM search_logs), 2) AS ivp_percent
FROM search_logs sl JOIN workers w ON sl.worker_id = w.id
GROUP BY worker_type
```
**Unidad:** % de apariciones en resultados de búsqueda, por tipo de trabajador.

---

### KPI 3 — TF: Tasa de Formalización
```sql
SELECT worker_type,
    COUNT(DISTINCT w.id) AS total,
    COUNT(DISTINCT c.worker_id) AS with_contract,
    ROUND(100.0 * COUNT(DISTINCT c.worker_id) / NULLIF(COUNT(DISTINCT w.id), 0), 2) AS tasa
FROM workers w LEFT JOIN contracts c ON c.worker_id = w.id
GROUP BY worker_type
```
**Unidad:** % de trabajadores con al menos un contrato, por tipo.

---

### KPI 4 — RBS: Reducción Brecha Salarial
```python
# Requiere descifrado AES en memoria — NUNCA loguear datos económicos
income_pre = float(decrypt_field(row.income_pre_encrypted))
income_post = float(decrypt_field(row.income_post_encrypted))
change_pct = ((income_post - income_pre) / income_pre) * 100
```
**Fuente:** `economic_surveys` con fases `pre` y `post`, consentimiento Ley 29733 obligatorio.
**Unidad:** % de variación de ingreso mensual (pre vs post intervención).

---

### KPI 5 — TCC: Tasa de Completitud de CV
```sql
SELECT worker_type,
    COUNT(DISTINCT w.id) AS total,
    COUNT(DISTINCT gc.worker_id) AS with_cv,
    ROUND(100.0 * COUNT(DISTINCT gc.worker_id) / NULLIF(COUNT(DISTINCT w.id), 0), 2) AS tcc
FROM workers w LEFT JOIN generated_cvs gc ON gc.worker_id = w.id
WHERE w.worker_type IN ('primer_empleo', 'oficio')
GROUP BY worker_type
```
**Unidad:** % de trabajadores (primer_empleo y oficio) con al menos un CV generado.

---

### KPI 6 — IVM: Índice de Visibilidad en Marketplace
```sql
SELECT
    ROUND(100.0 * COUNT(DISTINCT sl.id) / NULLIF(COUNT(DISTINCT w.id), 0), 2) AS ivm_percent,
    COUNT(DISTINCT sl.id) AS active_listings,
    COUNT(DISTINCT w.id) AS total_oficio
FROM workers w
LEFT JOIN service_listings sl ON sl.worker_id = w.id AND sl.is_active = true
WHERE w.worker_type = 'oficio'
```
**Unidad:** % de trabajadores de oficio con al menos un listing activo en el marketplace.

---

### KPI 7 — TCSS: Tasa de Cold-Start Superado
```sql
SELECT worker_type,
    COUNT(DISTINCT w.id) AS total,
    COUNT(DISTINCT me.worker_id) AS with_match,
    ROUND(100.0 * COUNT(DISTINCT me.worker_id) / NULLIF(COUNT(DISTINCT w.id), 0), 2) AS tcss
FROM workers w LEFT JOIN match_events me ON me.worker_id = w.id
WHERE w.worker_type IN ('primer_empleo', 'oficio')
GROUP BY worker_type
```
**Unidad:** % de usuarios primer_empleo/oficio con al menos un match exitoso (cold start superado).

---

## 3. Flujo del Proceso

```
[Celery Beat — diario 6:00 AM Lima]
    └─► calculate_all_kpis(db) → calcula los 7 KPIs
            └─► Cachear en Redis "admin:dashboard:kpis" (TTL 1 hora)

[Admin DRTPE] GET /api/v1/admin/dashboard
    │
    ├─► Verificar rol ADMIN (require_role) — 403 si no es admin
    ├─► Intentar leer caché Redis "admin:dashboard:kpis"
    ├─► [Cache miss] → recalcular + actualizar caché
    └─► Retornar DashboardResponse {vil, ivp, tf, rbs, tcc, ivm, tcss, calculated_at}

[Admin DRTPE] GET /api/v1/admin/workers/stats
    │
    └─► Estadísticas por tipo + distrito:
            {worker_type, district, total, avg_completeness, available}
```

---

## 4. Acceso al Panel (Seguridad)

| Condición | Resultado |
|-----------|-----------|
| Sin token | 401 |
| Token de WORKER o EMPLOYER | 403 |
| Token de ADMIN | 200 — acceso completo |
| `GET /api/v1/admin/model/metrics` | Solo ADMIN — métricas F1/precision/recall del modelo ML |

Todos los endpoints bajo `/api/v1/admin/` tienen `dependencies=[Depends(require_role(UserRole.ADMIN))]` en el router base.

---

## 5. Dashboard Frontend (AdminDashboard.tsx)

| Componente | Tecnología | Descripción |
|-----------|-----------|-------------|
| KPIGlobe | Three.js + @react-three/fiber | Globo 3D interactivo con distribución geográfica de trabajadores |
| Gráficas de KPIs | Recharts | Barras y líneas para VIL, TF, TCC, TCSS |
| Tabla de stats | shadcn/ui | Datos por tipo + distrito con avg_completeness |

---

## 6. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| RBAC estricto | Solo ADMIN puede acceder; verificado en router base |
| Caché de 1 hora | Los KPIs son costosos; no se recalculan por cada request |
| RBS sin log de datos económicos | El cálculo descifra en memoria y no loguea montos |
| Retorno seguro con BD vacía | Cada KPI retorna 0 en lugar de lanzar excepción cuando no hay datos |
| `calculated_at` en timestamp | Permite al admin saber cuándo fue el último cálculo |

---

## 7. Indicadores de Desempeño del Proceso

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Tiempo de cálculo de KPIs | < 5 segundos | Celery task duration |
| Frecuencia de actualización | Diaria (6AM) + on-demand | Celery Beat + endpoint |
| Disponibilidad del panel | > 99% durante horario hábil | Prometheus `http_requests_total` |

---

## 8. Pruebas Automatizadas

Archivo: `backend/tests/unit/test_kpi_calculator.py`
- `test_calculate_vil_returns_by_type`
- `test_calculate_tcc_only_primer_empleo_oficio`
- `test_calculate_ivm_only_oficio`
- `test_rbs_decrypts_correctly`
- `test_no_kpi_raises_with_empty_db`

Archivo: `backend/tests/integration/test_api_admin_dashboard.py`
- `test_dashboard_without_token_returns_401`
- `test_dashboard_with_worker_token_returns_403`
- `test_dashboard_with_admin_token_returns_200`

---

*P-013 | Linku DRTPE-Junín · Implementado Sprint 4 · RF136–RF145*
