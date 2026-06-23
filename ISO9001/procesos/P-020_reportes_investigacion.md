# P-020 — Generación de Reportes de Investigación
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M09 — Reportes DRTPE
**RF Cubiertos:** RF136–RF145
**Sprint de implementación:** Sprint 4
**Componentes clave:**
- `backend/app/tasks/reports.py`
- `backend/app/services/reports/kpi_calculator.py`
- `backend/app/api/v1/admin/dashboard.py`

---

## 1. Propósito

Generar automáticamente los conjuntos de datos y reportes de investigación necesarios para la tesis académica y para los informes de gestión de la DRTPE-Junín, incluyendo KPIs calculados, estadísticas de usuarios y datos de colocación laboral.

---

## 2. Tipos de Reportes Generados

| Reporte | Frecuencia | Destinatario | Formato |
|---------|-----------|-------------|---------|
| Dashboard KPIs (7 indicadores) | Diaria 6AM + on-demand | Admin DRTPE | JSON (API) / UI Dashboard |
| Estadísticas de workers por tipo/distrito | On-demand | Admin DRTPE | JSON (API) |
| Dataset de investigación (CSV anonimizado) | Manual (por investigador) | Equipo investigador | CSV |
| Métricas del modelo ML (F1, DI, precisión) | On-demand | Admin DRTPE | JSON (API) |
| Reporte de equidad (logs DI) | Semanal | Admin DRTPE | JSON (API) |

---

## 3. Tarea Celery: Dataset de Investigación

```python
# En app/tasks/reports.py
@shared_task(name="tasks.generate_research_dataset")
def generate_research_dataset():
    """
    Genera CSV anonimizado para análisis estadístico de la tesis.
    Campos incluidos (sin PII):
    - worker_type, district, profile_completeness
    - has_embedding (bool), embedding_dim
    - applications_count, matches_count
    - days_to_first_contract (VIL)
    - survey_phase, income_change_pct (sin valores absolutos)
    
    Excluidos: full_name, DNI, teléfono, email, IP
    Cola: reports
    Worker: worker-reports
    """
```

---

## 4. Flujo del Proceso de Reportes

```
[Celery Beat — Diario 6:00 AM]
    └─► calculate_all_kpis(db)
            ├─► VIL, IVP, TF, RBS, TCC, IVM, TCSS
            ├─► Cachear en Redis "admin:dashboard:kpis" (TTL 1h)
            └─► structlog "kpis_calculated" {vil, ivp, tf, ...}

[Admin DRTPE] GET /api/v1/admin/dashboard
    └─► Leer desde caché Redis o recalcular

[Investigador] POST /api/v1/admin/generate-dataset
    └─► Encolar generate_research_dataset()
            └─► Cola "reports" → worker-reports
                    └─► CSV anonimizado → storage (GCS o local)

[Admin DRTPE] GET /api/v1/admin/model/metrics
    └─► SELECT FROM model_versions WHERE is_active=True
            └─► {version, worker_type, f1_score, precision, recall, deployed_at}
```

---

## 5. Modelo de Datos — `model_versions`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador |
| `version_tag` | VARCHAR(50) | Ej. "v1.0.0-primer-empleo" |
| `worker_type` | VARCHAR(20) | Para qué tipo de trabajador |
| `f1_score` | DECIMAL(5,4) | F1-score del modelo en el set de validación |
| `precision_score` | DECIMAL(5,4) | Precisión |
| `recall_score` | DECIMAL(5,4) | Recall |
| `is_active` | BOOLEAN | Versión actualmente en producción |
| `deployed_at` | TIMESTAMPTZ | Fecha de despliegue |

---

## 6. Seed de Datos de Investigación

Para facilitar las pruebas de los reportes, el sistema incluye un script de seed con **60 trabajadores realistas de Huancayo**:

| Tipo | Cantidad | Datos incluidos |
|------|---------|----------------|
| `primer_empleo` | 20 | Nombres reales, distritos, skills coloquiales, nivel educativo |
| `oficio` | 20 | Nombre, oficio, años de experiencia, calificación, portafolio |
| `experiencia` | 20 | Nombre, cargo, bio profesional, años de experiencia |

```bash
# Ejecutar seed de datos de investigación
python -m app.utils.seed_research
```

Todos los datos del seed usan `encrypt_field()` para la PII, replicando el comportamiento real del sistema.

---

## 7. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Anonimización en dataset | El CSV de investigación excluye todos los campos PII |
| Acceso restringido a ADMIN | Solo el rol ADMIN puede solicitar datasets y ver métricas del modelo |
| Cache para KPIs | Los KPIs no se recalculan por cada request — caché de 1 hora |
| Trazabilidad del cálculo | Cada ejecución de `calculate_all_kpis` registra el timestamp |
| RBS sin log de montos | El cálculo descifra en memoria; los valores absolutos no aparecen en ningún log |

---

## 8. Indicadores de Desempeño del Proceso

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Disponibilidad del cálculo de KPIs | Diaria sin fallos | Celery Beat + Flower |
| Tiempo de generación del dashboard | < 5 segundos (desde caché < 100ms) | Redis + endpoint timing |
| Dataset de investigación generado | 60 registros base (seed) + datos reales | `workers` count |

---

## 9. Conexión con la Tesis Académica

Los 7 KPIs calculados por este proceso son los **indicadores centrales de la tesis**:

| KPI | Hipótesis que valida |
|-----|---------------------|
| VIL | H1: El sistema reduce el tiempo de inserción laboral |
| IVP | H2: El sistema aumenta la visibilidad de perfiles informales |
| TF | H3: El sistema incrementa la tasa de formalización laboral |
| RBS | H4: Los usuarios reducen la brecha salarial después de usar el sistema |
| TCC | H5: El sistema facilita la creación de CVs digitales en usuarios sin experiencia |
| IVM | H6: Los trabajadores de oficio logran visibilidad digital en el marketplace |
| TCSS | H7: El sistema supera el problema de cold-start para usuarios sin historial |

---

*P-020 | Linku DRTPE-Junín · Implementado Sprint 4 · RF136–RF145*
