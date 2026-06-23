# PLAN DE MEJORA DE SEGURIDAD INTEGRAL — ISO/IEC 27001
## Sistema Linku — DRTPE-Junín | Intermediación Laboral ML/NLP

---

| Campo | Valor |
|---|---|
| **Documento** | Plan de Mejora de Seguridad de la Información |
| **Basado en** | Auditoría ISO/IEC 27001 — Informe `auditoria-seguridad-iso27001.md` |
| **Sistema** | Linku v0.2.0 — Sprint 5 |
| **Elaborado por** | Consultor Senior en Seguridad de la Información y SGSI |
| **Fecha de elaboración** | 2026-06-23 |
| **Vigencia del plan** | 2026-06-23 al 2027-06-23 (12 meses) |
| **Clasificación** | CONFIDENCIAL — USO INTERNO |
| **Normas de referencia** | ISO/IEC 27001:2022 · ISO/IEC 27002:2022 · ISO/IEC 25010:2023 · Ley 29733 (Perú) |

---

## RESUMEN EJECUTIVO

### Contexto

El presente Plan de Mejora de Seguridad (PMS) fue elaborado a partir de los hallazgos de la auditoría de seguridad realizada el 23 de junio de 2026 al sistema Linku, plataforma de intermediación laboral operada por la Dirección Regional de Trabajo y Promoción del Empleo de Junín (DRTPE-Junín). El sistema maneja datos personales sensibles (DNI, nombre completo, teléfono) de trabajadores de sectores informales de la región Junín, Perú.

### Situación Actual

| Indicador | Valor actual |
|---|---|
| Cumplimiento ISO/IEC 27001 | ~35% |
| Nivel de madurez de seguridad | Nivel 2 — Gestionado (CMMI) |
| Riesgos críticos identificados | 5 |
| Riesgos medios identificados | 10 |
| Controles técnicos funcionales | 55% de los controles aplicables |
| Controles documentales/SGSI | 10% de los requisitos |

### Principales Vulnerabilidades Identificadas

1. **PII almacenada en texto claro en Redis** (DNI, nombre) — exposición directa de datos personales sensibles
2. **Auto-asignación de rol ADMIN** en registro público — riesgo de escalada de privilegios
3. **Sin autenticación multifactor** para cuentas administrativas — acceso con solo contraseña
4. **Sistema de emails stub** — recuperación de contraseña inoperativa en producción
5. **Sin backups identificados** de PostgreSQL ni Redis — riesgo de pérdida total de datos
6. **Sin marco SGSI documentado** — ausencia de cláusulas 4-7 y 9-10 de ISO 27001
7. **Sin mecanismo ARCO** — incumplimiento de Ley 29733 (protección de datos personales Perú)

### Riesgos Más Críticos

| Riesgo | Impacto | Probabilidad | Nivel |
|---|---|---|---|
| Exposición masiva de DNIs desde Redis | Alto | Medio | **ALTO** |
| Escalada de privilegios via registro ADMIN | Alto | Medio | **ALTO** |
| Compromiso de cuentas admin sin MFA | Alto | Medio | **ALTO** |
| Pérdida total de datos sin backups | Alto | Medio | **ALTO** |
| Incumplimiento Ley 29733 | Alto | Alto | **ALTO** |

### Beneficios Esperados tras la Implementación

- **Incremento del cumplimiento ISO/IEC 27001**: de 35% a 75-80% al completar el plan de 12 meses
- **Reducción de riesgos críticos**: de 5 a 0 en los primeros 90 días
- **Mejora del nivel de madurez**: de Nivel 2 a Nivel 3-4 (CMMI)
- **Protección reforzada de datos personales**: cumplimiento Ley 29733
- **Disponibilidad mejorada**: RPO/RTO definidos con backups automatizados
- **Preparación para auditoría formal**: condiciones mínimas alcanzables en 12 meses

### Incremento Esperado de Cumplimiento

```
Cumplimiento actual:   35% ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
Post corto plazo:      55% ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░
Post mediano plazo:    70% ██████████████████░░░░░░░░░░░░░░░░░░░░░░
Post largo plazo:      80% ████████████████████████░░░░░░░░░░░░░░░░
Meta certificación:    85% ████████████████████████████░░░░░░░░░░░░
```

---

## ANÁLISIS DETALLADO DE HALLAZGOS

### Hallazgo H-01: PII Almacenada en Texto Plano en Redis

**Problema detectado:** En `backend/app/api/v1/auth.py:73-77`, al registrar un usuario se almacena `full_name|DNI` como cadena de texto sin cifrar en Redis con clave `reg_identity:{user.id}` y TTL de 1 hora.

**Control ISO 27002 afectado:** A.8.24 — Uso de criptografía; A.8.10 — Eliminación de información.

**Causa raíz:** Decisión de diseño que priorizó la simplicidad de la transferencia de datos entre registro y onboarding, sin aplicar el mismo patrón de cifrado AES-256-GCM ya implementado para la base de datos.

**Impacto en la triada CID:**
- **Confidencialidad**: ALTO — Un actor con acceso a Redis obtiene DNIs en texto claro de usuarios recién registrados
- **Integridad**: BAJO — Los datos no se modifican, solo se exponen
- **Disponibilidad**: NINGUNO

**Riesgo asociado:** R-01 — Exposición masiva de DNIs y nombres de trabajadores vulnerables

**Criticidad:** CRÍTICA

---

### Hallazgo H-02: Auto-Asignación de Rol ADMIN en Registro Público

**Problema detectado:** En `backend/app/schemas/auth.py:10`, el campo `role: UserRole = UserRole.WORKER` en `RegisterRequest` permite que cualquier cliente HTTP envíe `role=ADMIN` y obtenga privilegios de administrador total del sistema.

**Control ISO 27002 afectado:** A.8.2 — Gestión de identidades; A.8.3 — Gestión de accesos; A.5.17 — Gestión de autenticación.

**Causa raíz:** Campo heredado del diseño inicial para facilitar pruebas, no eliminado al pasar a entorno productivo.

**Impacto en la triada CID:**
- **Confidencialidad**: ALTO — Admin accede a todos los datos de usuarios incluyendo PII descifrada
- **Integridad**: ALTO — Admin puede modificar cualquier registro del sistema
- **Disponibilidad**: ALTO — Admin puede desactivar usuarios, eliminar ofertas, invalidar sesiones

**Riesgo asociado:** R-05 — Escalada de privilegios no autorizada

