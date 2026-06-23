# P-017 — Integración con la Bolsa de Trabajo DRTPE
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M12 — Integración Institucional
**RF Cubiertos:** RF161–RF165
**Sprint de implementación:** Sprint 4 (stub funcional)
**Componentes clave:**
- `backend/app/integrations/drtpe/connector.py`
- `backend/app/tasks/reports.py` (`sync_drtpe_offers_task`)

---

## 1. Propósito

Sincronizar el sistema Linku con la Bolsa de Trabajo oficial de la DRTPE-Junín, importando ofertas de empleo del registro institucional e informando colocaciones laborales al sistema público, creando un flujo bidireccional de datos entre el sistema de investigación y la institucionalidad estatal.

---

## 2. Estado Actual: Stub Funcional

El conector DRTPE implementado en Sprint 4 es un **stub funcional** (interfaz real con datos simulados):

| Estado | Sprint 4 (actual) | Sprint 6 (objetivo) |
|--------|-----------------|---------------------|
| `fetch_active_offers` | Retorna 3 ofertas simuladas de Junín | GET `https://api.drtpe.gob.pe/bolsa/ofertas` |
| `sync_worker_registration` | Log `"drtpe_sync_registration_stub"` | POST al registro DRTPE |
| `report_placement` | Log `"drtpe_report_placement_stub"` | POST de colocación al sistema DRTPE |

---

## 3. Arquitectura del Conector

```python
# Interfaz del protocolo (permite swap sin cambiar código cliente)
class DRTPEConnectorProtocol(Protocol):
    async def fetch_active_offers(self, limit: int) -> list[DRTPEJobOffer]: ...
    async def sync_worker_registration(self, worker_id: str, data: dict) -> bool: ...
    async def report_placement(self, contract_id: str, data: dict) -> bool: ...

# Instancia singleton (cambiar DRTPEConnectorStub → DRTPEConnectorReal en Sprint 6)
drtpe_connector: DRTPEConnectorProtocol = DRTPEConnectorStub()
```

---

## 4. Estructura de Oferta DRTPE

```python
@dataclass
class DRTPEJobOffer:
    external_id: str        # ej. "DRTPE-2026-001"
    title: str              # "Técnico en instalaciones eléctricas"
    employer_name: str      # "Empresa Constructora El Tambo S.A.C."
    district: str           # "El Tambo"
    required_skills: list[str]
    salary_min: float | None
    salary_max: float | None
    published_at: str
    source: str = "DRTPE-JUNIN"
```

---

## 5. Datos Simulados (Sprint 4)

| External ID | Puesto | Empleador | Distrito |
|-------------|--------|-----------|---------|
| DRTPE-2026-001 | Técnico en instalaciones eléctricas | Empresa Constructora El Tambo S.A.C. | El Tambo |
| DRTPE-2026-002 | Auxiliar administrativo | Municipalidad Provincial de Huancayo | Huancayo |
| DRTPE-2026-003 | Gasfitero para mantenimiento | Urbanización Los Jardines S.A. | Chilca |

---

## 6. Flujo de Sincronización Automática

```
[Celery Beat — Diario 8:00 AM Lima]
    └─► sync_drtpe_offers_task()
            │
            ├─► drtpe_connector.fetch_active_offers(limit=100)
            ├─► Por cada oferta DRTPE:
            │       ├─► Upsert en job_offers (source='DRTPE-JUNIN')
            │       └─► Encolar generate_job_embedding(job_offer_id)
            └─► structlog "drtpe_offers_synced" {count}
```

---

## 7. Reporte de Colocaciones (RF165)

Cuando un trabajador obtiene un contrato (status="contratada" en applications):
```
report_placement(contract_id, {
    "worker_type": ...,
    "district": ...,
    "job_title": ...,
    "signed_at": ...
})
# Sprint 4: solo log
# Sprint 6: POST a API DRTPE para estadísticas de colocación
```

---

## 8. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Interfaz desacoplada | `DRTPEConnectorProtocol` permite swap de stub a real sin cambiar código cliente |
| Idempotencia de sincronización | Upsert por `external_id` — no duplica ofertas al re-sincronizar |
| Trazabilidad de origen | Campo `source='DRTPE-JUNIN'` en job_offers importadas |
| Manejo de fallos | Si la API DRTPE falla, la tarea Celery re-intenta con backoff |
| Sin PII en sincronización | Solo datos de oferta (título, skills, salario); no datos del trabajador |

---

## 9. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Ofertas DRTPE sincronizadas | > 0 por ejecución | `sync_drtpe_offers_task` count |
| Tasa de embeddings generados para ofertas DRTPE | > 90% | `job_offers WHERE source='DRTPE-JUNIN' AND embedding IS NOT NULL` |
| Tiempo de sincronización | < 30 segundos por 100 ofertas | Celery task duration |

---

*P-017 | Linku DRTPE-Junín · Implementado Sprint 4 (stub) · RF161–RF165*
