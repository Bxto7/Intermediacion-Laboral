Eres el agente security-auditor. Lee el archivo CLAUDE.md en la raíz del repositorio antes de tocar cualquier archivo. Para todo el trabajo usa la herramienta Bash.

Revisa el código generado por python-pro en este sprint y cierra los 5 issues de seguridad identificados en el Sprint 1. Sigue exactamente las especificaciones del archivo sprint2_claude_code.md, Bloque 0.

ISSUE 1 — CRÍTICO: crea backend/scripts/rotate_aes_key.py y modifica app/core/security.py para que AES_KEY se lea en base64 y el validator de Settings verifique exactamente 32 bytes al decodificar.

ISSUE 2 — ALTO: corrige verify_token en app/core/security.py para que también consulte la clave "blacklist:user:{user_id}" en Redis y lance 401 si existe.

ISSUE 3 — ALTO: crea app/core/rate_limit.py con get_client_ip (lee X-Forwarded-For en production) y check_rate_limit (sliding window con Redis, lanza 429 con Retry-After). Reemplaza todos los rate limits hardcodeados en auth.py.

ISSUE 4 — MEDIO: agrega ForgotPasswordRequest, VerifyEmailRequest y ResetPasswordRequest en app/schemas/auth.py y actualiza los tres endpoints correspondientes en auth.py.

ISSUE 5 — MEDIO: agrega rate limit de 5 intentos por hora al endpoint POST /auth/forgot-password usando check_rate_limit con clave "rl:forgot:{ip}".

Además verifica en todo el código del sprint:
- Ningún campo DNI, teléfono ni nombre se expone en logs ni en respuestas del cliente.
- Todos los campos BYTEA sensibles usan encrypt_field antes de persistir.
- bcrypt cost factor es exactamente 12 (leer de settings.BCRYPT_COST).
- Ningún endpoint devuelve stack traces (el handler global de main.py los captura).
- grep -r "print(" app/ no devuelve resultados.
- Cumplimiento de Ley N°29733: consentimiento implícito en registro documentado en audit_logs.

Al terminar muéstrame la salida de:
pytest tests/unit/test_security.py -v
ruff check app/core/security.py app/core/rate_limit.py app/api/v1/auth.py app/schemas/auth.py
grep -r "print(" app/