**Criticidad:** CRÍTICA

---

### Hallazgo H-03: Ausencia Total de Autenticación Multifactor (MFA)

**Problema detectado:** No existe implementación de segundo factor de autenticación en ningún endpoint del sistema. Las cuentas ADMIN solo requieren email + contraseña.

**Control ISO 27002 afectado:** A.8.5 — Autenticación segura.

**Causa raíz:** No implementado en el roadmap del Sprint actual. La autenticación de un solo factor es el estado por defecto de muchos sistemas en fases tempranas.

**Impacto en la triada CID:**
- **Confidencialidad**: ALTO — Una contraseña comprometida da acceso total
- **Integridad**: ALTO — Acceso no autorizado puede modificar datos y configuraciones
- **Disponibilidad**: MEDIO — Atacante podría deshabilitar servicios

**Riesgo asociado:** R-03 — Compromiso de cuentas por credential stuffing o phishing

**Criticidad:** CRÍTICA

---

### Hallazgo H-04: Sistema de Notificaciones Email Inoperativo (Stub)

**Problema detectado:** `backend/app/tasks/notifications.py` contiene solo `logger.info()`. Los emails de verificación y recuperación de contraseña **nunca se envían**. Los tokens de reset existen en Redis pero el usuario nunca los recibe.

**Control ISO 27002 afectado:** A.8.5 — Autenticación segura; A.5.17 — Gestión de autenticación.

**Causa raíz:** Funcionalidad marcada como "stub Sprint 1" no implementada en sprints posteriores.

**Impacto en la triada CID:**
- **Confidencialidad**: ALTO — Un atacante puede solicitar reset de contraseña de una cuenta ajena para denegación de servicio; el usuario legítimo no es notificado
- **Integridad**: ALTO — Usuarios no pueden recuperar cuentas comprometidas
- **Disponibilidad**: ALTO — Recuperación de acceso inoperativa en producción

**Riesgo asociado:** R-02 — Inoperatividad del proceso de recuperación de credenciales

**Criticidad:** CRÍTICA

---

### Hallazgo H-05: Ausencia de Backups Identificados

**Problema detectado:** No se identificó ninguna configuración de backup en `docker-compose.yml`, scripts ni documentación. PostgreSQL y Redis operan sin respaldo automatizado documentado.

**Control ISO 27002 afectado:** A.8.13 — Respaldo de información.

**Causa raíz:** Infraestructura configurada para desarrollo, no para producción. La gestión de backups no fue incluida en el alcance de los sprints actuales.

**Impacto en la triada CID:**
- **Confidencialidad**: BAJO
- **Integridad**: ALTO — Pérdida de integridad de datos históricos sin recuperación posible
- **Disponibilidad**: ALTO — Fallo de hardware o ataque resulta en pérdida total de datos

**Riesgo asociado:** R-07 — Pérdida total e irrecuperable de datos de trabajadores

**Criticidad:** CRÍTICA

---

### Hallazgo H-06: Sin Mecanismo ARCO ni Cumplimiento Ley 29733

**Problema detectado:** No existe endpoint de eliminación/exportación de datos personales propios. No se identificó modal de consentimiento ni política de privacidad en el código. El sistema procesa DNIs sin registro en ARCO (MINJUSDH).

**Control ISO 27002 afectado:** A.5.31 — Requisitos legales, estatutarios, reglamentarios y contractuales.

**Causa raíz:** Foco en funcionalidades de negocio sin integración del cumplimiento legal peruano desde el diseño.

**Impacto en la triada CID:**
- **Confidencialidad**: ALTO — Usuarios no tienen control sobre sus datos personales
- **Integridad**: MEDIO
- **Disponibilidad**: BAJO

**Riesgo asociado:** R-14 — Sanción regulatoria, daño reputacional institucional

**Criticidad:** ALTA

---

### Hallazgo H-07: Token de Acceso con Vida Útil de 24 Horas

**Problema detectado:** `ACCESS_TOKEN_EXPIRE_MINUTES=1440` en `config.py`. Un token robado (XSS, red insegura, dispositivo perdido) permite acceso por 24 horas sin posibilidad de detección hasta que expire.

**Control ISO 27002 afectado:** A.8.5 — Autenticación segura; A.8.6 — Gestión de derechos de acceso.

**Causa raíz:** Ausencia de refresh automático en el frontend, compensada extendiendo la vida del access token para mejorar la UX.

**Criticidad:** ALTA

---

### Hallazgo H-08: Header Content-Security-Policy Ausente

**Problema detectado:** `SecurityHeadersMiddleware` incluye 5 headers de seguridad pero omite `Content-Security-Policy`, que es la principal defensa contra ataques XSS.

**Control ISO 27002 afectado:** A.8.9 — Gestión de la configuración.

**Causa raíz:** Configuración parcial del middleware. CSP requiere conocimiento de todas las fuentes de contenido legítimas del frontend.

**Criticidad:** ALTA

---

### Hallazgo H-09: Sin Marco SGSI Documentado (Cláusulas 4-10)

**Problema detectado:** Ausencia total de documentación del Sistema de Gestión de Seguridad de la Información: contexto organizacional, partes interesadas, declaración de aplicabilidad (SoA), política de seguridad, registro de riesgos formal, objetivos de seguridad.

**Control ISO 27001 afectado:** Cláusulas 4, 5, 6, 7, 9, 10 completas.

**Causa raíz:** El equipo ha priorizado el desarrollo técnico del producto sobre la gestión documental del SGSI.

**Criticidad:** ALTA

---

### Hallazgo H-10: Sin Bloqueo de Cuenta por Intentos Fallidos

**Problema detectado:** El rate limiting es por IP (`rl:login:{ip}`), no por cuenta. Un atacante con acceso a múltiples IPs (botnet, proxies) puede realizar fuerza bruta contra una cuenta específica sin límite.

**Control ISO 27002 afectado:** A.8.5 — Autenticación segura.

**Causa raíz:** Implementación simplificada de rate limiting que no contempla ataques distribuidos.

**Criticidad:** MEDIA

---

### Hallazgo H-11: Política de Contraseñas Insuficiente

**Problema detectado:** Solo se valida longitud mínima (8 caracteres). Sin requisitos de complejidad (mayúsculas, números, caracteres especiales) ni detección de contraseñas comunes.

**Control ISO 27002 afectado:** A.5.17 — Gestión de autenticación.

