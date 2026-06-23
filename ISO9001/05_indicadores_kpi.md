# ISO 9001:2015 — Cláusula 9
## Evaluación del Desempeño — Indicadores y KPIs

**Sistema:** Linku — Sistema de Intermediación Laboral DRTPE-Junín
**Revisión:** 1.0 | Fecha: 2026-06-23

---

## 9.1 Seguimiento, medición, análisis y evaluación

### 9.1.1 KPIs de la Investigación (Tesis Académica)

Calculados automáticamente por `kpi_calculator.py` y disponibles en el panel admin:

| Código | Indicador | Fórmula | Frecuencia | Proceso |
|--------|-----------|---------|------------|---------|
| **VIL** | Velocidad de Inserción Laboral | Días promedio desde registro hasta primer contrato, por `worker_type` | Diaria | P-013, P-020 |
| **IVP** | Índice de Visibilidad de Perfil | (Apariciones en búsquedas / Total consultas) × 100, por `worker_type` | Diaria | P-013 |
| **TF** | Tasa de Formalización | (Workers con ≥1 contrato / Total registrados) × 100, por `worker_type` | Diaria | P-013 |
| **RBS** | Reducción de Brecha Salarial | ((Ingreso post − Ingreso pre) / Ingreso pre) × 100, promedio por tipo | Diaria | P-013, P-019 |
| **TCC** | Tasa de Completitud de CV | (Workers con CV generado / Total primer_empleo + oficio) × 100 | Diaria | P-013, P-009 |
| **IVM** | Índice de Visibilidad en Marketplace | (Listings activos / Total workers OFICIO) × 100 | Diaria | P-013, P-015 |
| **TCSS** | Tasa de Cold-Start Superado | (Workers primer_empleo/oficio con ≥1 match / Total) × 100 | Diaria | P-013, P-008 |

---

### 9.1.2 KPIs de Calidad del Sistema

| Indicador | Meta | Herramienta de medición | Frecuencia |
|-----------|------|------------------------|------------|
| Cobertura de pruebas (pytest --cov) | ≥ 80% | pytest-cov → `backend/coverage.xml` | Por sprint |
| Quality Gate SonarQube | OK (0 vulnerabilidades) | SonarQube (puerto 9000) | Por sprint |
| Bugs activos SonarQube (Reliability) | Rating A | SonarQube | Por sprint |
| Code smells SonarQube | < 50 | SonarQube | Por sprint |
| Errores de linting (ruff) | 0 errores | ruff check . | Continua (CI) |
| Tests totales (backend) | ≥ 266 (Sprint 3 baseline) | pytest -v | Por sprint |
| Tests frontend | > 0 | Vitest (pendiente Sprint 6) | Por sprint |

---

### 9.1.3 KPIs de Seguridad

| Indicador | Meta | Fuente |
|-----------|------|--------|
| Vulnerabilidades OWASP detectadas | 0 críticas, 0 altas | SonarQube + Auditoría OWASP manual |
| Rating de Seguridad SonarQube | A | SonarQube |
| Datos PII en texto plano en BD | 0 campos | Verificación de columnas BYTEA |
| Datos PII en logs | 0 ocurrencias | grep en structlog outputs |
| Tokens activos en blacklist correctamente | 100% de logouts registrados | Redis keys `blacklist:*` |

---

### 9.1.4 KPIs de Performance

| Indicador | Meta | Herramienta |
|-----------|------|-------------|
| Tiempo respuesta login | < 500ms | Header `X-Process-Time` |
| Tiempo respuesta matching | < 2 segundos | Header `X-Process-Time` |
| Tiempo generación PDF (modo async) | < 5 segundos | Celery task duration (Flower) |
| Tiempo generación embedding | < 500ms | Celery task duration |
| Cache hit rate (KPIs dashboard) | > 80% | Redis INFO hits/misses |

---

### 9.1.5 KPIs de Infraestructura

| Indicador | Meta | Herramienta |
|-----------|------|-------------|
| Disponibilidad del sistema | > 99% (horario DRTPE) | Prometheus `http_requests_total` |
| Workers Celery activos | 4 workers (embed, cv, notif, reports) | Flower (puerto 5555) |
| Tareas Celery exitosas | > 99% | Flower → "Successful" |
| Tareas Celery fallidas | < 1% | Flower → "Failed" con alerta |
| Conexiones BD activas | < 80% del pool | Prometheus + pgvector |

---

## 9.2 Auditoría Interna

### Plan de Auditorías por Sprint

| Sprint | Auditoría | Herramienta | Resultado Actual |
|--------|-----------|------------|-----------------|
| Sprint 1 | OWASP básico: auth, JWT, rate-limit | Manual + SonarQube | Hardening en Sprint 2 |
| Sprint 2 | Seguridad NLP + AES + rate-limit global | Manual | 5 issues resueltos |
| Sprint 3 | FURPS+ — cobertura funcional, performance, reliability | Auditoría estática | Scorecard 80/100 |
| Sprint 4 | OWASP — panel admin, datos económicos, WebSocket | Manual | Conector DRTPE, consent_records |
| Sprint 5 | Auditoría final FURPS+ + OWASP | Manual | SECURITY_AUDIT.md generado |

### Resultados de Auditoría FURPS+ (Sprint 5)

| Categoría | Puntaje | Tendencia |
|-----------|---------|-----------|
| Functionality | 80/100 | → Estable (ml_score stub pendiente) |
| Usability | 88/100 | ↑ Mejora en mensajes de error |
| Reliability | 75/100 | → Estable (PDF síncrono pendiente) |
| Performance | 75/100 | → Estable (pgvector subutilizado pendiente) |
| Supportability | 80/100 | ↑ Mejora en tests backend |
| Plus (seguridad) | 84/100 | ↑ Mejora continua |
| **GLOBAL** | **80/100** | **Bueno** |

---

## 9.3 Revisión por la Dirección

La revisión del SGC se realiza al cierre de cada sprint y debe incluir:

1. Estado de los KPIs de investigación (7 indicadores).
2. Estado de los KPIs de calidad (cobertura, SonarQube, linting).
3. Bugs resueltos y nuevos hallazgos.
4. Estado de la deuda técnica priorizada.
5. Ajustes al plan del próximo sprint.

**Formato:** Actualización de la tabla de Bugs/Deuda en `CLAUDE.md` y del plan en `03_planificacion.md`.

---

*Linku — DRTPE-Junín · ISO 9001:2015 Cláusula 9 · Huancayo 2026*
