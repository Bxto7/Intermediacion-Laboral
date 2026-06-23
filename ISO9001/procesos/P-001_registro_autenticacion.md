# P-001 — Registro y Autenticación de Usuarios
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M01 — Identidad y Autenticación
**RF Cubiertos:** RF001–RF012
**RNF Cubiertos:** RNF001–RNF008
**Sprint de implementación:** Sprint 1 (base) + Sprint 2 (hardening seguridad)
**Componentes clave:** `backend/app/api/v1/auth.py`, `backend/app/core/security.py`

---

## 1. Propósito

Gestionar de forma segura el ciclo completo de identidad digital de los usuarios del sistema Linku (trabajadores, empleadores, administradores y moderadores), garantizando autenticación robusta, protección de credenciales y trazabilidad de accesos conforme a la Ley N° 29733.

---

## 2. Alcance

Cubre desde el registro inicial hasta el cierre de sesión, incluyendo recuperación de contraseña y verificación de email. Aplica a todos los roles: `WORKER`, `EMPLOYER`, `ADMIN`, `MODERATOR`.

---

## 3. Entradas del Proceso

| Entrada | Fuente | Formato |
|---------|--------|---------|
| Email del usuario | Formulario de registro/login | EmailStr (Pydantic v2) |
| Contraseña | Formulario de registro | str, mín. 8 chars, máx. 128 chars |
| Rol solicitado | Formulario de registro | `UserRole` enum: worker/employer/admin/moderator |
| Token de acceso (en solicitudes autenticadas) | Header `Authorization: Bearer <token>` | JWT RS256 |
| IP del cliente | Header `X-Forwarded-For` (prod) / `request.client.host` (dev) | string IPv4/IPv6 |

---

## 4. Salidas del Proceso

| Salida | Destino | Formato |
|--------|---------|---------|
| `access_token` | Frontend (localStorage) | JWT RS256, exp 24h, incluye sub/role/jti |
| `refresh_token` | Frontend (localStorage) | JWT RS256, exp 7 días |
| Registro en `users` | Base de datos PostgreSQL | UUID, email, hashed_password, role, is_active |
| Registro en `audit_logs` | BD (inmutable) | action=user_registered/user_login/user_logout |
| Evento structlog | Consola / Prometheus | JSON con event/user_id/ip/duration_ms |

---

## 5. Flujo del Proceso

### 5.1 Registro (RF001–RF003)
```
[Cliente] POST /api/v1/auth/register
    │
    ├─► Rate limit: 10 intentos/hora/IP (Redis INCR)
    ├─► Validar email único (409 si ya existe)
    ├─► Hashear contraseña: bcrypt cost 12
    ├─► Insertar en tabla `users`
    ├─► Generar access_token + refresh_token (RS256)
    ├─► Registrar en audit_logs (action="user_registered")
    └─► Retornar TokenResponse {access_token, refresh_token, token_type:"bearer"}
```

### 5.2 Login (RF004–RF006)
```
[Cliente] POST /api/v1/auth/login {email, password}
    │
    ├─► Rate limit: 20 intentos/hora/IP
    ├─► Buscar usuario por email
    ├─► verify_password(plain, hashed) → bcrypt
    ├─► [Si falla] 401 genérico (no revelar cuál campo es incorrecto)
    ├─► Generar tokens
    └─► Retornar TokenResponse
```

### 5.3 Refresh de token (RF007)
```
[Cliente] POST /api/v1/auth/refresh {refresh_token}
    │
    ├─► verify_token(refresh_token) → validar firma RS256
    ├─► Verificar type=="refresh" en payload
    ├─► Verificar JTI no en blacklist Redis
    ├─► Invalidar JTI del token viejo
    └─► Generar nuevo par de tokens
```

### 5.4 Logout (RF008)
```
[Cliente] POST /api/v1/auth/logout
    │
    ├─► Extraer JTI del access_token
    ├─► invalidate_token(jti, TTL=tiempo_restante_hasta_exp) en Redis
    ├─► [Si hay refresh_token en body] también invalidar su JTI
    ├─► Registrar en audit_logs (action="user_logout")
    └─► Retornar 200 "Sesión cerrada correctamente"
```

