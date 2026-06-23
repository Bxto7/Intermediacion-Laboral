# P-015 — Marketplace de Servicios de Oficio
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M07 — Marketplace
**RF Cubiertos:** RF118–RF125
**Sprint de implementación:** Sprint 3 (marketplace base) + Sprint 5 (contratos)
**Componentes clave:**
- `backend/app/api/v1/marketplace.py`
- `backend/app/api/v1/contracts.py`
- `backend/app/services/marketplace/marketplace_service.py`

---

## 1. Propósito

Proporcionar un mercado digital de servicios de oficio donde trabajadores de tipo `oficio` publican sus listados de servicios (con precio, disponibilidad y cobertura geográfica) y clientes/empresas pueden contratarlos directamente, generando contratos y registros para los KPIs de la investigación.

---

## 2. Estructura de un Listing de Marketplace

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `trade_category` | TradeCategory | Categoría del oficio |
| `title` | VARCHAR(200) | Título del servicio |
| `description` | TEXT | Descripción detallada |
| `enriched_keywords` | JSONB | Keywords añadidas por NLP para búsqueda |
| `districts` | JSONB | Zonas de cobertura: Huancayo/El Tambo/Chilca |
| `price_reference` | DECIMAL(10,2) | Precio de referencia |
| `price_unit` | VARCHAR(20) | `hora` / `proyecto` / `día` |
| `availability` | VARCHAR(20) | `inmediata` / `semana` / `mes` |
| `is_active` | BOOLEAN | Activo o desactivado (por ban o por el propio worker) |
| `views_count` | INTEGER | Contador de visualizaciones |
| `embedding` | vector(384) | Para búsqueda semántica |

---

## 3. Flujo del Proceso

### 3.1 Publicación de Listing
```
[Trabajador OFICIO] POST /api/v1/marketplace/listings
    │
    ├─► Verificar worker_type == "oficio"
    ├─► Enriquecer keywords con NLP (trade_extractor)
    ├─► Crear service_listing con is_active=True
    ├─► Encolar generate_listing_embedding(listing_id)
    └─► Retornar ListingResponse (201)
```

### 3.2 Búsqueda Pública de Servicios
```
GET /api/v1/marketplace/search?district=Huancayo&trade=Electricidad&q=cableado
    │
    ├─► Sin autenticación requerida
    ├─► Filtros: district, trade_category, query semántica
    ├─► ORDER BY similitud semántica (embedding <=> query_embedding)
    └─► Retornar list[ListingPublicResponse] (sin datos PII del worker)
```

### 3.3 Creación de Contrato desde Marketplace (RF124)
```
[Cliente] POST /api/v1/contracts
    {worker_id, listing_id, agreed_amount, contract_type, consent_given}
    │
    ├─► require_consent(consent_given, "contrato_laboral") — Ley 29733
    ├─► Calcular contract_number (último + 1 para el worker)
    ├─► Crear Contract:
    │       worker_id, employer_id=None (cliente anónimo del marketplace)
    │       contract_type ("formal" / "marketplace")
    │       monthly_salary = encrypt_field(str(agreed_amount)) — AES-256
    │       signed_at = ahora
    ├─► Commit BD
    └─► Retornar {contract_id, contract_number}

[Trabajador] GET /api/v1/contracts/worker/{worker_id} (RF125)
    └─► Historial de contratos: [{id, contract_number, type, signed_at, is_active}]
```

### 3.4 Re-indexado Automático (Celery Beat)
```
Tarea: reindexar_marketplace()
Frecuencia: Diaria 3:00 AM Lima
Cola: embeddings

Acción: regenerar embeddings de listings activos + actualizar keywords enriquecidas
```

---

## 4. Diferencia con el Flujo de Postulaciones

| Característica | Marketplace (P-015) | Postulaciones (P-010) |
|---------------|--------------------|-----------------------|
| Inicia | Trabajador publica servicio | Empleador publica oferta |
| Cliente | Anónimo / cualquier usuario | Empleador registrado |
| Contrato | Directo (precio acordado) | Via proceso de selección |
| Visibilidad | Pública sin login | Feed con/sin login |
| KPI asociado | IVM (Índice Visibilidad Marketplace) | TF (Tasa de Formalización) |

---

## 5. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Tipo de trabajador verificado | Solo `oficio` puede publicar listings |
| Consentimiento para contratos | Ley 29733 — `consent_given=True` obligatorio |
| Cifrado de monto acordado | `agreed_amount` → AES-256 en `contracts.monthly_salary` |
| Soft-delete al banear | `is_active=False` — no se borra el listing (ver P-016) |
| PII nunca en listado público | Solo trade_category, distrito, precio y descripción; NO nombre completo, DNI, teléfono |

---

## 6. Indicadores de Desempeño

| Indicador | KPI | Fuente |
|-----------|-----|--------|
| % trabajadores OFICIO con listing activo | IVM | `service_listings WHERE is_active=True / workers WHERE type=oficio` |
| Tiempo hasta primer contrato desde marketplace | VIL (variante marketplace) | `contracts.signed_at - workers.created_at` |
| Views por listing | Visibilidad | `service_listings.views_count` |

---

*P-015 | Linku DRTPE-Junín · Implementado Sprint 3–5 · RF118–RF125*
