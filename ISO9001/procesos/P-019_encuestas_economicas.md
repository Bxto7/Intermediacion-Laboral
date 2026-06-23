# P-019 — Encuestas Económicas y Medición de Impacto
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M09 / Investigación
**RF Cubiertos:** RF136, RF140 (datos para RBS)
**Sprint de implementación:** Sprint 4
**Componentes clave:**
- `backend/app/api/v1/surveys.py`
- Modelo `EconomicSurvey` + `ConsentRecord`

---

## 1. Propósito

Recolectar datos económicos de los trabajadores (ingreso mensual pre y post intervención) para calcular el KPI **RBS — Reducción de Brecha Salarial**, el indicador de impacto central de la investigación, en estricto cumplimiento de la Ley N° 29733.

---

## 2. Diseño de la Encuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `worker_id` | UUID | Trabajador encuestado |
| `survey_phase` | VARCHAR(10) | `"pre"` (antes de usar Linku) o `"post"` (después) |
| `monthly_income` | BYTEA | Ingreso mensual en S/. — **cifrado AES-256-GCM** |
| `employment_type` | VARCHAR(30) | formal / informal / desempleado |
| `consent_given` | BOOLEAN | Consentimiento explícito — obligatorio Ley 29733 |

---

## 3. Flujo del Proceso

```
[Trabajador autenticado] POST /api/v1/surveys/economic
    {worker_id, survey_phase, monthly_income, employment_type, consent_given}
    │
    ├─► require_consent(consent_given, "datos_economicos")
    │       └─► [Si False] 400 "Se requiere consentimiento informado... Ley N° 29733"
    │
    ├─► Verificar que worker.user_id == token.sub (403 si no)
    │
    ├─► encrypt_field(str(monthly_income)) → BYTEA cifrado AES-256-GCM
    │       │
    │       └─► NUNCA almacenar monthly_income en texto plano
    │
    ├─► Crear EconomicSurvey {worker_id, survey_phase, monthly_income=encrypted, consent_given=True}
    │
    ├─► Crear ConsentRecord {user_id, data_purpose="datos_economicos", ip_address, consent_given=True}
    │       └─► Registro auditable del consentimiento (Ley 29733 Art. 13)
    │
    ├─► commit BD
    └─► Retornar EconomicSurveyResponse {id, survey_phase}
```

---

## 4. Cálculo del KPI RBS (en P-013)

```python
# En kpi_calculator.py → calculate_rbs():
# 1. Obtener pares (pre, post) por worker_id
# 2. Descifrar en memoria (decrypt_field) — NUNCA loguear
# 3. Calcular variación: ((post - pre) / pre) × 100
# 4. Promediar por worker_type

# Ejemplo:
income_pre = float(decrypt_field(row.income_pre_encrypted))   # S/. 900
income_post = float(decrypt_field(row.income_post_encrypted)) # S/. 1200
change_pct = ((1200 - 900) / 900) * 100  # +33.3%
```

---

## 5. Registro de Consentimientos (`consent_records`)

| Campo | Contenido |
|-------|-----------|
| `user_id` | UUID del trabajador |
| `data_purpose` | `datos_economicos` / `perfil` / `portfolio` / `contrato_laboral` |
| `ip_address` | IP del cliente al momento del consentimiento |
| `consent_given` | TRUE (solo se registra si se dio consentimiento) |
| `consent_version` | `"1.0"` (versión de la política de privacidad vigente) |
| `created_at` | TIMESTAMPTZ |

**Índice:** `(user_id, data_purpose, created_at DESC)`

---

## 6. Controles de Calidad y Privacidad

| Control | Descripción |
|---------|-------------|
| Consentimiento pre-requisito | Sin `consent_given=True` → 400 inmediato con referencia a Ley 29733 |
| Cifrado antes de persistir | `encrypt_field()` antes de cualquier `db.add()` |
| Sin montos en logs | Los datos económicos no aparecen en ningún log estructurado |
| Ownership verificado | El worker solo puede crear encuestas para sí mismo |
| Pares pre/post requeridos para RBS | Si falta la fase `pre` o `post`, el worker no aporta al KPI (seguridad estadística) |
| Registro auditable de consentimiento | Cada consentimiento queda en `consent_records` con IP y timestamp |

---

## 7. Consideraciones Éticas de la Investigación

Conforme a la Ley N° 29733 y los principios éticos de la investigación académica:

1. **Principio de proporcionalidad:** Solo se solicitan los datos mínimos necesarios para calcular el KPI (ingreso mensual y tipo de empleo).
2. **Principio de finalidad:** Los datos se usan exclusivamente para calcular el KPI RBS de la tesis; no se comparten con terceros.
3. **Derecho de rectificación:** El trabajador puede corregir su encuesta contactando a la DRTPE.
4. **Retención limitada:** Los datos económicos se retienen mientras el sistema Linku opere; al finalizar la investigación se notificará a los participantes.

---

## 8. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Tasa de participación en encuesta | > 30% de trabajadores activos | `COUNT(DISTINCT worker_id FROM economic_surveys) / COUNT(workers)` |
| Pares pre/post completados | > 50% de los que hicieron "pre" | Correlación por worker_id |
| Consentimientos registrados | 100% de encuestas tienen ConsentRecord | `economic_surveys` vs `consent_records` |

---

*P-019 | Linku DRTPE-Junín · Implementado Sprint 4 · RF136 (RBS) · Ley 29733*
