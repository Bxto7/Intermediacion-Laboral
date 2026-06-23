# P-018 — Seguridad y Protección de Datos Personales (PII)
## Proceso Transversal | ISO 9001:2015 — Cláusula 8 / ISO 27001

**Sistema:** Linku — DRTPE-Junín
**Módulo:** Transversal — Seguridad
**RNF Cubiertos:** RNF001–RNF008
**Normativa:** Ley N° 29733 (Protección de Datos Personales, Perú)
**Sprint de implementación:** Sprint 1 (base) + Sprint 2 (hardening) + Sprint 4 (consent_records)
**Componentes clave:**
- `backend/app/core/security.py`
- `backend/app/core/rate_limit.py`
- `backend/app/core/consent.py`
- `backend/app/core/security_headers.py`

---

## 1. Propósito

Garantizar la confidencialidad, integridad y disponibilidad de los datos del sistema, con especial protección de la información de identificación personal (PII) de los trabajadores conforme a la Ley N° 29733 de Protección de Datos Personales del Perú.

---

## 2. Datos PII y Su Tratamiento

| Dato | Tabla | Columna | Tratamiento |
|------|-------|---------|-------------|
| Nombre completo (`full_name`) | workers | BYTEA | AES-256-GCM cifrado |
| DNI | workers | BYTEA | AES-256-GCM cifrado |
| Teléfono (`phone`) | workers | BYTEA | AES-256-GCM cifrado |
| RUC del empleador | employers | BYTEA | AES-256-GCM cifrado |
| Nombre de contacto del empleador | employers | BYTEA | AES-256-GCM cifrado |
| Ingreso mensual | economic_surveys | BYTEA | AES-256-GCM cifrado |
| Monto de contrato | contracts | BYTEA | AES-256-GCM cifrado |
| Email | users | VARCHAR | Texto plano (necesario para login) |
| IP del usuario | audit_logs, consent_records | VARCHAR | Texto plano (auditoría) |

**Regla absoluta:** Los datos en columnas BYTEA NUNCA se almacenan en texto plano ni se retornan en respuestas de la API.

---

## 3. Mecanismos de Seguridad

### 3.1 Cifrado de PII (AES-256-GCM)
```python
encrypt_field(value: str) -> bytes:
    key = base64.b64decode(settings.AES_KEY)    # 32 bytes exactos
    nonce = os.urandom(12)                        # nonce aleatorio por cifrado
    ciphertext = AESGCM(key).encrypt(nonce, value.encode(), None)
    return nonce + ciphertext                     # nonce incluido en el BYTEA

decrypt_field(value: bytes) -> str:
    nonce = value[:12]
    ciphertext = value[12:]
    return AESGCM(key).decrypt(nonce, ciphertext, None).decode()
```

El nonce aleatorio de 12 bytes garantiza que dos cifrados del mismo texto producen resultados diferentes (evita ataques de análisis por frecuencia).

### 3.2 Autenticación JWT RS256
```
- Clave privada RSA auto-generada en keys/private.pem (2048 bits)
- Clave pública RSA en keys/public.pem (verificación de firma)
- access_token: exp = 24 horas, incluye sub/role/jti
- refresh_token: exp = 7 días
- Blacklist por JTI en Redis (revocación inmediata)
- Blacklist por usuario post-reset (invalida TODOS sus tokens)
```

### 3.3 Hash de Contraseñas
```
bcrypt con cost factor 12 (~400ms por hash)
verify_password(plain, hashed) → bool
```

### 3.4 Rate Limiting (RNF007–RNF008)

| Endpoint / Alcance | Límite | Ventana | Clave Redis |
|--------------------|--------|---------|-------------|
| Registro | 10 req | 1 hora/IP | `rl:register:{ip}` |
| Login | 20 req | 1 hora/IP | `rl:login:{ip}` |
| Forgot-password | 5 req | 1 hora/IP | `rl:forgot:{ip}` |
| NLP (wizard/portfolio) | 60/30 req | 1 min/usuario | `rl:nlp:{user_id}` |
| Matching | 30 req | 1 min/usuario | `rl:match:{user_id}` |
| Global | 1000 req | 1 min/IP | `rl:global:{ip}` |

