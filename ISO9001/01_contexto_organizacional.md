# ISO 9001:2015 — Cláusula 4
## Contexto de la Organización

**Sistema:** Linku — Sistema de Intermediación Laboral DRTPE-Junín
**Revisión:** 1.0 | Fecha: 2026-06-23

---

## 4.1 Comprensión de la organización y su contexto

### Organización
La **Dirección Regional de Trabajo y Promoción del Empleo de Junín (DRTPE-Junín)** es el organismo público responsable de fomentar el empleo formal y reducir las brechas de acceso al mercado laboral en la región Junín, Perú. Opera desde su sede central en Huancayo.

### Contexto externo relevante
- Alta informalidad laboral en la región Junín: estimada en >65% de la PEA ocupada.
- Trabajadores de oficios manuales sin perfil digital ni currículum formal.
- Jóvenes en búsqueda de primer empleo sin historial laboral documentado.
- Mercado fragmentado: oferta de empleo dispersa entre empresas formales, municipalidades, y servicios informales.
- Cobertura geográfica: distritos de Huancayo, El Tambo y Chilca como área de influencia directa.
- Marco normativo: Ley N° 29733 (Protección de Datos Personales), Decreto Legislativo N° 728 (Fomento del Empleo).

### Contexto interno relevante
- El sistema Linku es desarrollado como investigación académica (tesis de pregrado — Universidad Continental).
- Tecnología: backend Python/FastAPI, base de datos PostgreSQL con pgvector, ML/NLP con sentence-transformers.
- Infraestructura: contenedores Docker, workers Celery, Redis, Prometheus/Grafana.
- Equipo de investigación: Rojas Peña W. / Tovar Sanchez C.

---

## 4.2 Comprensión de las necesidades y expectativas de las partes interesadas

| Parte Interesada | Rol en el Sistema | Necesidades Clave |
|-----------------|-------------------|-------------------|
| **Trabajador — Primer Empleo** | Usuario del wizard de 6 pasos | Obtener un CV digital, conocer sectores compatibles con sus habilidades blandas |
| **Trabajador — Oficio** | Usuario del portafolio | Visibilidad digital de sus trabajos, contratación directa desde el marketplace |
| **Trabajador — Experiencia** | Usuario del parseo de CV | Matching preciso con ofertas formales, portabilidad de su historial laboral |
| **Empleador** | Publicador de ofertas | Acceso a candidatos clasificados, score de compatibilidad, gestión de postulaciones |
| **DRTPE-Junín (Admin)** | Administrador del sistema | KPIs de colocación laboral, reportes para políticas públicas, datos de investigación |
| **Moderador** | Supervisor del marketplace | Control de contenido inapropiado, colas de revisión de flags |
| **Equipo Investigador** | Desarrollador / Auditor | Cobertura de RF/RNF, calidad de código, resultados de KPIs de la tesis |
| **Universidad Continental** | Entidad evaluadora | Rigor metodológico, documentación, evidencia de funcionamiento |

---

## 4.3 Determinación del alcance del Sistema de Gestión de Calidad

### Alcance
El SGC cubre el ciclo completo de intermediación laboral automatizada del sistema Linku, desde el registro del usuario hasta la colocación laboral, incluyendo:

1. Autenticación y onboarding de usuarios (trabajadores y empleadores).
2. Construcción de perfil diferenciada por tipo de trabajador (`primer_empleo`, `oficio`, `experiencia`).
3. Extracción automática de competencias mediante NLP (embeddings semánticos, spaCy, diccionario local Huancayo).
4. Motor de emparejamiento (matching) basado en similitud coseno pgvector + score ML.
5. Generación automática de CV/Hoja de Vida en PDF (WeasyPrint + Jinja2).
6. Gestión de ofertas de empleo y postulaciones.
7. Marketplace de servicios de oficio con moderación.
8. Alertas y notificaciones en tiempo real.
9. Panel administrativo con KPIs de investigación.
10. Equidad algorítmica y explicabilidad de resultados.
11. Encuestas económicas y medición de impacto de la intervención.
12. Protección de datos personales (Ley 29733).

### Exclusiones justificadas
- **Integración real con DRTPE**: el conector externo es un stub funcional; la integración en producción queda fuera del alcance de la tesis.
- **Modelo ML supervisado entrenado**: el `ml_score` es fijo (0.5 stub) hasta contar con datos reales de colocación suficientes para entrenamiento.
- **SMTP real**: el envío de emails es un stub de notificación (solo log estructurado).

---

## 4.4 Sistema de Gestión de Calidad y sus procesos

El sistema implementa **20 procesos automatizados** interconectados, cuyas entradas, salidas, responsables y controles quedan documentados en los archivos `P-001` a `P-020` de este directorio.

El mapa de procesos se encuentra en [04_mapa_procesos.md](04_mapa_procesos.md).

Los procesos siguen la secuencia PDCA (Planificar — Hacer — Verificar — Actuar):
- **Planificar:** definición de RF/RNF, diseño de sprints.
- **Hacer:** implementación por sprints (Sprint 1–5).
- **Verificar:** auditorías FURPS+ y OWASP, pytest con cobertura ≥80%, SonarQube.
- **Actuar:** plan de mejora continua documentado en [06_mejora_continua.md](06_mejora_continua.md).

---

*Linku — DRTPE-Junín · ISO 9001:2015 Cláusula 4 · Huancayo 2026*
