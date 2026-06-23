# P-005 — Construcción de Perfil — Tipo Experiencia
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M02 / M04 — Perfil del Trabajador / NLP de Competencias
**RF Cubiertos:** RF066–RF075
**Sprint de implementación:** Sprint 2
**Componentes clave:**
- `backend/app/api/v1/nlp.py`
- `backend/app/nlp/cv_parser/parser.py`
- `backend/app/utils/cv_templates/experiencia.html`

---

## 1. Propósito

Facilitar a profesionales y técnicos con historial laboral documentado la importación automática de su información profesional mediante el parseo inteligente de su CV existente (PDF o DOCX), extrayendo campos estructurados con niveles de confianza para validación del usuario.

---

## 2. Alcance

Aplica exclusivamente a trabajadores con `worker_type = "experiencia"`. Acepta archivos PDF (con texto digital, no escaneados) y DOCX hasta 10 MB. Los campos extraídos con confianza ≥ 0.75 se precargan en el formulario; los de menor confianza requieren ingreso manual.

---

## 3. Formatos de Entrada Soportados

| Formato | MIME Type | Condición |
|---------|-----------|-----------|
| PDF con texto digital | `application/pdf` | Texto extraído ≥ 100 caracteres |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Cualquier tamaño válido |
| PDF escaneado | `application/pdf` | Retorna warning: texto < 100 chars |

**Tamaño máximo:** 10 MB por archivo.

---

## 4. Campos Extraídos y Umbrales de Confianza

| Campo | Técnica de Extracción | Confianza | Umbral para Precarga |
|-------|----------------------|-----------|---------------------|
| `full_name` | spaCy NER — entidades PER en primeras 5 líneas | 0.85 (1 entidad) / 0.50 (varias) | ≥ 0.75 |
| `email` | Regex estándar de email | 0.99 (1 encontrado) | ≥ 0.75 |
| `phone` | Regex formato peruano: `+51 9XXXXXXXX` / `9XXXXXXXX` | 0.95 | ≥ 0.75 |
| `education` | Keywords (universidad/instituto/bachiller...) + NER ORG | 0.80 | ≥ 0.75 |
| `work_experiences` | Bloques con años (`\d{4}`) + NER ORG | 0.70 | < 0.75 — ingreso manual |
| `skills` | Lista después de keywords (habilidades/competencias/skills) | 0.75 | ≥ 0.75 |

---

## 5. Entradas del Proceso

| Entrada | Fuente | Validación |
|---------|--------|------------|
| Archivo CV | Frontend multipart `/api/v1/nlp/parse-cv` | MIME: solo PDF o DOCX; tamaño ≤ 10MB |
| `worker_id` del token | JWT payload | `require_role(WORKER)` + `worker_type == experiencia` |

---

## 6. Salidas del Proceso

| Salida | Destino | Contenido |
|--------|---------|-----------|
| `ParsedCVResult` | Frontend (JSON) | Campos extraídos con niveles de confianza |
| `parse_warnings` | Frontend (lista) | Advertencias para campos con confianza < 0.75 |
| `raw_text_length` | Frontend | Número de caracteres extraídos |

> **Nota de deuda técnica (CV-EXP-VACIO):** Actualmente `ParsedCVResult` no está conectado directamente al contexto del CV PDF. Los datos parseados deben completarse manualmente en el perfil del trabajador antes de generar el CV. Esta deuda está registrada en el CLAUDE.md.

---

## 7. Flujo del Proceso

```
[Trabajador EXPERIENCIA] POST /api/v1/nlp/parse-cv (multipart)
    │
    ├─► Verificar worker_type == "experiencia" (403 si no)
    ├─► Validar MIME type (422 si no es PDF o DOCX)
    ├─► Leer bytes del archivo
    │
    ├─► [PDF] parse_pdf(file_content: bytes) → str
    │       │
    │       ├─► PyPDF2.PdfReader → extraer texto
    │       ├─► [Si texto < 100 chars] warning "pdf_no_text_extracted"
    │       └─► [PDF inválido] capturar excepción, log, retornar "" (no lanzar)
    │
    ├─► [DOCX] parse_docx(file_content: bytes) → str
    │       └─► python_docx.Document → concatenar párrafos
    │
    ├─► [Si raw_text_length < 100]
    │       └─► HTTP 422 "No se pudo extraer texto del archivo..."
    │
    ├─► extract_cv_fields(raw_text: str) → ParsedCVResult
    │       │
    │       ├─► full_name: spaCy NER PER en primeras 5 líneas
    │       ├─► email: regex
    │       ├─► phone: regex formato peruano
    │       ├─► education: keywords + NER ORG
    │       ├─► work_experiences: años + NER ORG
    │       ├─► skills: keywords + lista
    │       └─► [Confianza < 0.75] → campo = None, agregar a parse_warnings
    │
    └─► Retornar ParsedCVResult {full_name, email, phone, education, skills,
                                  *_confidence, parse_warnings, raw_text_length}
```

---

## 8. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Tipo de trabajador verificado | Solo `experiencia` accede al endpoint de parseo |
| MIME validado estrictamente | `.txt`, `.odt` y otros formatos → 422 inmediato |
| Manejo robusto de PDF malformados | `try/except` sin relanzar; log + retorno vacío |
| Umbrales de confianza documentados | El frontend solo premuestra campos con confianza ≥ 0.75 |
| Rate limit NLP | 30 requests/minuto por usuario (parseo es costoso en CPU) |
| Sin almacenamiento del archivo | El CV no se persiste; solo los datos extraídos |

---

## 9. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Tasa de éxito de parseo | ≥ 80% de PDFs producen ≥ 100 chars de texto | `raw_text_length ≥ 100` |
| Tasa de extracción de email | ≥ 95% (campo más común en CVs) | `email_confidence ≥ 0.99` |
| Campos pre-cargados en promedio | ≥ 3 campos por CV (email, teléfono, skills) | Count campos con confianza ≥ 0.75 |

---

## 10. Pruebas Automatizadas

Archivo: `backend/tests/unit/test_nlp_cv_parser.py`
- `test_parse_pdf_returns_string`
- `test_extract_email_from_text`
- `test_extract_phone_peruvian_format`
- `test_low_confidence_field_is_none`
- `test_empty_pdf_returns_warnings`

Archivo: `backend/tests/integration/test_api_nlp.py`
- `test_parse_cv_requires_experiencia_type`
- `test_parse_cv_validates_mime_type`

---

*P-005 | Linku DRTPE-Junín · Implementado Sprint 2 · RF066–RF075*
