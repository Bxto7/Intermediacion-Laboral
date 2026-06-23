# P-006 — Extracción NLP de Competencias
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M04 — NLP de Competencias
**RF Cubiertos:** RF059–RF075
**Sprint de implementación:** Sprint 2
**Componentes clave:**
- `backend/app/nlp/skill_extractor/first_job_extractor.py`
- `backend/app/nlp/portfolio_nlp/trade_extractor.py`
- `backend/app/nlp/embeddings/generator.py` (`normalize_text`)
- `backend/app/utils/local_dict/huancayo_trades.json`

---

## 1. Propósito

Transformar automáticamente texto en lenguaje natural (coloquial, técnico o formal) en listas de competencias estandarizadas, adaptadas al contexto laboral de Huancayo-Junín, mediante un pipeline NLP de tres capas: normalización, diccionario local y modelos lingüísticos.

---

## 2. Pipeline NLP Unificado

```
Texto libre del usuario
       │
       ▼
[Capa 1: Normalización]
    normalize_text(text):
        1. text.lower()
        2. ftfy.fix_text() → corrección de encoding
        3. re.sub → eliminar chars especiales (conservar letras, números, acentos)
        4. apply_local_dictionary(text) → diccionario regional
        5. Eliminar stopwords en español (NLTK)
       │
       ▼
[Capa 2: Diccionario Local Huancayo]
    apply_local_dictionary(text):
        Archivo: huancayo_trades.json
        Términos: gasfitero→plomero, techero→techador, fierrero→soldador...
        Método: regex \b{term}\b case-insensitive
        Cache: módulo-level (cargado una sola vez)
       │
       ▼
[Capa 3: Extracción diferenciada por tipo]
    ┌─── primer_empleo → first_job_extractor.py (soft_skills_map, spaCy NER)
    ├─── oficio        → trade_extractor.py (TRADE_SKILLS_MAP, fuzzy matching)
    └─── experiencia   → cv_parser.py (regex + spaCy NER campos estructurados)
       │
       ▼
Lista de competencias estandarizadas (deduplicada)
```

---

## 3. Diccionario Local — Regionalismos de Huancayo

El archivo `backend/app/utils/local_dict/huancayo_trades.json` contiene el vocabulario de oficios de la región Junín:

| Término Local | Equivalentes Estándar |
|--------------|----------------------|
| gasfitero | plomero, fontanero, instalador sanitario |
| techero | techadista, instalador de techos, techador |
| fierrero | soldador, herrero, metalurgista |
| albañil | constructor, obrero de construcción, operario civil |
| electricista | instalador eléctrico, técnico eléctrico |
| pintor | aplicador de pintura, pintor de obras |
| carpintero | ebanista, trabajador de madera |
| mecánico | técnico automotriz, mecánico automotriz |
| plomero | gasfitero |
| instalador | técnico de instalaciones |

Este diccionario es **extensible** sin reentrenamiento del modelo NLP.

---

## 4. Extracción por Tipo de Trabajador

### 4.1 Primer Empleo (`first_job_extractor.py`)

**Técnica:** Coincidencia en `soft_skills_map` (fuzzy: subcadena ≥ 4 chars) + spaCy NER MISC/PER.

**Muestra del mapa de skills:**
```python
"puntual"              → "puntualidad"
"responsable"          → "responsabilidad"
"trabajo en equipo"    → "trabajo colaborativo"
"ayudo en casa"        → "gestión doméstica"
"vendo en el mercado"  → "ventas informales"
"atiendo clientes"     → "atención al cliente"
"cocino"               → "preparación de alimentos"
```

**Sugerencia de sectores:** 8 sectores (Comercio, Gastronomía, Construcción, Tecnología, Cuidado de personas, Manufactura, Transporte, Servicios). Score = solapamiento de skills del usuario con skills del sector.

### 4.2 Oficio (`trade_extractor.py`)

**Técnica:** `TRADE_SKILLS_MAP` por categoría (≥15 skills por categoría) + fuzzy matching (token overlap ≥ 0.60).

**Nivel estimado:**
- `"avanzado"` → descripción ≥ 200 palabras Y ≥ 8 skills encontradas
- `"intermedio"` → ≥ 5 skills encontradas
- `"básico"` → resto

**Confianza:** `len(skills_found) / max_expected_skills_for_category`

### 4.3 Experiencia (`cv_parser.py`)

**Técnica:** Combinación de regex y spaCy NER con umbrales de confianza por campo (ver P-005 para detalle completo).

---

## 5. Endpoints Expuestos

| Endpoint | Método | Tipo Requerido | Rate Limit |
|----------|--------|----------------|------------|
| `/api/v1/nlp/extract-skills/wizard` | POST | primer_empleo | 60 req/min/usuario |
| `/api/v1/nlp/extract-skills/portfolio` | POST | oficio | 30 req/min/usuario |
| `/api/v1/nlp/parse-cv` | POST | experiencia | 30 req/min/usuario |

**Payload wizard:**
```json
{"step": 3, "text": "soy muy puntual y me llevo bien con todos"}
```
**Respuesta wizard:**
```json
{"skills": ["puntualidad", "habilidades interpersonales"], "suggested_sectors": ["Comercio", "Servicios"]}
```

---

## 6. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Singletons de modelos | spaCy y sentence-transformers se cargan una sola vez al inicio de la app |
| Cache del diccionario local | El JSON se lee del disco una vez y queda en memoria (módulo-level) |
| Tipo de trabajador forzado | Los endpoints NLP verifican `worker_type` y retornan 403 al tipo incorrecto |
| Rate limiting diferenciado | NLP es CPU-intensivo; límite más estricto que endpoints CRUD |
| No almacenamiento de texto crudo | El texto del usuario no se persiste; solo las skills extraídas |

---

## 7. Indicadores de Desempeño

| Indicador | Objetivo | Medición |
|-----------|---------|----------|
| Tiempo de respuesta extracción wizard | < 500ms | Header `X-Process-Time` |
| Tasa de skills extraídas no vacías | > 80% de requests | `len(skills) > 0` en respuesta |
| Uso de caché del diccionario | 0 lecturas de disco después del primer request | Métricas de I/O |

---

## 8. Pruebas Automatizadas

Archivo: `backend/tests/unit/test_nlp_first_job.py`
- `test_extract_skills_puntual` → "puntualidad"
- `test_suggest_sectors_from_skills` → "Gastronomía" en top sectores para skills de cocina
- `test_normalize_text_removes_stopwords`
- `test_apply_local_dictionary_gasfitero` → "plomero"
- `test_apply_local_dictionary_case_insensitive`

Archivo: `backend/tests/unit/test_nlp_trade_portfolio.py`
- `test_extract_skills_electricidad`
- `test_estimated_level_avanzado`
- `test_estimated_level_basico`

---

*P-006 | Linku DRTPE-Junín · Implementado Sprint 2 · RF059–RF075*
