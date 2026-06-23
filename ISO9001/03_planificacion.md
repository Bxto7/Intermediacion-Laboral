# ISO 9001:2015 — Cláusula 6
## Planificación

**Sistema:** Linku — Sistema de Intermediación Laboral DRTPE-Junín
**Revisión:** 1.0 | Fecha: 2026-06-23

---

## 6.1 Acciones para abordar riesgos y oportunidades

### Riesgos identificados

| ID | Riesgo | Probabilidad | Impacto | Control Implementado |
|----|--------|-------------|---------|----------------------|
| R-001 | Tokens JWT comprometidos por robo | Media | Alto | Blacklist por JTI en Redis; refresh_token de 7 días; blacklist total por usuario post-reset de contraseña |
| R-002 | Exposición de PII (DNI, teléfono) | Baja | Crítico | AES-256-GCM con nonce aleatorio 12 bytes; campos BYTEA en BD; nunca en logs ni respuestas |
| R-003 | Sesiones simultáneas abusivas por WebSocket | Media | Medio | Límite de 3 conexiones por usuario (Redis INCR/DECR); código de cierre 4029 al exceder |
| R-004 | Fallo de generación de PDF bajo carga | Alta | Alto | Tarea Celery asíncrona (`cv_generation`); cola dedicada con worker separado |
| R-005 | Matching sesgado por grupo demográfico | Media | Alto | Equity ranker: disparate impact < 0.80 dispara re-ranking; auditoría en `equity_audit_log` |
| R-006 | Datos de ingreso mensual expuestos | Baja | Crítico | AES-256-GCM para `monthly_income`; consentimiento Ley 29733 obligatorio antes de persistir |
| R-007 | Scraping/abuso de endpoints públicos | Alta | Medio | Rate limiting Redis: 1000 req/min global, 10 req/min auth, 30 req/min matching |
| R-008 | CV tipo experiencia vacío (bug CV-EXP-VACIO) | Alta | Medio | Identificado en auditoría FURPS+; pendiente cableado de datos parseados (deuda técnica) |
| R-009 | Índice pgvector sin uso en matching | Alta | Medio | Identificado en auditoría FURPS+ (P1); migración a operador `<=>` planificada |
| R-010 | Importación de roles incorrecta sin autenticación | Baja | Crítico | `require_role` como dependency FastAPI; AdminRouter con `dependencies=[Depends(require_role(ADMIN))]` en router base |

### Oportunidades identificadas

| ID | Oportunidad | Plan |
|----|-------------|------|
| O-001 | Entrenamiento del modelo ML con datos reales de colocación | Sprint 6 (posterior a tesis): entrenar modelo supervisado con datos de `contracts` y `applications` |
| O-002 | Integración real con API de la Bolsa DRTPE | Sprint 6: reemplazar `DRTPEConnectorStub` por `DRTPEConnectorReal` |
| O-003 | Implementación de SMTP real para notificaciones | Sprint 6: reemplazar stubs Celery (`notifications.py`) con AWS SES o SendGrid |
| O-004 | Refresh automático de token en frontend | Sprint 6: interceptor Axios con lógica de retry a `/auth/refresh` en 401 |
| O-005 | Pruebas automatizadas del frontend (0 tests actualmente) | Sprint 6: Vitest + React Testing Library para wizard, guards y contextos |

---

## 6.2 Objetivos de calidad y planificación

### Objetivos de calidad

| Objetivo | Indicador | Meta | Estado Actual |
|---------|-----------|------|---------------|
| OC-001 | Cobertura de pruebas backend | ≥ 80% (pytest --cov) | Cumplido (Sprint 3: 266 tests, 80%) |
| OC-002 | Calidad de código SonarQube | Quality Gate OK; 0 vulnerabilidades | Cumplido (Rating Seguridad A, Mantenibilidad A) |
| OC-003 | Linting Python | ruff check . sin errores | Cumplido (verificado por sprint) |
| OC-004 | Cobertura de requerimientos funcionales | 165 RF documentados y trazados | Cumplido (RF001–RF165 distribuidos en 5 sprints) |
| OC-005 | Tiempo de respuesta del matching | < 2 segundos para top-K resultados | Pendiente (pgvector subutilizado — ver R-009) |
| OC-006 | Equidad algorítmica (disparate impact) | ≥ 0.80 entre grupos | Implementado; monitoreo continuo por `equity_audit_log` |
| OC-007 | Protección de PII | 0 datos sensibles en texto plano en BD | Cumplido (AES-256-GCM verificado en auditoría) |
| OC-008 | Consentimiento informado documentado | 100% de operaciones con PII tienen registro en `consent_records` | Implementado en surveys y portfolio |

---

## 6.3 Planificación de cambios

Los cambios en los procesos automatizados siguen el protocolo de control de versiones:

1. **Identificación:** el cambio se documenta en la tabla de Bugs/Deuda del `CLAUDE.md`.
2. **Análisis de impacto:** se revisan los procesos relacionados (P-001 a P-020) y los RF afectados.
3. **Implementación:** branch `fix/descripcion` o `feature/descripcion` en Git.
4. **Verificación:** pytest con cobertura ≥80% + ruff check + SonarQube antes del merge.
5. **Actualización de documentación:** CLAUDE.md y archivos ISO 9001 correspondientes.
6. **Registro:** commit en español con referencia al RF/RNF modificado.

### Sprints ejecutados

| Sprint | Período | Módulos Implementados | RF Cubiertos |
|--------|---------|----------------------|--------------|
| Sprint 1 | Mar 2026 | M01 Auth, M02 Perfil base, Infra Docker | RF001–RF035, 23 RNF |
| Sprint 2 | Abr 2026 | M03 Empleadores, M04 NLP, M06 Wizard, Portfolio | RF036–RF075, RF096–RF100 |
| Sprint 3 | May 2026 | M05 Matching, M06 CV PDF, M07 Alertas, M08 WebSocket, M10 Equidad | RF076–RF155 |
| Sprint 4 | May 2026 | M09 Admin DRTPE, KPIs, Encuestas, M12 Integración | RF136–RF165 |
| Sprint 5 | Jun 2026 | Moderación, Contratos, RF023/RF034, Equidad visible, Seed datos | RF023, RF034, RF118–RF125, RF150 |

---

*Linku — DRTPE-Junín · ISO 9001:2015 Cláusula 6 · Huancayo 2026*