### 5.5 Recuperación de contraseña (RF010–RF012)
```
[Cliente] POST /api/v1/auth/forgot-password {email}
    │
    ├─► Rate limit: 5 intentos/hora/IP
    ├─► [Siempre] 200 con mensaje genérico (evitar enumeración de usuarios)
    ├─► [Si email existe] generar token UUID
    ├─► Guardar en Redis "pwd_reset:{token}" = user_id (TTL 3600s)
    └─► Encolar Celery send_reset_email (stub: solo log)

[Cliente] POST /api/v1/auth/reset-password {token, new_password}
    │
    ├─► Buscar "pwd_reset:{token}" en Redis
    ├─► Actualizar hashed_password en BD
    ├─► Eliminar token de Redis
    └─► Invalidar TODOS los tokens del usuario (blacklist:user:{user_id})
```

---

## 6. Controles de Calidad y Seguridad

| Control | Implementación | Estándar |
|---------|---------------|----------|
| Cifrado de contraseñas | bcrypt cost 12 (≈400ms por hash) | OWASP A02 |
| Tokens cortos de vida | access_token exp 24h; refresh 7 días | OWASP A07 |
| Firma asimétrica JWT | RS256 con par RSA auto-generado en `keys/` | RFC 7519 |
| Blacklist de tokens | Redis con TTL = tiempo restante del token | OWASP A07 |
| Rate limiting | Redis sliding window: 10/h registro, 20/h login, 5/h forgot | OWASP A04 |
| Sin revelación de campos | Mensaje 401 genérico en login/forgot-password | OWASP A01 |
| Audit log inmutable | Tabla `audit_logs` sin UPDATE/DELETE | ISO 27001 A.12.4 |
| Sin PII en logs | structlog nunca loguea contraseñas ni tokens completos | Ley 29733 |

---

## 7. Indicadores de Desempeño (KPIs del proceso)

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Tasa de éxito de registro | > 95% de intentos válidos | `audit_logs` action=user_registered |
| Tiempo promedio de login | < 500ms (incluye bcrypt) | Header `X-Process-Time` |
| Intentos bloqueados por rate limit | Monitorear anomalías > 100/h/IP | Redis keys `rl:login:*` |
| Tokens revocados por reset de contraseña | Trazabilidad completa | Redis keys `blacklist:user:*` |

---

## 8. Excepciones y Manejo de Errores

| Condición | HTTP Code | Respuesta |
|-----------|-----------|-----------|
| Email ya registrado | 409 | `{"detail": "El email ya está registrado"}` |
| Credenciales inválidas | 401 | `{"detail": "Credenciales inválidas"}` |
| Token expirado o inválido | 401 | `{"detail": "Token inválido o expirado"}` |
| Token en blacklist | 401 | `{"detail": "Token revocado"}` |
| Rate limit excedido | 429 | `{"detail": "Demasiadas solicitudes"}` + header `Retry-After` |
| Validación fallida (Pydantic) | 422 | Detalle del campo inválido |

---

## 9. Registros y Trazabilidad

- **`audit_logs`:** registro inmutable de todos los eventos de autenticación.
- **Redis blacklist:** revocación instantánea de tokens comprometidos.
- **structlog:** eventos JSON con `event`, `user_id`, `ip`, `duration_ms`.
- **Prometheus:** métrica `http_requests_total` con etiquetas `endpoint`/`status_code`.

---

## 10. Pruebas Automatizadas

Archivo: `backend/tests/integration/test_api_auth.py`
- `test_register_returns_tokens` — 200 con access/refresh token.
- `test_register_duplicate_email_returns_409`.
- `test_login_valid_credentials_returns_tokens`.
- `test_login_wrong_password_returns_401`.
- `test_refresh_returns_new_tokens`.
- `test_logout_returns_200`.
- `test_reset_password_invalidates_all_sessions`.

---

*P-001 | Linku DRTPE-Junín · Implementado Sprint 1–2 · RF001–RF012*
