# P-004 — Construcción de Perfil — Tipo Oficio
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M02 / M04 — Perfil del Trabajador / NLP de Competencias
**RF Cubiertos:** RF056–RF065
**Sprint de implementación:** Sprint 2
**Componentes clave:**
- `backend/app/api/v1/portfolio.py`
- `backend/app/nlp/portfolio_nlp/trade_extractor.py`
- `backend/app/utils/cv_templates/oficio.html`

---

## 1. Propósito

Permitir que trabajadores de oficios manuales (electricistas, gasfiteros, carpinteros, etc.) construyan un portafolio digital de trabajos realizados con extracción automática de competencias técnicas, generando visibilidad y credibilidad sin necesidad de un CV formal.

---

## 2. Alcance

Aplica a trabajadores con `worker_type = "oficio"`. El portafolio puede contener hasta ilimitadas entradas, cada una describiendo un trabajo específico con fotos, período, calificación del cliente y skills extraídas por NLP.

---

## 3. Categorías de Oficio Soportadas (13 categorías)

| Código | Categoría | Skills base (muestra) |
|--------|-----------|----------------------|
| ELECTRICIDAD | Electricidad | instalación eléctrica residencial, cableado, tableros, tomacorrientes, norma EM.010 |
| GASFITERIA | Gasfitería | plomería, sanitarios, cañerías, PVC, termofusión |
| CARPINTERIA | Carpintería | melanina, ebanistería, barnizado, madera nativa |
| ALBANILERIA | Albañilería | ladrillo, concreto, fierro, porcelanato, acabados |
| PINTURA | Pintura | pintura látex, empaste, texturas, estuco veneciano |
| MECANICA | Mecánica automotriz | motor, frenos, transmisión, diagnóstico, scanner |
| TECHADO | Techado | calamina, fibrocemento, eternit, trabajo en altura |
| SOLDADURA | Soldadura y metalurgia | soldadura MIG/TIG, fierro, estructuras metálicas |
| JARDINERIA | Jardinería | diseño paisajístico, riego tecnificado, plantas ornamentales |
| LIMPIEZA | Limpieza y mantenimiento | limpieza industrial, pulido de pisos, desinfección |
| COCINA | Cocina y pastelería | cocina andina, catering, repostería |
| COSTURA | Costura y confección | costura industrial, patronaje, uniformes |
| OTROS | Otros oficios | habilidad técnica manual, herramientas de oficio |

---

## 4. Entradas del Proceso

| Entrada | Fuente | Validación |
|---------|--------|------------|
| `title` de la entrada de portafolio | Frontend | min 3, max 200 chars |
| `description` del trabajo | Frontend | min 20, max 2000 chars |
| `period_start` / `period_end` | Frontend | Fechas opcionales |
| `client_rating` | Frontend | float 1.0–5.0, opcional |
| `is_public` | Frontend | bool, default True |
| Fotos (hasta 5) | Frontend multipart | JPEG/PNG/WEBP, max 5MB c/u |
| `trade_category` | Perfil del worker en BD | TradeCategory enum |

---

## 5. Salidas del Proceso

| Salida | Destino | Contenido |
|--------|---------|-----------|
| Entrada en `portfolio_entries` | BD | title, description, extracted_skills, embedding=NULL |
| `workers.avg_rating` recalculado | BD | Promedio de todos los `client_rating` del worker |
| Tarea Celery embedding | Cola `embeddings` | `generate_portfolio_entry_embedding(entry_id)` |
| Tarea Celery embedding worker | Cola `embeddings` | `generate_worker_embedding(worker_id)` |
| URLs de fotos | BD (JSONB) | Dev: `/static/{entry_id}/{filename}`; Prod: GCS signed URL |

---

## 6. Flujo del Proceso

```
[Trabajador OFICIO] POST /api/v1/portfolio/entries
    │
    ├─► Verificar worker_type == "oficio" (403 si no)
    ├─► Obtener trade_category del perfil del worker
    │
    ├─► extract_skills_from_job_description(description, trade_category)
    │       │
    │       ├─► normalize_text + apply_local_dictionary
    │       ├─► spaCy NLP → tokens y chunks relevantes
    │       ├─► Búsqueda fuzzy en TRADE_SKILLS_MAP (overlap ≥ 0.60)
    │       ├─► Estimar nivel: "básico" / "intermedio" / "avanzado"
    │       └─► Retornar JobSkillExtraction {skills, estimated_level, confidence}
    │
    ├─► Crear portfolio_entry con extracted_skills
    ├─► Recalcular avg_rating si client_rating presente
    ├─► Encolar generate_portfolio_entry_embedding(entry_id)
    ├─► Encolar generate_worker_embedding(worker_id)
    └─► Retornar PortfolioEntryResponse {id, title, extracted_skills, ...}

POST /api/v1/portfolio/entries/{entry_id}/photos
    │
    ├─► Validar MIME (JPEG/PNG/WEBP únicamente)
    ├─► Validar tamaño ≤ 5MB por foto
    ├─► Dev: guardar en disco local /tmp/portfolio_photos/{entry_id}/
    ├─► Prod: TODO → GCS signed URL
    └─► Actualizar portfolio_entries.photos (JSONB con lista de URLs)

GET /api/v1/portfolio/{username} (público, sin autenticación)
    │
    ├─► Buscar worker por slug/username
    ├─► Verificar worker_type == "oficio" (404 si no)
    ├─► Retornar solo entradas con is_public=True
    └─► NUNCA exponer DNI, teléfono ni user_id interno
```

---

## 7. Lógica de Estimación de Nivel de Competencia

```python
if len(description) >= 200_words and len(skills_found) >= 8:
    estimated_level = "avanzado"
elif len(skills_found) >= 5:
    estimated_level = "intermedio"
else:
    estimated_level = "básico"

confidence = len(skills_found) / max_expected_skills_for_category
```

---

## 8. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Tipo de trabajador verificado | Solo `oficio` puede crear entradas de portafolio |
| Visibilidad granular | `is_public=False` excluye la entrada del portafolio público y del matching |
| Inmutabilidad selectiva | DELETE físico permitido (portafolio es propiedad del trabajador); recalcula rating y re-genera embedding |
| Validación MIME de fotos | Rechaza archivos que no sean JPEG/PNG/WEBP explícitamente |
| avg_rating consistente | Se recalcula como promedio de TODOS los ratings cada vez que cambia la colección |

---

## 9. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Entradas de portafolio por worker OFICIO | ≥ 2 entradas en promedio | `COUNT(*) FROM portfolio_entries GROUP BY worker_id` |
| Tasa de extracción de skills | ≥ 3 skills/entrada en promedio | `len(extracted_skills)` por entrada |
| Cobertura de portafolio público (`IVM`) | (listados activos / total OFICIO) × 100 | KPI IVM del panel admin |

---

## 10. Pruebas Automatizadas

Archivo: `backend/tests/integration/test_api_portfolio.py`
- `test_create_portfolio_entry_extracts_skills`
- `test_portfolio_public_endpoint_no_auth_required`
- `test_portfolio_public_hides_dni`
- `test_delete_entry_returns_204`
- `test_oficio_worker_type_required`

---

*P-004 | Linku DRTPE-Junín · Implementado Sprint 2 · RF056–RF065*
