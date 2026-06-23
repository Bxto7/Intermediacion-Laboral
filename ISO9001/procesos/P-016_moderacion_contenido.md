# P-016 — Moderación de Contenido del Marketplace
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M07 — Moderación
**RF Cubiertos:** RF118, RF123–RF125
**Sprint de implementación:** Sprint 5
**Componentes clave:**
- `backend/app/api/v1/moderation.py`
- Modelo `content_flags` en BD

---

## 1. Propósito

Mantener la calidad y seguridad del contenido del marketplace mediante un sistema de reportes de usuarios y cola de revisión por moderadores, con capacidad de banear/desbanear listings que violen los términos del servicio.

---

## 2. Ciclo de Vida de un Flag de Contenido

```
[Usuario reporta listing] → content_flag (status="pending")
                                    │
                         [Moderador revisa]
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            [Contenido inapropiado]        [Reporte injustificado]
                    │                               │
            ban_listing()                   flag.status = "dismissed"
            listing.is_active = False               │
                    │                       [Listing sigue activo]
            flag.status = "resolved"
```

---

## 3. Razones de Reporte Válidas

| Código | Descripción |
|--------|-------------|
| `spam` | Contenido repetitivo o publicitario no relacionado |
| `falso` | Información engañosa o fraudulenta |
| `ofensivo` | Contenido inapropiado u ofensivo |
| `otro` | Otras razones con descripción en `details` |

---

## 4. Flujo del Proceso

### 4.1 Reporte de Listing por Usuario
```
[Trabajador autenticado] POST /api/v1/moderation/listings/{listing_id}/flag
    {reason, details}
    │
    ├─► Verificar que el listing existe (404 si no)
    ├─► Verificar que el usuario NO es el owner del listing (400 si sí)
    ├─► Crear ContentFlag {listing_id, reported_by, reason, details, status="pending"}
    ├─► structlog "listing_flagged" {listing_id, reason}
    └─► Retornar FlagResponse {id, status}
```

### 4.2 Cola de Moderación (solo MODERATOR/ADMIN)
```
[Moderador] GET /api/v1/moderation/queue?status=pending
    │
    ├─► Verificar rol MODERATOR (403 si WORKER/EMPLOYER)
    └─► Retornar lista de flags pendientes (max 50, ordenados por created_at ASC)
```

### 4.3 Banear Listing
```
[Moderador] POST /api/v1/moderation/listings/{listing_id}/ban
    {reason}
    │
    ├─► Cargar listing de BD (404 si no existe)
    ├─► listing.is_active = False
    ├─► listing.ban_reason = reason
    ├─► listing.banned_at = ahora
    ├─► listing.banned_by = current_user.id
    ├─► structlog "listing_banned" {listing_id, reason, by}
    └─► Retornar {status: "banned", listing_id}
```

### 4.4 Desbanear Listing
```
[Moderador] POST /api/v1/moderation/listings/{listing_id}/unban
    │
    ├─► listing.is_active = True
    ├─► listing.ban_reason = None
    ├─► listing.banned_at = None
    ├─► listing.banned_by = None
    ├─► structlog "listing_unbanned"
    └─► Retornar {status: "active", listing_id}
```

---

## 5. Modelo de Datos — `content_flags`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador |
| `listing_id` | UUID (FK service_listings) | Listing reportado |
| `reported_by` | UUID (FK users) | Usuario que reportó |
| `reason` | VARCHAR(50) | spam/falso/ofensivo/otro |
| `details` | TEXT | Descripción adicional |
| `status` | VARCHAR(20) | pending / resolved / dismissed |
| `resolved_by` | UUID (FK users, nullable) | Moderador que resolvió |
| `resolved_at` | TIMESTAMPTZ | Fecha de resolución |
| `created_at` | TIMESTAMPTZ | Fecha del reporte |

**Índices:** `(listing_id, status)` + `(status, created_at DESC)`

---

## 6. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Anti-autoflagueo | Un usuario no puede reportar su propio listing (400) |
| RBAC por acción | Reportar: WORKER; Revisar/Banear: MODERATOR o ADMIN |
| Soft-ban | `is_active=False` preserva historial de contratos y datos del listing |
| Trazabilidad | `banned_by` + `banned_at` son auditables; structlog con todos los eventos |
| Sin exposición de datos de otros | El moderador ve los flags pero no datos PII del trabajador reportado |

---

## 7. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Tiempo promedio de resolución de flag | < 48 horas | `content_flags.resolved_at - created_at` |
| Tasa de flags resueltos | > 90% en 7 días | `status != "pending" / total` |
| Listings baneados activos | < 2% del total de listings | `is_active=False AND ban_reason IS NOT NULL` |

---

## 8. Pruebas Automatizadas

Archivo: `backend/tests/integration/test_api_moderation.py`
- `test_flag_listing_returns_201`
- `test_cannot_flag_own_listing`
- `test_moderation_queue_requires_moderator`
- `test_ban_listing_deactivates`
- `test_unban_listing_reactivates`

---

*P-016 | Linku DRTPE-Junín · Implementado Sprint 5 · RF118, RF123–RF125*