Implementación: `check_rate_limit()` con patrón sliding window Redis (INCR + EXPIRE). IP real desde `X-Forwarded-For` en producción.

### 3.5 Consentimiento Informado (Ley 29733)
```python
# En TODOS los endpoints que recolectan PII:
require_consent(consent_given=True, data_purpose="datos_economicos")
# Si consent_given=False → HTTP 400 con mención explícita de Ley 29733

# Registro en consent_records:
ConsentRecord(user_id, data_purpose, ip_address, consent_given=True, consent_version="1.0")
```

Propósitos registrados: `perfil`, `datos_economicos`, `portfolio`, `contrato_laboral`.

---

## 4. Principio de Mínimo Privilegio (RBAC)

| Rol | Acceso permitido |
|-----|-----------------|
| `WORKER` | Sus propios datos; feed público; matches de su perfil |
| `EMPLOYER` | Sus propias ofertas y postulaciones; datos básicos de candidatos (sin DNI) |
| `MODERATOR` | Cola de moderación; ban/unban de listings |
| `ADMIN` | Todo + panel DRTPE + métricas del modelo + eliminación de cuentas |

Implementación: `require_role(*roles)` como dependency FastAPI en todos los endpoints.

---

## 5. Audit Log Inmutable

La tabla `audit_logs` registra todos los eventos críticos:

| Campo | Contenido |
|-------|-----------|
| `action` | user_registered / user_login / user_logout / worker_profile_created / aes_key_rotated / account_deletion_requested |
| `user_id` | UUID del usuario (nullable para acciones anónimas) |
| `ip_address` | IP del cliente |
| `details` | JSONB con contexto adicional (sin PII en texto plano) |
| `created_at` | TIMESTAMPTZ |

**La tabla `audit_logs` NO tiene UPDATE ni DELETE** — es un registro inmutable de auditoría.

---

## 6. Headers de Seguridad

El middleware `SecurityHeadersMiddleware` añade en todas las respuestas:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

---

## 7. Resultado de Auditoría FURPS+ y OWASP

| Hallazgo | Severidad | Estado |
|---------|-----------|--------|
| RS256 con par RSA auto-generado | ✅ Fortaleza | Implementado Sprint 1 |
| AES-256-GCM con nonce aleatorio 12 bytes | ✅ Fortaleza | Implementado Sprint 1 |
| Blacklist JWT por JTI y por usuario | ✅ Fortaleza | Implementado Sprint 1–2 |
| Rate-limiting Redis sliding window | ✅ Fortaleza | Implementado Sprint 2 |
| consent_records auditable Ley 29733 | ✅ Fortaleza | Implementado Sprint 4 |
| SecurityHeadersMiddleware | ✅ Fortaleza | Implementado Sprint 1 |
| forgot-password sin enumeración de usuarios | ✅ Fortaleza | Implementado Sprint 1 |
| XSS en portafolio público (texto libre sin sanitización HTML) | ⚠️ Pendiente | Verificar autoescape Jinja2 |

---

## 8. Pruebas Automatizadas

Archivo: `backend/tests/unit/test_security.py`
- `test_hash_and_verify_password`
- `test_aes_encrypt_decrypt_roundtrip`
- `test_aes_different_plaintexts_produce_different_ciphers` (nonce aleatorio)
- `test_expired_token_raises_401`
- `test_reset_password_blocks_all_sessions`
- `test_rate_limit_blocks_after_threshold`

---

*P-018 | Linku DRTPE-Junín · Transversal Sprints 1–4 · RNF001–RNF008 · Ley 29733*
