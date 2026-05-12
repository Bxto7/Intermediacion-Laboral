# SPRINT 4 — INSTRUCCIÓN 5 de 5
# Agente: `devops-engineer`
# Tarea: CI/CD GitHub Actions completo + GCS real (reemplaza stubs) + docker-compose.staging.yml

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
Las instrucciones 1–4 del Sprint 4 entregaron:
1. Seguridad hardened (rate limiting, AES, consent_records)
2. Panel admin DRTPE + KPIs + conector DRTPE stub
3. ML avanzado: DatasetBuilder + PSI drift + Celery ML
4. Frontend completo: Onboarding, Wizard, Dashboard, Portfolio, Admin

**Tu trabajo:** Pipeline CI/CD completo en GitHub Actions (lint → tests → build → staging → prod)
y reemplazar los stubs de almacenamiento GCS con la implementación real.

---

## PARTE A — GitHub Actions: Pipeline CI/CD completo

Crea `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ──────────────────────────────────────────────────────────────
  # JOB 1 — Backend: Lint
  # ──────────────────────────────────────────────────────────────
  lint-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ env.PYTHON_VERSION }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}
          restore-keys: ${{ runner.os }}-pip-

      - name: Install ruff
        run: pip install ruff

      - name: Lint backend
        working-directory: backend
        run: |
          ruff check . --output-format=github
          ruff format . --check

  # ──────────────────────────────────────────────────────────────
  # JOB 2 — Frontend: Lint + TypeScript check
  # ──────────────────────────────────────────────────────────────
  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node ${{ env.NODE_VERSION }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: TypeScript check
        working-directory: frontend
        run: npx tsc --noEmit

      - name: ESLint
        working-directory: frontend
        run: npm run lint

  # ──────────────────────────────────────────────────────────────
  # JOB 3 — Backend: Tests con cobertura
  # ──────────────────────────────────────────────────────────────
  test-backend:
    runs-on: ubuntu-latest
    needs: lint-backend

    services:
      postgres:
        image: pgvector/pgvector:pg15
        env:
          POSTGRES_DB: drtpe_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: testpassword
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DATABASE_URL: postgresql+asyncpg://postgres:testpassword@localhost:5432/drtpe_test
      REDIS_URL: redis://localhost:6379/1
      SECRET_KEY: test_secret_key_for_ci_only_32bytes
      FIELD_ENCRYPTION_KEY: 0000000000000000000000000000000000000000000000000000000000000000
      ENV: testing

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ env.PYTHON_VERSION }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}

      - name: Install dependencies
        working-directory: backend
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx

      - name: Run migrations
        working-directory: backend
        run: alembic upgrade head

      - name: Run tests
        working-directory: backend
        run: |
          pytest tests/ \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=xml:coverage.xml \
            --cov-fail-under=80 \
            -v \
            --tb=short

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml
          fail_ci_if_error: false

  # ──────────────────────────────────────────────────────────────
  # JOB 4 — Frontend: Tests
  # ──────────────────────────────────────────────────────────────
  test-frontend:
    runs-on: ubuntu-latest
    needs: lint-frontend
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node ${{ env.NODE_VERSION }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run tests
        working-directory: frontend
        run: npm run test -- --coverage --passWithNoTests

  # ──────────────────────────────────────────────────────────────
  # JOB 5 — Build Docker images
  # ──────────────────────────────────────────────────────────────
  build:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-backend:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-backend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-frontend:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-frontend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ──────────────────────────────────────────────────────────────
  # JOB 6 — Deploy a Staging (rama: develop)
  # ──────────────────────────────────────────────────────────────
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Run (staging)
        run: |
          gcloud run deploy drtpe-api-staging \
            --image ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-backend:${{ github.sha }} \
            --region us-central1 \
            --platform managed \
            --no-allow-unauthenticated \
            --set-env-vars ENV=staging \
            --set-secrets DATABASE_URL=drtpe-db-url:latest,SECRET_KEY=drtpe-secret:latest

  # ──────────────────────────────────────────────────────────────
  # JOB 7 — Deploy a Producción (rama: main, manual approval)
  # ──────────────────────────────────────────────────────────────
  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production    # Requiere aprobación manual en GitHub

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Run migrations in production
        run: |
          # Ejecutar migraciones vía Cloud Run Job (no inline en el deploy)
          gcloud run jobs execute drtpe-migrations \
            --region us-central1 \
            --wait

      - name: Deploy to Cloud Run (production)
        run: |
          gcloud run deploy drtpe-api \
            --image ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-backend:${{ github.sha }} \
            --region us-central1 \
            --platform managed \
            --allow-unauthenticated \
            --min-instances 1 \
            --max-instances 10 \
            --set-env-vars ENV=production \
            --set-secrets DATABASE_URL=drtpe-db-url:latest,SECRET_KEY=drtpe-secret:latest,FIELD_ENCRYPTION_KEY=drtpe-enc-key:latest

      - name: Health check post-deploy
        run: |
          sleep 30
          curl -f https://api.drtpe-junin.gob.pe/api/v1/health || exit 1
          echo "✅ Health check passed"
```

