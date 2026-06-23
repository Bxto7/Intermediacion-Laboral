# P-002 — Detección y Clasificación de Tipo de Trabajador
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M02 — Perfil del Trabajador (Onboarding)
**RF Cubiertos:** RF016–RF022
**Sprint de implementación:** Sprint 1
**Componentes clave:** `backend/app/services/onboarding/detector.py`, `backend/app/api/v1/onboarding.py`

---

## 1. Propósito

Clasificar automáticamente a cada nuevo trabajador en uno de los tres tipos de perfil (`primer_empleo`, `oficio`, `experiencia`) a partir de un cuestionario de dos preguntas, y crear el perfil base en la base de datos. Esta clasificación determina el flujo completo de construcción de perfil y los pesos del motor de matching.

---

## 2. Alcance

Aplica exclusivamente a usuarios con rol `WORKER` que aún no tienen un registro en la tabla `workers`. Se ejecuta una única vez por usuario. No puede modificarse directamente (ver P-003 / RF023 para cambio de tipo con confirmación).

---

## 3. Entradas del Proceso

| Entrada | Fuente | Validación |
|---------|--------|------------|
| `is_first_job` (bool) | Frontend — cuestionario onboarding | Pydantic — campo obligatorio |
| `is_trade_worker` (bool) | Frontend — cuestionario onboarding | Pydantic — campo obligatorio |
| `trade_category` (TradeCategory \| None) | Frontend — selección de categoría | Requerido si `is_trade_worker=True` |
| `user_id` del token JWT | Header Authorization | `require_role(WORKER)` |

---

## 4. Salidas del Proceso

| Salida | Destino | Contenido |
|--------|---------|-----------|
| `worker_type` determinado | BD tabla `workers` | `primer_empleo` / `oficio` / `experiencia` |
| Perfil base en BD | Tabla `workers` | `full_name`/`dni` placeholder cifrado, `embedding=NULL`, `profile_completeness=0` |
| `OnboardingResponse` | Frontend | `{worker_type, worker_id, next_step, message}` |
| Redirección de UI | Frontend router | `/wizard/step/1` / `/oficio/portfolio` / `/dashboard` |
| Registro en `audit_logs` | BD | `action="worker_profile_created"` |

---

## 5. Flujo del Proceso

```
[Trabajador autenticado] POST /api/v1/onboarding/detect-type
    │
    ├─► Verificar rol WORKER (require_role)
    ├─► Verificar que no existe registro en workers (409 si ya tiene perfil)
    │
    ├─► detect_worker_type(answers: OnboardingAnswers) — función pura
    │       │
    │       ├─► is_first_job == True          → worker_type = "primer_empleo"
    │       ├─► is_first_job == False
    │       │   is_trade_worker == True       → worker_type = "oficio"
    │       └─► else                          → worker_type = "experiencia"
    │
    ├─► create_worker_profile(user_id, worker_type, trade_category, db)
    │       │
    │       ├─► Cifrar placeholder "pendiente" → full_name (BYTEA AES-256)
    │       ├─► Cifrar placeholder "00000000"  → dni (BYTEA AES-256)
    │       ├─► Generar username = slugify(full_name) + sufijo único
    │       ├─► profile_completeness = 0
    │       └─► embedding = NULL (se genera en P-007 tras completar perfil)
    │
    ├─► get_next_step_url(worker_type):
    │       ├─► primer_empleo → "/wizard/step/1"
    │       ├─► oficio        → "/oficio/portfolio"
    │       └─► experiencia   → "/dashboard"
    │
    └─► Retornar OnboardingResponse + registrar en audit_logs
```

---

## 6. Lógica de Clasificación — Árbol de Decisión

```
¿Es tu primer empleo? (is_first_job)
    │
    ├─► SÍ → PRIMER_EMPLEO
    │         Flujo: Wizard de 6 pasos asistido por NLP
    │         Template CV: primer_empleo.html
    │         Pesos matching: coseno=0.65, ml=0.35, reputación=0.00
    │
    └─► NO
          ¿Trabajas en un oficio? (is_trade_worker)
              │
              ├─► SÍ + trade_category → OFICIO
              │         Flujo: Portafolio de trabajos
              │         Template CV: oficio.html
              │         Pesos matching: coseno=0.45, ml=0.25, reputación=0.30
              │
              └─► NO → EXPERIENCIA
                        Flujo: Parseo de CV (PDF/DOCX)
                        Template CV: experiencia.html
                        Pesos matching: coseno=0.50, ml=0.30, reputación=0.20
```

---

## 7. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Función pura `detect_worker_type` | Sin efectos secundarios; 100% testeable de forma unitaria |
| Validación Pydantic `OnboardingAnswers` | Si `is_trade_worker=True` y `trade_category=None` → `ValidationError` inmediato |
| Idempotencia | Un usuario no puede crear dos perfiles; 409 en el segundo intento |
| Placeholder cifrado | Los datos PII no se almacenan en texto plano desde el primer momento |
| Audit log | Trazabilidad del momento exacto de clasificación y del `worker_type` asignado |

---

## 8. Indicadores de Desempeño

| Indicador | Fuente | Uso |
|-----------|--------|-----|
| Distribución de tipos en onboarding | BD: `SELECT worker_type, COUNT(*) FROM workers GROUP BY worker_type` | KPI para DRTPE: composición de usuarios |
| Tasa de onboarding completado | `audit_logs` count(action="worker_profile_created") / count(action="user_registered") | Embudo de conversión |
| Tiempo hasta primer perfil completo | `workers.updated_at - workers.created_at` | Experiencia de usuario |

---

## 9. Pruebas Automatizadas

Archivo: `backend/tests/unit/test_onboarding_detector.py`
- `test_is_first_job_true_returns_primer_empleo`
- `test_trade_worker_true_returns_oficio`
- `test_neither_returns_experiencia`
- `test_oficio_without_trade_category_raises_value_error`
- `test_worker_type_values_are_lowercase_strings`

Archivo: `backend/tests/integration/test_api_onboarding.py`
- `test_onboarding_primer_empleo`
- `test_onboarding_oficio_con_categoria`
- `test_onboarding_duplicado_devuelve_409`
- `test_onboarding_status_antes_y_despues`

---

*P-002 | Linku DRTPE-Junín · Implementado Sprint 1 · RF016–RF022*
