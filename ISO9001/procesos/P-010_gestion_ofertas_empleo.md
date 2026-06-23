# P-010 — Publicación y Gestión de Ofertas de Empleo
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M03 — Empleadores y Ofertas
**RF Cubiertos:** RF036–RF055
**Sprint de implementación:** Sprint 2
**Componentes clave:**
- `backend/app/api/v1/employers.py`
- `backend/app/api/v1/jobs.py`

---

## 1. Propósito

Gestionar el ciclo completo de las ofertas de empleo: desde la creación por parte del empleador (con validación, embedding automático y flujo de postulaciones) hasta la visualización pública por trabajadores, incluyendo el feed filtrado y el sistema de gestión de candidatos.

---

## 2. Entidades Involucradas

| Tabla | Propósito |
|-------|-----------|
| `employers` | Perfil del empleador (company_name, sector, district; RUC cifrado AES-256) |
| `job_offers` | Ofertas publicadas con skills, salario, modalidad, expiración y embedding |
| `applications` | Postulaciones de trabajadores a ofertas específicas |
| `search_logs` | Registro de búsquedas para KPI IVP |

---

## 3. Ciclo de Vida de una Oferta de Empleo

```
CREADA (is_active=True, embedding=NULL)
    │
    └─► Celery genera embedding → ACTIVA + INDEXADA
            │
            ├─► EXPIRADA (expires_at < now())
            └─► DESACTIVADA (soft-delete: is_active=False, expires_at=now())
```

---

## 4. Flujo del Proceso

### 4.1 Perfil de Empleador (RF036–RF040)
```
[Empleador autenticado] POST /api/v1/employers/profile
    │
    ├─► Verificar rol EMPLOYER + no tener perfil previo (409 si existe)
    ├─► Validar RUC (11 dígitos numéricos, regex)
    ├─► Cifrar ruc + contact_name con AES-256-GCM
    └─► Crear registro en employers

GET /api/v1/employers/profile
    └─► Descifrar contact_name; NUNCA retornar ruc
```

### 4.2 Creación de Oferta (RF041–RF043)
```
[Empleador] POST /api/v1/employers/jobs
    │
    ├─► Recibir JobOfferCreate:
    │       title (5-200 chars)
    │       description (50-5000 chars)
    │       required_skills (lista, max 20 items)
    │       district, modality ("presencial"/"remoto"/"híbrido")
    │       salary_min, salary_max (validar max > min)
    │       worker_type_target, expires_at
    │
    ├─► Crear job_offer con is_active=True, embedding=NULL
    ├─► Encolar generate_job_embedding(job_offer_id) → cola "embeddings"
    └─► Retornar JobOfferResponse (201)
```

### 4.3 Feed Público de Ofertas (RF055)
```
GET /api/v1/jobs/feed [sin autenticación obligatoria]
    │
    ├─► Filtros opcionales: district, modality, worker_type_target, salary_min, salary_max
    ├─► Paginación: limit (def 20, max 100) / offset
    ├─► Ordenar por created_at DESC
    ├─► Excluir: is_active=False + expires_at < now()
    ├─► Registrar en search_logs (para KPI IVP)
    └─► Retornar list[JobOfferResponse] con employer_name y days_until_expiry
```

### 4.4 Gestión de Postulaciones (RF047–RF050)
```
[Empleador] GET /api/v1/employers/jobs/{job_id}/applications
    │
    ├─► Verificar que la oferta pertenece al empleador (403 si no)
    └─► Retornar lista con status, match_score, datos básicos del worker (NO DNI)

[Empleador] PATCH /api/v1/employers/jobs/{job_id}/applications/{app_id}/status
    │
    ├─► Avanzar en el flujo de estado:
    │       enviada → en_revision → entrevista → contratada | descartada
    ├─► [Si status == "contratada"] encolar notify_worker_hired(worker_id, job_offer_id)
    └─► Retornar ApplicationResponse
```

### 4.5 Postulación del Trabajador (RF051–RF053)
```
[Trabajador] POST /api/v1/workers/apply
    │
    ├─► Verificar rol WORKER
    ├─► Verificar que la oferta exista y esté activa
    ├─► Verificar no postulación previa (409 si ya postuló)
    ├─► Verificar profile_completeness ≥ 40 (400 si muy incompleto)
    ├─► Crear application con match_score=NULL
    ├─► Registrar en search_logs
    └─► Encolar notify_employer_new_application (stub)
```

---

## 5. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Validación de salario | `salary_max > salary_min` (Pydantic validator) |
| Descripción mínima | min 50 chars — garantiza calidad del embedding |
| RUC cifrado | AES-256-GCM; NUNCA retornado en respuestas |
| Soft-delete | Las ofertas nunca se borran físicamente para preservar el historial de postulaciones |
| Autorización por employer | Un empleador no puede ver/modificar ofertas de otro (verificación en cada endpoint) |
| Completitud requerida | Profile completeness ≥ 40 para postular (evita postulaciones con perfiles vacíos) |
| Postulación única | Índice único `(worker_id, job_offer_id)` en `applications` |

---

## 6. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Tiempo hasta primer embedding de oferta | < 30 segundos | Celery task + Flower |
| Tasa de ofertas con embedding activo | > 90% de ofertas activas | `job_offers WHERE embedding IS NOT NULL AND is_active` |
| Postulaciones por oferta | Media 5–20 | `applications.count() GROUP BY job_offer_id` |
| Conversión a contratación (TF) | KPI de investigación | Ver P-013 |

---

## 7. Pruebas Automatizadas

Archivo: `backend/tests/integration/test_api_employers.py`
- `test_create_employer_profile_returns_200`
- `test_create_duplicate_employer_returns_409`
- `test_ruc_never_in_response`
- `test_create_job_offer_queues_embedding_task`
- `test_deactivate_job_offer_returns_200`

---

*P-010 | Linku DRTPE-Junín · Implementado Sprint 2 · RF036–RF055*