---

## PARTE B — OWASP ZAP en CI (DAST)

Agrega `.github/workflows/security.yml`:

```yaml
name: Security Scan (DAST)

on:
  schedule:
    - cron: '0 2 * * 1'  # Lunes 2am UTC
  workflow_dispatch:

jobs:
  zap-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run OWASP ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.12.0
        with:
          target: 'https://staging.drtpe-junin.gob.pe'
          rules_file_name: '.zap/rules.tsv'
          cmd_options: '-a'
```

---

## PARTE C — GCS real (reemplaza stubs de almacenamiento)

Actualiza `app/services/storage.py`:

```python
# app/services/storage.py
"""
Servicio de almacenamiento en Google Cloud Storage.
Sprint 4: implementación real (reemplaza stubs de Sprint 3).
URLs firmadas con expiración máx 60 minutos (regla de seguridad del CLAUDE.md).
"""
import datetime
from pathlib import Path
from google.cloud import storage
from google.oauth2 import service_account
import structlog

from app.core.config import settings

logger = structlog.get_logger()

MAX_URL_EXPIRATION_MINUTES = 60  # Regla de seguridad — URLs firmadas máx 60 min


def _get_storage_client() -> storage.Client:
    """Obtener cliente GCS autenticado."""
    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return storage.Client(credentials=credentials, project=settings.GCP_PROJECT_ID)
    # En Cloud Run: usar ADC (Application Default Credentials)
    return storage.Client()


def upload_file(
    content: bytes,
    destination_path: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Subir archivo a GCS y retornar la ruta (no la URL firmada).
    La URL firmada se genera por separado con expiración máx 60 min.
    
    destination_path: ej "portfolio/{worker_id}/foto.jpg"
    Retorna: "gs://bucket/portfolio/{worker_id}/foto.jpg"
    """
    client = _get_storage_client()
    bucket = client.bucket(settings.GCS_BUCKET)
    blob = bucket.blob(destination_path)
    blob.upload_from_string(content, content_type=content_type)
    
    gcs_uri = f"gs://{settings.GCS_BUCKET}/{destination_path}"
    logger.info(
        "file_uploaded_gcs",
        path=destination_path,
        size_bytes=len(content),
        content_type=content_type,
    )
    return gcs_uri


def generate_signed_url(
    gcs_path: str,
    expiration_minutes: int = 15,
) -> str:
    """
    Generar URL firmada para acceso temporal a un archivo en GCS.
    Expiración máxima: 60 minutos (regla del CLAUDE.md de seguridad).
    
    gcs_path: puede ser URI completo "gs://bucket/path" o solo "path"
    """
    # Aplicar límite de seguridad
    expiration_minutes = min(expiration_minutes, MAX_URL_EXPIRATION_MINUTES)
    
    # Parsear path
    if gcs_path.startswith("gs://"):
        parts = gcs_path[5:].split("/", 1)
        bucket_name, blob_path = parts[0], parts[1]
    else:
        bucket_name = settings.GCS_BUCKET
        blob_path = gcs_path

    client = _get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method="GET",
    )
    
    logger.info(
        "signed_url_generated",
        path=blob_path,
        expiration_minutes=expiration_minutes,
    )
    return url


def delete_file(gcs_path: str) -> bool:
    """Eliminar archivo de GCS (soft-delete via naming convention)."""
    try:
        if gcs_path.startswith("gs://"):
            parts = gcs_path[5:].split("/", 1)
            bucket_name, blob_path = parts[0], parts[1]
        else:
            bucket_name = settings.GCS_BUCKET
            blob_path = gcs_path

        client = _get_storage_client()
        # Mover a "deleted/" en lugar de eliminar (audit trail)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        deleted_path = f"deleted/{blob_path}"
        bucket.copy_blob(blob, bucket, deleted_path)
        blob.delete()
        
        logger.info("file_soft_deleted_gcs", path=blob_path, moved_to=deleted_path)
        return True
    except Exception as e:
        logger.error("file_delete_failed", path=gcs_path, error=str(e))
        return False


# Compatibilidad con código del Sprint 3 que usaba upload_to_gcs
def upload_to_gcs(
    content: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
    expiration_minutes: int = 15,
) -> str:
    """Wrapper para compatibilidad — sube y retorna URL firmada."""
    gcs_path = upload_file(content, filename, content_type)
    return generate_signed_url(gcs_path, expiration_minutes=expiration_minutes)
```

Actualizar `requirements.txt`:
```
google-cloud-storage>=2.10.0
google-auth>=2.20.0
```

---

## PARTE D — docker-compose.staging.yml

Crea `docker-compose.staging.yml`:

