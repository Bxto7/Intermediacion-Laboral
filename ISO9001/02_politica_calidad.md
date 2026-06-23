# ISO 9001:2015 — Cláusula 5
## Liderazgo y Política de Calidad

**Sistema:** Linku — Sistema de Intermediación Laboral DRTPE-Junín
**Revisión:** 1.0 | Fecha: 2026-06-23

---

## 5.1 Liderazgo y compromiso

### 5.1.1 Generalidades

El equipo de investigación (Rojas Peña W. / Tovar Sanchez C.) asume el liderazgo del SGC con los siguientes compromisos:

- Asegurar que la política y los objetivos de calidad sean coherentes con el contexto y la dirección estratégica de la DRTPE-Junín.
- Integrar los requisitos del SGC en los procesos de negocio del sistema (cada proceso lleva trazabilidad a un RF/RNF específico).
- Asegurar que se disponga de los recursos necesarios para el SGC (entorno Docker reproducible, CI/CD con SonarQube).
- Comunicar la importancia de la gestión de calidad eficaz al equipo técnico.
- Asegurar que el SGC logre sus resultados previstos (cobertura pytest ≥80%, Quality Gate SonarQube OK).
- Apoyar la mejora continua a través de auditorías periódicas (FURPS+, OWASP).

### 5.1.2 Enfoque al cliente

El sistema Linku está diseñado con **enfoque en el usuario de baja alfabetización digital**:
- Textos en español peruano simple (DNI, S/., boleta de pago).
- Asistencia NLP para traducir lenguaje coloquial a competencias formales.
- Wizard de 6 pasos para jóvenes sin experiencia previa.
- Portafolio visual para trabajadores de oficio sin CV formal.
- Mensajes de error específicos y accionables en todos los formularios.

---

## 5.2 Política de Calidad

### Declaración de política

> **Linku se compromete a proporcionar un servicio de intermediación laboral digital que sea accesible, seguro, justo y eficaz, reduciendo las brechas de acceso al empleo en la región Junín mediante el uso responsable de Machine Learning y Procesamiento de Lenguaje Natural, en plena conformidad con la Ley N° 29733 de Protección de Datos Personales y los principios de equidad algorítmica.**

### Principios de la política

| Principio | Implementación Técnica |
|-----------|----------------------|
| **Accesibilidad** | Wizard guiado, lenguaje coloquial aceptado por NLP, UX para baja alfabetización digital |
| **Seguridad de datos** | JWT RS256, AES-256-GCM para PII, bcrypt cost 12, blacklist de tokens en Redis |
| **Equidad** | Disparate impact < 0.80 activa re-ranking automático (`equity_ranker`); auditoría en `equity_audit_log` |
| **Trazabilidad** | Audit log inmutable en BD; structlog con campos event/user_id/ip/duration_ms |
| **Mejora continua** | Auditorías FURPS+/OWASP por sprint; Quality Gate SonarQube; pytest ≥80% de cobertura |
| **Consentimiento informado** | `consent_given=True` obligatorio (Ley 29733); tabla `consent_records` auditable |

---

## 5.3 Roles, responsabilidades y autoridades en la organización

| Rol | Responsabilidad en el SGC |
|-----|--------------------------|
| **Investigador / Arquitecto de Sistema** | Definición de RF/RNF; diseño de arquitectura; aprobación de cambios en procesos críticos (matching, seguridad) |
| **Desarrollador Backend (python-pro)** | Implementación de endpoints FastAPI, modelos SQLAlchemy, esquemas Pydantic; responsable de cobertura pytest |
| **ML Engineer** | Implementación y validación de pipelines NLP/embeddings; optimización del motor de matching; métricas de equidad |
| **Security Auditor** | Auditorías OWASP por sprint; hardening de seguridad; cumplimiento Ley 29733 |
| **DevOps Engineer** | Infraestructura Docker; migraciones Alembic; CI/CD; SonarQube |
| **Senior Frontend** | Implementación de la UI React; accesibilidad WCAG 2.1 AA; integración con API |
| **Admin DRTPE** | Operación del panel administrativo; revisión de KPIs; moderación de contenido |

---

*Linku — DRTPE-Junín · ISO 9001:2015 Cláusula 5 · Huancayo 2026*