**Causa raíz:** Validación básica priorizando facilidad de uso sobre seguridad, sin implementar librería de análisis de fortaleza.

**Criticidad:** MEDIA

---

### Hallazgo H-12: Clave RSA Privada sin Passphrase

**Problema detectado:** En `security.py:46`, la clave RSA se genera con `serialization.NoEncryption()`. El archivo `keys/private.pem` queda sin cifrado adicional en el sistema de archivos.

**Control ISO 27002 afectado:** A.8.24 — Uso de criptografía.

**Criticidad:** MEDIA

---

### Hallazgo H-13: Audit Logs Modificables

**Problema detectado:** La tabla `audit_logs` en PostgreSQL no tiene restricciones de inmutabilidad (triggers, políticas). Un usuario con acceso de DBA puede alterar o eliminar registros de auditoría.

**Control ISO 27002 afectado:** A.8.15 — Registro de actividades; A.8.17 — Sincronización de relojes.

**Criticidad:** MEDIA

---

### Hallazgo H-14: Verificación de Email No Obligatoria en Login

**Problema detectado:** El campo `email_verified` existe en el modelo `User` y hay endpoint de verificación, pero `POST /auth/login` no evalúa este campo. Usuarios con emails falsos pueden operar normalmente.

**Control ISO 27002 afectado:** A.8.2 — Gestión de identidades.

**Criticidad:** MEDIA

---

### Hallazgo H-15: Generación de CV Síncrona — Riesgo DoS

**Problema detectado:** `GET /api/v1/cv/download/{worker_id}` ejecuta WeasyPrint sincrónicamente dentro del request HTTP. Múltiples peticiones simultáneas pueden saturar el servidor.

**Control ISO 27002 afectado:** A.8.6 — Gestión de la capacidad.

**Criticidad:** MEDIA

---

## MATRIZ DEL PLAN DE MEJORA

