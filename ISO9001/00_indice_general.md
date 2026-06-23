# Sistema de Gestión de Calidad ISO 9001:2015
## Linku — Sistema de Intermediación Laboral DRTPE-Junín

**Organización:** Dirección Regional de Trabajo y Promoción del Empleo de Junín (DRTPE-Junín)
**Ubicación:** Huancayo, Perú
**Versión del documento:** 1.0
**Fecha de emisión:** 2026-06-23
**Clasificación:** Interno — Investigación Académica

---

## Índice General

Este directorio documenta los procesos automatizados del sistema **Linku** en conformidad con el estándar ISO 9001:2015, estructurado para servir como evidencia de la tesis académica *"Implementación de un Sistema de Intermediación Laboral mediante Machine Learning y NLP para la Reducción de Brechas de Acceso al Empleo — DRTPE Junín"*.

---

### Sección 1 — Contexto y Alcance

| Documento | Descripción |
|-----------|-------------|
| [01_contexto_organizacional.md](01_contexto_organizacional.md) | Cláusula 4 — Contexto, partes interesadas y alcance del SGC |
| [02_politica_calidad.md](02_politica_calidad.md) | Cláusula 5 — Liderazgo y política de calidad |
| [03_planificacion.md](03_planificacion.md) | Cláusula 6 — Planificación, riesgos y objetivos |

---

### Sección 2 — Mapa de Procesos

| Documento | Descripción |
|-----------|-------------|
| [04_mapa_procesos.md](04_mapa_procesos.md) | Diagrama y relaciones entre los 20 procesos automatizados |

---

### Sección 3 — Procesos Automatizados

| Código | Proceso | Módulo | RF Cubiertos |
|--------|---------|--------|--------------|
| [P-001](procesos/P-001_registro_autenticacion.md) | Registro y Autenticación de Usuarios | M01 — Identidad | RF001–RF012 |
| [P-002](procesos/P-002_onboarding_clasificacion.md) | Detección y Clasificación de Tipo de Trabajador | M02 — Onboarding | RF016–RF022 |
| [P-003](procesos/P-003_perfil_primer_empleo.md) | Construcción de Perfil — Primer Empleo | M02 / M06 | RF023–RF035, RF096–RF100 |
| [P-004](procesos/P-004_perfil_oficio.md) | Construcción de Perfil — Oficio | M02 / M04 | RF056–RF065 |
| [P-005](procesos/P-005_perfil_experiencia.md) | Construcción de Perfil — Experiencia | M02 / M04 | RF066–RF075 |
| [P-006](procesos/P-006_extraccion_nlp_competencias.md) | Extracción NLP de Competencias | M04 — NLP | RF059–RF075 |
| [P-007](procesos/P-007_embeddings_vectoriales.md) | Generación Automática de Embeddings Vectoriales | M04 / M05 | RF076–RF079 |
| [P-008](procesos/P-008_motor_matching.md) | Motor de Emparejamiento (Matching) | M05 — ML | RF080–RF095 |
| [P-009](procesos/P-009_generacion_cv.md) | Generación Automática de CV / Hoja de Vida | M06 — Identidad Laboral | RF096–RF110 |
| [P-010](procesos/P-010_gestion_ofertas_empleo.md) | Publicación y Gestión de Ofertas de Empleo | M03 — Empleadores | RF036–RF055 |
| [P-011](procesos/P-011_alertas_empleo.md) | Sistema de Alertas de Empleo | M07 — Alertas | RF111–RF117 |
| [P-012](procesos/P-012_notificaciones_tiempo_real.md) | Notificaciones en Tiempo Real (WebSocket) | M08 — Notificaciones | RF126–RF135 |
| [P-013](procesos/P-013_panel_admin_kpis.md) | Panel Administrativo DRTPE y KPIs de Investigación | M09 — Reportes | RF136–RF145 |
| [P-014](procesos/P-014_equidad_explicabilidad.md) | Equidad Algorítmica y Explicabilidad del Matching | M10 — Equidad | RF146–RF155 |
| [P-015](procesos/P-015_marketplace_servicios.md) | Marketplace de Servicios de Oficio | M07 — Marketplace | RF118–RF125 |
| [P-016](procesos/P-016_moderacion_contenido.md) | Moderación de Contenido del Marketplace | M07 — Moderación | RF118, RF123–RF125 |
| [P-017](procesos/P-017_integracion_drtpe.md) | Integración con la Bolsa de Trabajo DRTPE | M12 — Integración | RF161–RF165 |
| [P-018](procesos/P-018_seguridad_proteccion_datos.md) | Seguridad y Protección de Datos Personales (PII) | Transversal — Seguridad | RNF001–RNF008 |
| [P-019](procesos/P-019_encuestas_economicas.md) | Encuestas Económicas y Medición de Impacto | M09 / Investigación | RF136, RF140 |
| [P-020](procesos/P-020_reportes_investigacion.md) | Generación de Reportes de Investigación | M09 — Reportes | RF136–RF145 |

---

### Sección 4 — Evaluación y Mejora

| Documento | Descripción |
|-----------|-------------|
| [05_indicadores_kpi.md](05_indicadores_kpi.md) | Cláusula 9 — Indicadores de desempeño y KPIs de la tesis |
| [06_mejora_continua.md](06_mejora_continua.md) | Cláusula 10 — Hallazgos de auditoría FURPS+/OWASP y plan de mejora |

---

### Correspondencia con ISO 9001:2015

| Cláusula ISO 9001:2015 | Documentos Linku |
|------------------------|-----------------|
| 4 — Contexto de la organización | 01_contexto_organizacional.md |
| 5 — Liderazgo | 02_politica_calidad.md |
| 6 — Planificación | 03_planificacion.md |
| 7 — Apoyo (infraestructura, recursos) | 04_mapa_procesos.md, P-018 |
| 8 — Operación | P-001 a P-020 |
| 9 — Evaluación del desempeño | 05_indicadores_kpi.md |
| 10 — Mejora | 06_mejora_continua.md |

---

*Sistema Linku — DRTPE-Junín · Sprint 5 · Huancayo, Perú · 2026*
