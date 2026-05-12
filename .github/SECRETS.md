# GitHub Actions — Secrets requeridos

## Repository Secrets (aplican a todos los environments)

| Secret | Descripción | Cómo obtener |
|--------|-------------|--------------|
| `GCP_SA_KEY` | JSON de la Service Account de GCP con permisos Cloud Run + GCS | GCP Console → IAM → Service Accounts → Crear clave JSON |
| `GCP_PROJECT_ID` | ID del proyecto GCP | GCP Console → Dashboard → Project ID |
| `CODECOV_TOKEN` | Token de Codecov para reporte de cobertura | codecov.io → Settings → Repository token |

## Environment Secrets — `staging`

| Secret | Descripción |
|--------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db_staging` |
| `REDIS_URL` | `redis://redis-host:6379/0` |
| `SECRET_KEY` | 32 bytes hex aleatorio (JWT signing) |
| `AES_KEY` | 32 bytes hex — cifra DNI, teléfono, ingresos |
| `JWT_PRIVATE_KEY` | Clave privada RS256 (PEM) |
| `JWT_PUBLIC_KEY` | Clave pública RS256 (PEM) |
| `GCS_BUCKET_NAME` | Nombre del bucket GCS de staging |
| `STAGING_URL` | URL pública del backend staging (para smoke test) |

## Environment Secrets — `production`

| Secret | Descripción |
|--------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db_prod` |
| `REDIS_URL` | `redis://redis-host:6379/0` |
| `SECRET_KEY` | **Diferente** al de staging — generar nuevo |
| `AES_KEY` | **Diferente** al de staging — **NUNCA reutilizar** |
| `JWT_PRIVATE_KEY` | Clave privada RS256 producción |
| `JWT_PUBLIC_KEY` | Clave pública RS256 producción |
| `GCS_BUCKET_NAME` | Nombre del bucket GCS de producción |
| `GCP_SA_KEY_PROD` | Service Account con permisos de producción |

## Cómo generar los secrets

```bash
# SECRET_KEY (32 bytes)
openssl rand -hex 32

# AES_KEY (32 bytes = 64 hex chars)
openssl rand -hex 32

# Par de claves JWT RS256
openssl genrsa -out jwt_private.pem 2048
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem
```

## CRÍTICO — Reglas de seguridad

- Los secrets **NUNCA** van al repositorio
- `.env`, `.env.*`, `*.pem`, `credentials.json` están en `.gitignore`
- La `AES_KEY` de staging y producción deben ser **distintas**
- Rotar las claves cada 6 meses (`scripts/rotate_aes_key.py`)
- El `FIELD_ENCRYPTION_KEY` del CI usa `0000...` (64 ceros) — **solo para tests**, nunca en real

## Verificar que no hay secrets hardcodeados

```bash
# Desde la raíz del repositorio
grep -rn "AIza\|sk-\|AKIA\|gcp_key\|password.*=.*[a-zA-Z0-9]{20}" \
  backend/ frontend/ --include="*.py" --include="*.ts" --include="*.tsx" \
  && echo "❌ Posible secret hardcodeado" || echo "✅ Sin secrets hardcodeados"
```