| N° | Hallazgo | Riesgo Asociado | Control ISO 27001/27002 Relacionado | Causa Raíz | Acción Correctiva | Acción Preventiva | Prioridad | Responsable | Recursos Necesarios | Plazo |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PII (DNI/nombre) en Redis sin cifrar (`auth.py:73-77`) | R-01 Exposición masiva de datos personales | ISO 27002 A.8.24 — Criptografía; A.8.10 — Eliminación de información | Diseño sin aplicar patrón de cifrado AES ya existente a caché Redis | Reemplazar `f"{body.full_name}\|{body.dni}"` por `encrypt_field(body.full_name) + encrypt_field(body.dni)` antes de `redis.setex()`. O eliminar PII de Redis y solicitarla en onboarding. | Agregar revisión de código obligatoria para cualquier `redis.setex()` que contenga datos de usuario. Documentar estándar: "ningún dato personal se almacena en caché sin cifrar". | **CRÍTICA** | Desarrollador Backend + Tech Lead | 4h de desarrollo, revisión de código | 1 semana |
| 2 | Auto-asignación de rol ADMIN en registro público (`schemas/auth.py:10`) | R-05 Escalada de privilegios | ISO 27002 A.8.2 — Gestión de identidades; A.8.3 — Gestión de accesos | Campo heredado de etapa de pruebas no eliminado | Eliminar campo `role` de `RegisterRequest` o forzar `role=UserRole.WORKER` siempre. Crear endpoint separado `/admin/users/{id}/role` protegido con ADMIN para asignar roles elevados. | Agregar test automatizado que verifique que el registro público no puede crear cuentas ADMIN. Documentar política: "asignación de roles elevados solo vía consola administrativa". | **CRÍTICA** | Desarrollador Backend | 2h de desarrollo, 1h de tests | 1 semana |
| 3 | Sin MFA para cuentas administrativas | R-03 Compromiso de cuentas admin | ISO 27002 A.8.5 — Autenticación segura | MFA no incluido en roadmap de Sprint actual | Implementar TOTP (RFC 6238) para roles ADMIN y MODERATOR usando librería `pyotp`. Flujo: activación opcional en primer login, obligatorio en segundo acceso. | Definir política de seguridad: "MFA obligatorio para todos los roles privilegiados". Incluir MFA en definición de "done" de cualquier endpoint administrativo futuro. | **CRÍTICA** | Desarrollador Backend + Diseñador UX | `pyotp` (lib Python), 3-5 días de desarrollo, QA | 4 semanas |
| 4 | Sistema de emails inoperativo (stub) | R-02 Recuperación de contraseña inoperativa | ISO 27002 A.8.5 — Autenticación segura; A.5.17 — Gestión de autenticación | Funcionalidad marcada stub Sprint 1, no completada en sprints posteriores | Implementar `send_reset_email()` real usando SendGrid API o SMTP (Postfix). Configurar variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`. Reemplazar stub en `notifications.py`. | Agregar test de integración que verifique envío de email en staging. Crear alerta de monitoreo si la cola `notifications` acumula tareas sin procesar por >5 min. | **CRÍTICA** | Desarrollador Backend + DevOps | Cuenta SendGrid (o SMTP propio), 2-3 días de desarrollo | 2 semanas |
| 5 | Sin backups de PostgreSQL ni Redis | R-07 Pérdida total de datos | ISO 27002 A.8.13 — Respaldo de información | Infraestructura diseñada para desarrollo sin configuración de producción | Configurar `pg_dump` diario automatizado con cron + envío cifrado a GCS bucket ya configurado (`intermediacion-laboral-dev`). Habilitar Redis AOF persistence. Probar restauración. | Definir política de backups: RPO=24h, RTO=4h. Implementar script de restauración documentado. Calendarizar drill semestral de recuperación. Alertar si backup falla. | **CRÍTICA** | DevOps / SysAdmin | Acceso GCS, scripts bash, 8h implementación | 2 semanas |
| 6 | Sin mecanismo ARCO ni cumplimiento Ley 29733 | R-14 Sanción regulatoria | ISO 27002 A.5.31 — Requisitos legales; ISO 27001 Cláusula 6.1 | Foco en funcionalidad sin integración del cumplimiento legal desde el diseño | Implementar: (a) modal de consentimiento informado en registro, (b) endpoint `DELETE /auth/me` para eliminación de cuenta y datos, (c) endpoint `GET /auth/me/export` para exportación de datos propios. Iniciar trámite de registro en ARCO (MINJUSDH). | Consultar asesoría legal especializada en Ley 29733. Documentar "Política de Privacidad" pública. Incluir cumplimiento ARCO en checklist de aceptación de nuevas funcionalidades. | **ALTA** | Desarrollador Backend + Área Legal DRTPE | Asesoría legal, 5-8 días de desarrollo | 6 semanas |
| 7 | Token de acceso con vida útil 24h | R-04 Ventana extendida ante robo de token | ISO 27002 A.8.5 — Autenticación segura | Sin refresh automático en frontend, compensado con token largo | Reducir `ACCESS_TOKEN_EXPIRE_MINUTES` a `30`. Implementar refresh automático en `api/client.ts` (interceptor Axios: ante 401, intentar refresh; si falla, logout). | Documentar estándar de tokens: access ≤ 30 min, refresh ≤ 7 días. Agregar test que verifique expiración y comportamiento del interceptor. | **ALTA** | Desarrollador Backend + Desarrollador Frontend | 4h backend, 8h frontend | 3 semanas |
| 8 | Header Content-Security-Policy ausente | R-12 XSS almacenado | ISO 27002 A.8.9 — Gestión de la configuración | Configuración parcial del middleware de seguridad | Agregar CSP en `SecurityHeadersMiddleware`: `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://localhost:8000`. Ajustar directivas según librerías usadas (Three.js, Framer Motion). | Documentar fuentes legítimas de contenido. Revisar CSP en cada sprint ante nuevas dependencias. Usar `Content-Security-Policy-Report-Only` primero para detectar violaciones sin bloquear. | **ALTA** | Desarrollador Backend + Desarrollador Frontend | 4-8h (prueba y ajuste de directivas CSP) | 2 semanas |
| 9 | Sin marco SGSI documentado | Riesgo de no certificación formal | ISO 27001 Cláusulas 4, 5, 6, 7, 9, 10 completas | Priorización del desarrollo técnico sobre la gestión documental | Elaborar documentos básicos del SGSI: (a) Alcance, (b) Política de Seguridad de la Información, (c) Registro de Riesgos, (d) Declaración de Aplicabilidad (SoA), (e) Objetivos de seguridad medibles. | Designar Responsable de Seguridad de la Información (RISI). Establecer revisión semestral del SGSI. Integrar análisis de riesgo en cada sprint de desarrollo. | **ALTA** | RISI + Dirección DRTPE | 3-5 días consultoría, plantillas SGSI | 8 semanas |
| 10 | Sin bloqueo de cuenta por intentos fallidos | R-11 Fuerza bruta distribuida | ISO 27002 A.8.5 — Autenticación segura | Rate limiting solo por IP, no contempla ataques distribuidos | Agregar contador Redis por cuenta: `rl:login:account:{email}`. Tras 5 fallos: bloqueo de 15 min. Registrar en `audit_logs action="login_failed"`. Notificar al usuario por email al desbloquearse. | Definir política: "5 intentos fallidos → bloqueo 15 min → notificación". Monitorear tasa de bloqueos con Grafana para detectar ataques en curso. | **MEDIA** | Desarrollador Backend | 4h de desarrollo, Redis | 4 semanas |
| 11 | Política de contraseñas sin complejidad | Sin riesgo directo pero vulnerabilidad facilitadora | ISO 27002 A.5.17 — Gestión de autenticación | Validación básica priorizando UX | Implementar validación: mínimo 8 chars, 1 mayúscula, 1 número, 1 carácter especial. Agregar `zxcvbn` para estimación de fortaleza con feedback visual en frontend. | Documentar política de contraseñas. Forzar cambio de contraseña para usuarios con contraseñas débiles existentes (campamento de migración). | **MEDIA** | Desarrollador Backend + Desarrollador Frontend | `zxcvbn` (lib JS), 4h backend, 4h frontend | 5 semanas |
| 12 | Clave RSA privada sin passphrase | R-06 Exfiltración de clave de firma JWT | ISO 27002 A.8.24 — Uso de criptografía | Generación con `NoEncryption()` por simplicidad de arranque | Regenerar claves RSA con passphrase almacenada en variable de entorno `RSA_PASSPHRASE`. Modificar `_load_private_key()` para usar la passphrase. Migrar a gestor de secretos (HashiCorp Vault o GCP Secret Manager) en producción. | Documentar procedimiento de rotación de claves (frecuencia anual). Agregar script de validación al CI que verifique que `private.pem` no esté commiteado. | **MEDIA** | DevOps + Desarrollador Backend | HashiCorp Vault (o similar), 1 día de trabajo | 6 semanas |
| 13 | Audit logs modificables por DBA | R-08 Alteración de evidencias de auditoría | ISO 27002 A.8.15 — Registro de actividades | Sin restricciones de inmutabilidad en la tabla `audit_logs` | Crear trigger PostgreSQL que rechace `UPDATE` y `DELETE` en `audit_logs`. Exportar logs diariamente a GCS en formato inmutable (WORM). Considerar firma de registros con HMAC-SHA256. | Definir política de retención de audit_logs: 2 años en BD, archivado GCS. Separar credenciales de BD: app usa usuario con permisos INSERT/SELECT solo en audit_logs. | **MEDIA** | DBA + Desarrollador Backend | 4h implementación trigger, 4h pipeline exportación | 6 semanas |
| 14 | Verificación de email no obligatoria en login | R-10 Registro con emails ajenos | ISO 27002 A.8.2 — Gestión de identidades | Deuda técnica: campo existe pero no se evalúa en login | Agregar verificación en `auth.py:login`: si `not user.email_verified → raise 401 con mensaje "Verifica tu email antes de continuar"`. Enviar email de verificación automáticamente en registro (requiere H-04 resuelto). | Monitorear porcentaje de usuarios con email verificado. Alertar si tasa de verificación cae. Agregar reenvío de verificación en dashboard del usuario. | **MEDIA** | Desarrollador Backend | Depende de H-04 (SMTP), 2h de desarrollo | Después de H-04 |
| 15 | Generación de CV síncrona — riesgo DoS | R-09 Degradación de disponibilidad | ISO 27002 A.8.6 — Gestión de la capacidad | Diseño síncrono aceptable en dev, no escalable en producción | Migrar `GET /cv/download` a servicio del resultado de la tarea Celery: la tarea guarda el PDF en GCS y el endpoint retorna la URL firmada. Aplicar rate limit de 1 solicitud de generación por usuario por minuto. | Agregar métrica Prometheus de tiempo de generación de PDF. Alertar si p95 > 10 segundos. | **MEDIA** | Desarrollador Backend + DevOps | Tarea Celery existente (`generate_cv_task`), GCS, 2 días | 8 semanas |