```yaml
version: "3.9"
# Configuración de staging: misma estructura que producción pero sin volumes persistentes externos

x-staging-common: &staging-common
  env_file: .env.staging
  restart: unless-stopped
  networks:
    - drtpe_staging

services:
  api:
    image: ghcr.io/${GITHUB_REPO}-backend:${IMAGE_TAG:-latest}
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
    <<: *staging-common
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker-embeddings:
    image: ghcr.io/${GITHUB_REPO}-backend:${IMAGE_TAG:-latest}
    command: celery -A app.core.celery_app worker --queues=embeddings --concurrency=1
    <<: *staging-common

  worker-notifications:
    image: ghcr.io/${GITHUB_REPO}-backend:${IMAGE_TAG:-latest}
    command: celery -A app.core.celery_app worker --queues=notifications,default --concurrency=2
    <<: *staging-common

  celery-beat:
    image: ghcr.io/${GITHUB_REPO}-backend:${IMAGE_TAG:-latest}
    command: celery -A app.core.celery_app beat --loglevel=info
    <<: *staging-common

  frontend:
    image: ghcr.io/${GITHUB_REPO}-frontend:${IMAGE_TAG:-latest}
    ports:
      - "3000:80"
    <<: *staging-common

networks:
  drtpe_staging:
    driver: bridge
```

---

## PARTE E — Prometheus alertas

Crea `infra/prometheus/alerts.yml`:

```yaml
groups:
  - name: drtpe_api_alerts
    rules:
      # API caída
      - alert: APIDown
        expr: up{job="drtpe-api"} == 0
        for: 2m
        annotations:
          summary: "API DRTPE caída"
          description: "El servicio API no responde hace más de 2 minutos."

      # Latencia alta
      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
        for: 5m
        annotations:
          summary: "Latencia alta en la API"
          description: "El percentil 95 de latencia supera los 2 segundos."

      # Tasa de errores alta
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Tasa de errores HTTP 5xx elevada"

      # F1 del modelo bajo
      - alert: ModelF1Low
        expr: drtpe_model_f1_score < 0.70
        for: 1h
        annotations:
          summary: "F1 del modelo ML por debajo del umbral de alerta (0.70)"
          description: "El modelo de matching necesita reentrenamiento."
```

---

## PARTE F — Secrets de GitHub Actions (documentar)

Crea `.github/SECRETS.md`:

```markdown
# Secrets requeridos en GitHub Actions

## Repository Secrets

| Secret | Descripción | Obtener de |
|--------|-------------|------------|
| `GCP_SA_KEY` | JSON de la Service Account de GCP | GCP Console → IAM → Service Accounts |
| `CODECOV_TOKEN` | Token de Codecov para cobertura | codecov.io |

## Environment Secrets (staging)

| Secret | Descripción |
|--------|-------------|
| `DATABASE_URL` | URL de conexión a Cloud SQL (staging) |
| `SECRET_KEY` | JWT secret key (staging) |
| `FIELD_ENCRYPTION_KEY` | Clave AES-256 para datos sensibles (staging) |

## Environment Secrets (production)

| Secret | Descripción |
|--------|-------------|
| `DATABASE_URL` | URL de conexión a Cloud SQL (producción) |
| `SECRET_KEY` | JWT secret key (producción — diferente a staging) |
| `FIELD_ENCRYPTION_KEY` | Clave AES-256 (producción — NUNCA igual a staging) |

## Cómo generar SECRET_KEY
```bash
openssl rand -hex 32
```

## Cómo generar FIELD_ENCRYPTION_KEY (32 bytes = 64 hex chars)
```bash
openssl rand -hex 32
```

## CRÍTICO: estas keys NUNCA deben ir al repositorio
- Verificar que .gitignore excluye .env, .env.*, *.pem, *.json en credentials/
```

---

## VERIFICACIONES FINALES

```bash
# Verificar que el pipeline CI se puede parsear
cat .github/workflows/ci.yml | python3 -c "import yaml, sys; yaml.safe_load(sys.stdin); print('✅ CI YAML válido')"

# Verificar que no hay secrets hardcodeados en el código
grep -rn "AIza\|sk-\|gcp_key\|GCS_KEY" backend/ frontend/ && echo "❌ SECRET HARDCODEADO" || echo "✅ Sin secrets hardcodeados"

# Verificar que google-cloud-storage está en requirements
grep "google-cloud-storage" backend/requirements.txt && echo "✅" || echo "❌ Falta en requirements"

# Buildear imágenes localmente para verificar
docker build -t drtpe-backend:test ./backend
docker build -t drtpe-frontend:test ./frontend
echo "✅ Builds OK"
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `.github/workflows/ci.yml` — pipeline CI/CD completo (7 jobs)
- `.github/workflows/security.yml` — OWASP ZAP semanal
- `.github/SECRETS.md` — documentación de secrets requeridos
- `app/services/storage.py` — GCS real (reemplaza stubs)
- `docker-compose.staging.yml` — configuración de staging
- `infra/prometheus/alerts.yml` — alertas Prometheus
- `requirements.txt` — google-cloud-storage, google-auth

---

**El Sprint 4 está completado. El Sprint 5 cierra el sistema con:
moderación de contenido, GCP Cloud Run real, documentación OpenAPI y tests finales E2E.**