---

## INDICADORES DE SEGUIMIENTO (KPIs SMART)

### Indicadores de Corto Plazo (0-3 meses)

| Acción | Indicador | Fórmula | Meta | Frecuencia |
|---|---|---|---|---|
| H-01: Cifrado PII en Redis | % de datos en caché Redis que contienen PII en texto claro | (Claves Redis con PII plana / Total claves Redis) × 100 | **0%** (eliminación total) | Verificación semanal durante 1 mes post-implementación |
| H-02: Eliminación auto-ADMIN | % de usuarios con rol ADMIN creados vía endpoint público | (Usuarios ADMIN via /register / Total usuarios ADMIN) × 100 | **0%** | Revisión mensual de audit_logs |
| H-03: Implementación MFA | % de usuarios ADMIN con MFA activado | (Cuentas ADMIN con MFA / Total cuentas ADMIN) × 100 | **100% en 60 días** | Semanal durante implementación |
| H-04: SMTP funcional | % de emails de recuperación efectivamente entregados | (Emails entregados / Emails encolados) × 100 | **>95%** | Diario via monitoreo de cola Celery |
| H-05: Backups PostgreSQL | % de backups diarios exitosos | (Backups exitosos / Backups programados) × 100 × 30 días | **100%** | Diario — alerta automática si falla |
| H-05: Backups PostgreSQL | Tiempo de restauración probado (RTO real) | Tiempo medido en drill de recuperación | **< 4 horas** | Semestral (drill obligatorio) |
| H-08: CSP Header | Presencia de CSP en respuestas HTTP | Verificación automatizada en CI: `curl -I` + grep CSP | **Presente en 100% de respuestas** | Verificación en cada deploy |

### Indicadores de Mediano Plazo (3-6 meses)

| Acción | Indicador | Fórmula | Meta | Frecuencia |
|---|---|---|---|---|
| H-06: Cumplimiento ARCO | % de solicitudes ARCO atendidas en plazo (20 días hábiles, Ley 29733) | (Solicitudes atendidas a tiempo / Total solicitudes) × 100 | **100%** | Mensual |
| H-07: Token 30 minutos | Tiempo promedio de sesión activa sin reautenticación forzada | Promedio de duración de sesión en logs | **< 30 min access token** | Verificación en CI + monitoreo semanal |
| H-10: Bloqueo de cuenta | Número de ataques de fuerza bruta detectados y bloqueados | Conteo de `action="login_failed"` en audit_logs (agrupado por email, >5 en 1h) | **Tasa detectada > 80% de intentos anómalos** | Semanal via query a audit_logs |
| H-09: SGSI Documentado | % de documentos SGSI requeridos elaborados y aprobados | (Docs aprobados / Docs requeridos ISO 27001) × 100 | **80% al finalizar mediano plazo** | Mensual |
| H-11: Complejidad contraseña | % de contraseñas nuevas que cumplen política de complejidad | (Registros con contraseña válida / Total registros) × 100 | **100%** (validación en API) | Verificación continua (validator Pydantic) |
| General | Número de vulnerabilidades críticas abiertas | Conteo de hallazgos con prioridad Crítica sin cerrar | **0 críticos al mes 6** | Mensual |

### Indicadores de Largo Plazo (6-12 meses)

| Acción | Indicador | Fórmula | Meta | Frecuencia |
|---|---|---|---|---|
| Madurez SGSI | Nivel de madurez de seguridad (CMMI) | Evaluación por consultor externo | **Nivel 3 — Definido** | Semestral |
| Cobertura de audit_logs | % de acciones críticas registradas en audit_logs | (Acciones con log / Acciones críticas definidas) × 100 | **>95%** | Mensual |
| Disponibilidad del sistema | Uptime del servicio API | (Minutos disponibles / Minutos totales) × 100 | **>99.5%** | Continuo (Prometheus) |
| Cumplimiento ISO 27001 | % de controles del Anexo A implementados | (Controles implementados / Controles aplicables) × 100 | **>75%** | Trimestral |
| Tiempo de respuesta a incidentes | MTTR (Mean Time To Resolve) de incidentes de seguridad | Suma de tiempos de resolución / Número de incidentes | **< 4 horas para críticos** | Por incidente |
| Reducción de riesgos | % de riesgos altos mitigados o aceptados formalmente | (Riesgos tratados / Riesgos identificados nivel ALTO) × 100 | **100%** | Trimestral |
| Respaldos verificados | % de restauraciones exitosas en drill | (Restauraciones exitosas / Drills realizados) × 100 | **100%** | Semestral |

---

## PLAN DE IMPLEMENTACIÓN POR HORIZONTES

### CORTO PLAZO (0 – 3 meses) | Julio – Septiembre 2026
**Objetivo: Eliminar riesgos críticos y establecer controles de seguridad esenciales**

#### Semana 1-2 (Julio 2026): Acciones Urgentes de Código

**Sprint de Seguridad Crítica:**

```
Día 1-2:  [H-02] Bloquear auto-asignación de rol ADMIN en /register
           → Modificar RegisterRequest: eliminar campo role o forzar WORKER
           → Test automatizado de regresión
           → Deploy inmediato

Día 3-4:  [H-01] Cifrar PII en Redis
           → Modificar auth.py:73-77: aplicar encrypt_field() antes de setex()
           → O eliminar almacenamiento de PII en caché (recomendado)
           → Test unitario de cifrado/descifrado

Día 5:    [H-08] Agregar Content-Security-Policy
           → Actualizar SecurityHeadersMiddleware con CSP
           → Verificar en frontend con CSP-Report-Only primero
```

#### Semana 3-4 (Julio 2026): SMTP y Emails

```
Día 1-3:  [H-04] Implementar SMTP funcional
           → Elegir proveedor: SendGrid (recomendado para inicio rápido)
           → Configurar variables de entorno: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL
           → Implementar send_reset_email() real en notifications.py
           → Implementar send_verification_email()
           → Test de integración en staging

Día 4-5:  [H-14] Activar verificación de email en login
           → Modificar auth.py:login: verificar email_verified
           → Agregar endpoint de reenvío de verificación
           → Mensaje claro al usuario: "Verifica tu email para continuar"
```

#### Semana 5-6 (Agosto 2026): Backups e Infraestructura

```
Día 1-2:  [H-05] Script de backup PostgreSQL
           → Script pg_dump + compresión + cifrado GPG + upload GCS
           → Cron job diario a las 02:00 (America/Lima)
           → Script de verificación de integridad del backup
           → Test de restauración completa documentado

Día 3:    [H-05] Redis persistence
           → Habilitar Redis AOF (appendfsync everysec)
           → Verificar que docker-compose persiste volumen Redis
           → Script de backup RDB a GCS

Día 4-5:  Verificación y documentación
           → Runbook de restauración
           → Alerta Grafana si backup no ejecutado en 25h
```

#### Semana 7-12 (Agosto-Septiembre 2026): MFA y Mejoras de Autenticación

```
Semana 7-8: [H-03] Implementar TOTP/MFA
             → Instalar pyotp
             → Modelo MFAConfig en BD (secret, is_active, backup_codes)
             → Endpoints: /auth/mfa/setup, /auth/mfa/verify, /auth/mfa/disable
             → Obligatorio para ADMIN en segundo login
             → QR code para setup con libqrcode o similar

Semana 9:   [H-07] Reducir lifetime de access token
             → ACCESS_TOKEN_EXPIRE_MINUTES=30
             → Implementar refresh automático en api/client.ts (interceptor Axios)
             → Test E2E del flujo de refresh

Semana 10:  [H-10] Bloqueo de cuenta por intentos fallidos
             → Contador Redis: rl:login:account:{email}
             → Bloqueo 15 min tras 5 fallos
             → Registro en audit_logs: action="login_failed"
             → Email de alerta al usuario (requiere H-04 completado)

Semana 11-12: Pruebas de regresión + revisión de seguridad
              → Ejecutar SonarQube analysis
              → Corregir hotspot SONAR-2 (/tmp portfolio)
              → Revisión de código de seguridad por par
              → Documentar cambios implementados
```

---

### MEDIANO PLAZO (3 – 6 meses) | Octubre – Diciembre 2026
**Objetivo: Fortalecer controles, cumplimiento legal y procesos**

#### Octubre 2026: Cumplimiento Legal y SGSI Base

```
Semana 1-2: [H-06] Mecanismo ARCO
             → Endpoint DELETE /auth/me (eliminación de cuenta y datos)
             → Endpoint GET /auth/me/export (exportación datos propios JSON)
             → Modal de consentimiento en registro frontend
             → Enlace a Política de Privacidad en footer
             → Redacción Política de Privacidad (con asesoría legal)

Semana 3-4: [H-09] Documentos SGSI base
             → Documento: Alcance del SGSI
             → Documento: Política de Seguridad de la Información
             → Designación formal del RISI (Responsable de Seguridad)
             → Reunión de kick-off SGSI con dirección DRTPE
```

#### Noviembre 2026: Controles de Calidad y Gestión

```
Semana 1-2: [H-11] Política de contraseñas con complejidad
             → Backend: validación Pydantic con regex complejidad
             → Frontend: indicador visual de fortaleza (zxcvbn)
             → Script de migración: marcar usuarios con contraseñas débiles

Semana 3:   [H-12] Clave RSA con passphrase
             → Generar nueva clave RSA con passphrase vía env var RSA_PASSPHRASE
             → Modificar _load_private_key() para usar passphrase
             → Plan de rotación anual documentado
             → Evaluar migración a HashiCorp Vault

Semana 4:   [H-13] Audit logs inmutables
             → Trigger PostgreSQL: DENY UPDATE/DELETE en audit_logs
             → Pipeline de exportación diaria a GCS (JSON cifrado)
             → Credenciales de BD separadas: audit_user con INSERT/SELECT only
```

#### Diciembre 2026: Registro de Riesgos y Continuidad

```
Semana 1-2: [H-09] Registro formal de riesgos
             → Elaborar Risk Assessment completo (metodología MAGERIT adaptada)
             → Declaración de Aplicabilidad (SoA) con controles aplicables
             → Plan de tratamiento de riesgos documentado

Semana 3-4: Plan de Continuidad y DR
             → Definir RPO=24h, RTO=4h formalmente
             → Documentar DRP: escenarios, responsables, pasos
             → Primer drill de recuperación ante desastres
             → Runbook de incidentes de seguridad
```

---

### LARGO PLAZO (6 – 12 meses) | Enero – Junio 2027
**Objetivo: Mejoras estratégicas, optimización y preparación para certificación**

#### Enero-Febrero 2027: Capacidades Avanzadas

```
Enero:   [H-15] CV generation async
          → Migrar /cv/download a flujo async Celery + GCS
          → Endpoint retorna URL firmada del PDF en GCS
          → Rate limit: 1 generación/usuario/minuto
          → Prometheus: métrica de tiempo de generación

Febrero: Integración CI/CD de seguridad
          → Agregar Bandit al pipeline CI (análisis SAST Python)
          → npm audit en pipeline frontend
          → SonarQube en cada PR (gate de calidad)
          → DAST básico (OWASP ZAP en staging)
```

#### Marzo-Abril 2027: Gestión de Secretos y Monitoreo

```
Marzo:   Gestión centralizada de secretos
          → Implementar HashiCorp Vault o GCP Secret Manager
          → Migrar: AES_KEY, RSA_PASSPHRASE, SMTP_PASSWORD, DB_PASSWORD
          → Rotar secretos comprometidos
          → Documentar procedimiento de rotación

Abril:   Monitoreo y alertas de seguridad
          → Configurar alertas Grafana: tasa 401, tasa 429, errores 500
          → Dashboard de seguridad: intentos fallidos, accesos admin, CVs generados
          → Integración con canal de notificación (email/Slack DRTPE)
          → Proceso de gestión de incidentes de seguridad
```

#### Mayo-Junio 2027: Preparación para Certificación

```
Mayo:    Pre-auditoría interna
          → Evaluación completa contra todos los controles ISO 27001
          → Identificar brechas residuales
          → Plan de acción de brechas

Junio:   Auditoría externa de preparación
          → Contratar auditor externo certificado ISO 27001
          → Auditoría de certificación (si procede)
          → Revisión de la dirección (Management Review)
          → Cierre del primer ciclo PDCA del SGSI
```

---

## ANÁLISIS DE IMPACTO POR ACCIÓN

### Acciones Críticas

#### Acción 1: Cifrar PII en Redis (H-01)

| Dimensión | Análisis |
|---|---|
| **Beneficio esperado** | Eliminación de exposición de DNIs y nombres en texto claro. Consistencia con el modelo de seguridad AES-256-GCM ya implementado para PostgreSQL. |
| **Riesgo mitigado** | R-01 (exposición masiva PII): reducción de ALTO a BAJO-NULO |
| **Impacto en seguridad** | MUY ALTO — elimina la brecha más crítica del sistema |
| **Impacto operativo** | BAJO — la función `encrypt_field()` ya existe; cambio de 2-3 líneas de código |
| **Dificultad de implementación** | MUY BAJA — reutiliza infraestructura existente (AES-GCM) |

#### Acción 2: Bloquear Auto-ADMIN (H-02)

| Dimensión | Análisis |
|---|---|
| **Beneficio esperado** | Elimina vector de escalada de privilegios desde el registro público |
| **Riesgo mitigado** | R-05: escalada de privilegios, de ALTO a NULO |
| **Impacto en seguridad** | MUY ALTO — protege el activo más valioso (cuentas administrativas) |
| **Impacto operativo** | BAJO — requiere proceso alternativo de asignación de roles elevados |
| **Dificultad de implementación** | MUY BAJA — cambio de 1-2 líneas en schema |

#### Acción 3: MFA para Administradores (H-03)

| Dimensión | Análisis |
|---|---|
| **Beneficio esperado** | Las cuentas ADMIN son resistentes a credential stuffing y phishing incluso con contraseña comprometida |
| **Riesgo mitigado** | R-03: compromiso de cuentas, de ALTO a BAJO |
| **Impacto en seguridad** | MUY ALTO |
| **Impacto operativo** | MEDIO — requiere que administradores usen app de autenticación (Google Authenticator, Authy) |
| **Dificultad de implementación** | MEDIA — requiere nuevo modelo en BD, endpoints, UX de configuración |

#### Acción 4: SMTP Funcional (H-04)

| Dimensión | Análisis |
|---|---|
| **Beneficio esperado** | El sistema de recuperación de contraseñas y verificación de email es operativo. Usuarios pueden recuperar cuentas comprometidas. |
| **Riesgo mitigado** | R-02: inoperatividad de recuperación, de ALTO a BAJO |
| **Impacto en seguridad** | ALTO |
| **Impacto operativo** | ALTO POSITIVO — habilita funcionalidades que los usuarios esperan |
| **Dificultad de implementación** | BAJA — integración de API REST de SendGrid (bien documentada) |

#### Acción 5: Backups Automatizados (H-05)

| Dimensión | Análisis |
|---|---|
| **Beneficio esperado** | Continuidad del negocio garantizada. En caso de fallo catastrófico, pérdida máxima de 24 horas de datos. |
| **Riesgo mitigado** | R-07: pérdida total de datos, de ALTO a BAJO |
| **Impacto en seguridad** | ALTO — principio de disponibilidad garantizado |
| **Impacto operativo** | ALTO POSITIVO — reduce de 0% a ~95% la probabilidad de recuperación ante desastre |
| **Dificultad de implementación** | BAJA-MEDIA — scripts estándar de pg_dump + GCS |

---

## CRONOGRAMA GENERAL

| Actividad | Prioridad | Inicio | Fin | Responsable |
|---|---|---|---|---|
| **CORTO PLAZO** | | | | |
| Bloquear auto-asignación rol ADMIN | CRÍTICA | 2026-07-01 | 2026-07-03 | Dev Backend |
| Cifrar PII en Redis | CRÍTICA | 2026-07-03 | 2026-07-05 | Dev Backend |
| Agregar Content-Security-Policy | ALTA | 2026-07-06 | 2026-07-08 | Dev Backend |
| Implementar SMTP funcional (SendGrid) | CRÍTICA | 2026-07-08 | 2026-07-15 | Dev Backend |
| Activar verificación de email en login | MEDIA | 2026-07-15 | 2026-07-17 | Dev Backend |
| Script backup PostgreSQL + GCS | CRÍTICA | 2026-07-20 | 2026-07-25 | DevOps |
| Redis AOF persistence + backup | ALTA | 2026-07-25 | 2026-07-28 | DevOps |
| Test de restauración documentado | CRÍTICA | 2026-07-28 | 2026-07-30 | DevOps + Dev |
| Implementar MFA (TOTP) para ADMIN | CRÍTICA | 2026-08-03 | 2026-08-21 | Dev Backend |
| Reducir lifetime access token a 30 min | ALTA | 2026-08-21 | 2026-08-25 | Dev Backend + Frontend |
| Refresh automático en frontend | ALTA | 2026-08-25 | 2026-08-28 | Dev Frontend |
| Bloqueo de cuenta por intentos fallidos | MEDIA | 2026-09-01 | 2026-09-05 | Dev Backend |
| Corregir hotspot SONAR-2 (/tmp portfolio) | MEDIA | 2026-09-08 | 2026-09-10 | Dev Backend |
| Revisión de seguridad + SonarQube | — | 2026-09-15 | 2026-09-20 | Tech Lead |
| **MEDIANO PLAZO** | | | | |
| Endpoint ARCO: DELETE + GET/export | ALTA | 2026-10-01 | 2026-10-10 | Dev Backend |
| Modal de consentimiento + Política Privacidad | ALTA | 2026-10-01 | 2026-10-15 | Dev Frontend + Legal |
| Documentos SGSI base (alcance + política) | ALTA | 2026-10-15 | 2026-10-31 | RISI + Dirección |
| Registro de riesgos formal | ALTA | 2026-11-01 | 2026-11-15 | RISI + Consultora |
| Política de contraseñas con complejidad | MEDIA | 2026-11-01 | 2026-11-07 | Dev Backend + Frontend |
| Clave RSA con passphrase | MEDIA | 2026-11-10 | 2026-11-14 | Dev Backend + DevOps |
| Audit logs inmutables (trigger PostgreSQL) | MEDIA | 2026-11-17 | 2026-11-21 | DBA + Dev Backend |
| Pipeline exportación logs a GCS | MEDIA | 2026-11-21 | 2026-11-25 | DevOps |
| Declaración de Aplicabilidad (SoA) | ALTA | 2026-12-01 | 2026-12-15 | RISI + Consultora |
| Plan de Continuidad y DRP | ALTA | 2026-12-01 | 2026-12-20 | RISI + DevOps |
| Primer drill de recuperación ante desastres | ALTA | 2026-12-20 | 2026-12-22 | DevOps + Dev |
| **LARGO PLAZO** | | | | |
| CV generation async (Celery + GCS) | MEDIA | 2027-01-05 | 2027-01-20 | Dev Backend + DevOps |
| Bandit + npm audit en CI/CD | MEDIA | 2027-01-20 | 2027-02-05 | DevOps |
| HashiCorp Vault / Secret Manager | MEDIA | 2027-03-01 | 2027-03-31 | DevOps + Dev Backend |
| Dashboards de seguridad Grafana | MEDIA | 2027-04-01 | 2027-04-15 | DevOps |
| Alertas de seguridad configuradas | MEDIA | 2027-04-15 | 2027-04-30 | DevOps |
| Pre-auditoría interna ISO 27001 | ALTA | 2027-05-01 | 2027-05-15 | RISI + Consultora |
| Auditoría externa de preparación | ALTA | 2027-06-01 | 2027-06-15 | Auditor Externo |
| Revisión de la Dirección (Management Review) | ALTA | 2027-06-20 | 2027-06-23 | Dirección DRTPE |

---

## CONCLUSIÓN FINAL

### Nivel Actual de Madurez vs. Nivel Esperado

| Dimensión | Nivel Actual | Post Corto Plazo (3m) | Post Mediano Plazo (6m) | Post Largo Plazo (12m) |
|---|---|---|---|---|
| Controles técnicos | Nivel 2 | Nivel 3 | Nivel 3-4 | Nivel 4 |
| Documentación SGSI | Nivel 1 | Nivel 1-2 | Nivel 3 | Nivel 3-4 |
| Gestión de riesgos | Nivel 1 | Nivel 2 | Nivel 3 | Nivel 3-4 |
| Cumplimiento legal | Nivel 1 | Nivel 2 | Nivel 3 | Nivel 4 |
| Madurez global | **Nivel 2** | **Nivel 2-3** | **Nivel 3** | **Nivel 3-4** |
| Cumplimiento ISO 27001 | **35%** | **55%** | **70%** | **80%** |

### Controles Críticos que Deben Implementarse Primero

En orden absoluto de prioridad:

1. **Cifrar PII en Redis** — afecta a todos los usuarios que se registren; exposición activa
2. **Bloquear auto-ADMIN en registro** — vector de compromiso total del sistema disponible públicamente
3. **SMTP funcional** — sin esto, la recuperación de contraseñas es inoperativa y el sistema no es apto para producción
4. **Backups automatizados** — sin esto, cualquier incidente puede resultar en pérdida total e irrecuperable de datos
5. **MFA para administradores** — protege el acceso a todos los datos del sistema

### Recomendaciones para la Mejora Continua del SGSI

1. **Establecer ciclo PDCA mensual**: Planificar → Hacer → Verificar → Actuar. Revisión mensual de indicadores de seguridad con el equipo técnico.

2. **Designar y empoderar al RISI**: El Responsable de Seguridad de la Información debe tener autoridad para detener funcionalidades que introduzcan riesgos inaceptables, acceso directo a la dirección y presupuesto propio.

3. **Security by Design en cada sprint**: Toda nueva funcionalidad debe incluir análisis de seguridad en su definición de "done". Usar el modelo STRIDE para identificar amenazas en el diseño.

4. **Capacitación continua**: El equipo de desarrollo debe recibir formación anual en seguridad aplicada (OWASP, criptografía, gestión de secretos). Los usuarios administradores deben recibir formación en ingeniería social y phishing.

5. **Auditoría interna semestral**: Antes de cada ciclo de certificación, realizar auditoría interna completa contra la lista de verificación ISO 27001. Documentar hallazgos y seguimiento de acciones correctivas.

6. **Gestión de vulnerabilidades de dependencias**: Configurar `dependabot` (GitHub) o `renovate` para alertar sobre vulnerabilidades en dependencias Python y npm. Establecer SLA de parchado: crítico ≤ 7 días, alto ≤ 30 días.

7. **Pruebas de penetración anuales**: Contratar empresa externa para pentest anual del sistema en producción. Los hallazgos deben ingresar al registro de riesgos y tratarse con prioridad ALTA.

8. **Comunicación con los usuarios**: Dado el contexto de baja alfabetización digital de la población objetivo (trabajadores informales de Junín), el equipo debe diseñar mensajes claros sobre seguridad: qué datos se protegen, cómo recuperar acceso, qué hacer ante sospecha de compromiso.

9. **Revisión de la Dirección anual**: La Alta Dirección de DRTPE-Junín debe revisar formalmente el estado del SGSI al menos una vez al año, aprobando el presupuesto de seguridad y los objetivos del siguiente período.

10. **Preparar para certificación formal**: Con la implementación completa del plan, el sistema estará en condiciones de someterse a una auditoría de certificación ISO/IEC 27001 en el segundo semestre de 2027. Recomendamos un pre-audit externo en mayo 2027 para identificar brechas residuales antes de la certificación.

---

### Estimación de Reducción de Riesgos

| Riesgo | Nivel Actual | Nivel Post Plan Completo | Reducción |
|---|---|---|---|
| R-01 PII en Redis | ALTO | BAJO | -75% |
| R-02 Email stub | ALTO | BAJO | -80% |
| R-03 Sin MFA | ALTO | BAJO | -80% |
| R-04 Token 24h | MEDIO-ALTO | BAJO | -70% |
| R-05 Auto-ADMIN | ALTO | NULO | -100% |
| R-06 RSA sin passphrase | MEDIO | BAJO | -60% |
| R-07 Sin backups | ALTO | BAJO | -80% |
| R-08 Logs modificables | MEDIO | BAJO | -70% |
| R-09 CV síncrono | MEDIO | BAJO | -65% |
| R-10 Sin verif. email | MEDIO | BAJO | -70% |
| R-11 Sin bloqueo cuenta | MEDIO | BAJO | -70% |
| R-12 Sin CSP | MEDIO | BAJO | -75% |
| R-13 Tokens localStorage | MEDIO | BAJO | -60% |
| R-14 Sin ARCO | ALTO | BAJO | -80% |
| R-15 Sin backup Redis | MEDIO | BAJO | -75% |

**Reducción promedio estimada de riesgos: 74%**

---

*Plan de Mejora elaborado el 2026-06-23. Próxima revisión: 2026-09-23 (post implementación corto plazo).*
*Versión 1.0 — Sujeto a actualización conforme avance la implementación.*
