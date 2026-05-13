# SPRINT 5 — INSTRUCCIÓN 4 de 6
# Agente: `devops-engineer`
# Tarea: GCP Cloud Run deploy real + Cloud SQL + Redis Terraform + backups automáticos + Runbook

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
El CI/CD de GitHub Actions ya fue implementado en Sprint 4. Esta instrucción configura la
infraestructura real de producción en GCP usando Terraform.

---

## PARTE A — Terraform: Infraestructura GCP completa

Crea `infra/terraform/`:

```hcl
# infra/terraform/main.tf
terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  # Estado remoto en GCS
  backend "gcs" {
    bucket = "drtpe-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── Variables ────────────────────────────────────────────────────────
variable "project_id" { type = string }
variable "region"     { type = string  default = "us-central1" }
variable "env"        { type = string  default = "production" }

# ─── Cloud SQL — PostgreSQL 15 con pgvector ────────────────────────────
resource "google_sql_database_instance" "drtpe_postgres" {
  name             = "drtpe-postgres-${var.env}"
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = true

  settings {
    tier              = "db-custom-2-4096"  # 2 vCPU, 4 GB RAM
    availability_type = "REGIONAL"          # Alta disponibilidad

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"  # 3am Lima (8am UTC)
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30  # 30 días de backups
        retention_unit   = "COUNT"
      }
    }

    maintenance_window {
      day          = 7   # Domingo
      hour         = 3   # 3am UTC
      update_track = "stable"
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.drtpe_vpc.id
    }
  }
}

resource "google_sql_database" "drtpe_db" {
  name     = "drtpe"
  instance = google_sql_database_instance.drtpe_postgres.name
}

resource "google_sql_user" "drtpe_user" {
  name     = "drtpe_app"
  instance = google_sql_database_instance.drtpe_postgres.name
  password = var.db_password
}

# ─── Redis (Cloud Memorystore) ─────────────────────────────────────────
resource "google_redis_instance" "drtpe_redis" {
  name           = "drtpe-redis-${var.env}"
  tier           = "STANDARD_HA"    # Alta disponibilidad
  memory_size_gb = 2
  region         = var.region

  authorized_network = google_compute_network.drtpe_vpc.id

  redis_configs = {
    "maxmemory-policy" = "allkeys-lru"
  }
}

# ─── VPC privada ──────────────────────────────────────────────────────
resource "google_compute_network" "drtpe_vpc" {
  name                    = "drtpe-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "drtpe_subnet" {
  name          = "drtpe-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.drtpe_vpc.id
}

# ─── Cloud Run — API Backend ────────────────────────────────────────────
resource "google_cloud_run_v2_service" "drtpe_api" {
  name     = "drtpe-api"
  location = var.region

  template {
    containers {
      image = "ghcr.io/${var.github_repo}-backend:${var.image_tag}"

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        cpu_idle = false  # CPU activa siempre (no cold-start)
      }

      env {
        name  = "ENV"
        value = "production"
      }
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_url.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "FIELD_ENCRYPTION_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.enc_key.secret_id
            version = "latest"
          }
        }
      }

      # Liveness probe
      liveness_probe {
        http_get {
          path = "/api/v1/health"
          port = 8000
        }
        initial_delay_seconds = 30
        period_seconds        = 30
        failure_threshold     = 3
        timeout_seconds       = 10
      }

      # Readiness probe (startup)
      startup_probe {
        http_get {
          path = "/api/v1/health"
          port = 8000
        }
        initial_delay_seconds = 10
        period_seconds        = 10
        failure_threshold     = 10
        timeout_seconds       = 5
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    vpc_access {
      network_interfaces {
        network    = google_compute_network.drtpe_vpc.name
        subnetwork = google_compute_subnetwork.drtpe_subnet.name
      }
      egress = "ALL_TRAFFIC"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# ─── Cloud Run — Frontend ───────────────────────────────────────────────
resource "google_cloud_run_v2_service" "drtpe_frontend" {
  name     = "drtpe-frontend"
  location = var.region

  template {
    containers {
      image = "ghcr.io/${var.github_repo}-frontend:${var.image_tag}"
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
    }
    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }
  }
}

# ─── GCS Bucket ────────────────────────────────────────────────────────
resource "google_storage_bucket" "drtpe_media" {
  name          = "drtpe-junin-media-${var.env}"
  location      = "US-CENTRAL1"
  force_destroy = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action { type = "Delete" }
    condition {
      num_newer_versions = 3
      with_state         = "ARCHIVED"
    }
  }

  # Mover archivos "deleted/" a almacenamiento más barato después de 90 días
  lifecycle_rule {
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      days_since_noncurrent_time = 90
      matches_prefix             = ["deleted/"]
    }
  }

  uniform_bucket_level_access = true
}

# ─── Secret Manager ────────────────────────────────────────────────────
resource "google_secret_manager_secret" "db_url" {
  secret_id = "drtpe-db-url"
  replication { auto {} }
}

resource "google_secret_manager_secret" "secret_key" {
  secret_id = "drtpe-secret"
  replication { auto {} }
}

resource "google_secret_manager_secret" "enc_key" {
  secret_id = "drtpe-enc-key"
  replication { auto {} }
}

# ─── Outputs ────────────────────────────────────────────────────────────
output "api_url" {
  value = google_cloud_run_v2_service.drtpe_api.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.drtpe_frontend.uri
}

output "db_connection_name" {
  value = google_sql_database_instance.drtpe_postgres.connection_name
}
```

```hcl
# infra/terraform/variables.tf
variable "db_password"  { type = string  sensitive = true }
variable "github_repo"  { type = string  default = "rojas-tovar/drtpe-sistema" }
variable "image_tag"    { type = string  default = "latest" }
```

```hcl
# infra/terraform/terraform.tfvars.example
project_id  = "drtpe-junin-2026"
region      = "us-central1"
env         = "production"
github_repo = "tu-usuario/drtpe-sistema"
image_tag   = "latest"
# db_password: NO incluir aquí — usar secret manager o -var al aplicar
```

---

## PARTE B — Cloud Run Jobs: Migraciones y tareas Celery

```hcl
# infra/terraform/cloud_run_jobs.tf

# Job de migraciones — ejecutar antes de cada deploy
resource "google_cloud_run_v2_job" "drtpe_migrations" {
  name     = "drtpe-migrations"
  location = var.region

  template {
    template {
      containers {
        image   = "ghcr.io/${var.github_repo}-backend:${var.image_tag}"
        command = ["alembic"]
        args    = ["upgrade", "head"]

        env {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_url.secret_id
              version = "latest"
            }
          }
        }
      }
      max_retries = 3
    }
  }
}

# Job de seed inicial (solo una vez)
resource "google_cloud_run_v2_job" "drtpe_seed" {
  name     = "drtpe-seed-research"
  location = var.region

  template {
    template {
      containers {
        image   = "ghcr.io/${var.github_repo}-backend:${var.image_tag}"
        command = ["python"]
        args    = ["-m", "app.utils.seed_research"]
      }
    }
    task_count  = 1
    parallelism = 1
  }
}
```

---

## PARTE C — Backups automáticos GCS

Crea `infra/scripts/backup_db.sh`:

```bash
#!/bin/bash
# backup_db.sh — Backup manual de PostgreSQL a GCS
# Cloud SQL ya hace backups automáticos (configurado en Terraform)
# Este script es para backups adicionales de emergencia

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID}"
INSTANCE="${CLOUD_SQL_INSTANCE}"
DB_NAME="drtpe"
BUCKET="${GCS_BUCKET}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/manual/${TIMESTAMP}_${DB_NAME}.sql.gz"

echo "🔄 Iniciando backup de ${DB_NAME} → gs://${BUCKET}/${BACKUP_FILE}"

# Exportar desde Cloud SQL a GCS directamente
gcloud sql export sql "${INSTANCE}" \
  "gs://${BUCKET}/${BACKUP_FILE}" \
  --database="${DB_NAME}" \
  --project="${PROJECT_ID}"

echo "✅ Backup completado: gs://${BUCKET}/${BACKUP_FILE}"

# Listar backups recientes
gsutil ls -l "gs://${BUCKET}/backups/manual/" | sort -k2 | tail -5
```

Crea `infra/scripts/restore_db.sh`:

```bash
#!/bin/bash
# restore_db.sh — Restaurar backup específico
# USO: ./restore_db.sh gs://bucket/backups/manual/20260501_030000_drtpe.sql.gz

set -euo pipefail

BACKUP_URI="${1}"
INSTANCE="${CLOUD_SQL_INSTANCE}"

if [ -z "${BACKUP_URI}" ]; then
  echo "❌ Uso: $0 gs://bucket/path/to/backup.sql.gz"
  exit 1
fi

echo "⚠️  RESTAURAR: ${BACKUP_URI} → ${INSTANCE}"
echo "⚠️  Esto sobreescribirá la base de datos. ¿Confirmas? (escribir CONFIRMAR):"
read -r confirm
if [ "${confirm}" != "CONFIRMAR" ]; then
  echo "Cancelado."
  exit 0
fi

gcloud sql import sql "${INSTANCE}" "${BACKUP_URI}" \
  --database=drtpe \
  --quiet

echo "✅ Restauración completada"
```

---

## PARTE D — Health y Readiness Probes en FastAPI

Actualiza `app/api/v1/health.py` con probes diferenciados:

```python
# app/api/v1/health.py — versión completa
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.db import get_db, get_redis

router = APIRouter(tags=["health"])


@router.get("/api/v1/health")
async def liveness_check():
    """
    Liveness probe: verifica que el proceso está vivo.
    No verifica dependencias externas (BD, Redis) — eso es del readiness.
    Cloud Run usa este endpoint para reiniciar instancias caídas.
    """
    return {"status": "ok", "service": "drtpe-api"}


@router.get("/api/v1/ready")
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Readiness probe: verifica que el servicio puede atender tráfico.
    Verifica BD y Redis. Si falla, Cloud Run no enruta tráfico a esta instancia.
    """
    checks = {}

    # Verificar PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {type(e).__name__}"

    # Verificar Redis
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {type(e).__name__}"

    # Verificar extensión pgvector
    try:
        await db.execute(text("SELECT '[1,2,3]'::vector(3)"))
        checks["pgvector"] = "ok"
    except Exception:
        checks["pgvector"] = "not available"

    all_ok = all(v == "ok" for v in checks.values())

    if not all_ok:
        response.status_code = 503

    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": checks,
    }
```

---

## PARTE E — Runbook de operaciones

Crea `RUNBOOK.md`:

```markdown
# RUNBOOK — Sistema de Intermediación Laboral DRTPE-Junín

## Información del sistema

| Componente | Tecnología | URL |
|------------|------------|-----|
| API Backend | Cloud Run (FastAPI) | https://api.drtpe-junin.gob.pe |
| Frontend | Cloud Run (React) | https://drtpe-junin.gob.pe |
| Base de datos | Cloud SQL PostgreSQL 15 | Privada VPC |
| Redis | Cloud Memorystore | Privada VPC |
| Almacenamiento | GCS | drtpe-junin-media-production |
| Monitoreo | Prometheus + Grafana | https://grafana.drtpe-junin.gob.pe |
| CI/CD | GitHub Actions | GitHub → Cloud Run |

## Comandos de diagnóstico rápido

```bash
# Estado de todos los servicios Cloud Run
gcloud run services list --region us-central1

# Logs del API (últimas 100 líneas)
gcloud run services logs read drtpe-api --region us-central1 --limit 100

# Health check
curl https://api.drtpe-junin.gob.pe/api/v1/health
curl https://api.drtpe-junin.gob.pe/api/v1/ready

# Estado de Cloud SQL
gcloud sql instances describe drtpe-postgres-production

# Estado de Redis
gcloud redis instances describe drtpe-redis-production --region us-central1
```

## Procedimientos de incidente

### API Caída (alerta: APIDown en Prometheus)

1. Verificar logs: `gcloud run services logs read drtpe-api --region us-central1 --limit 50`
2. Verificar health check: `curl https://api.drtpe-junin.gob.pe/api/v1/ready`
3. Si BD no responde → ver sección "Cloud SQL caído"
4. Si Redis no responde → ver sección "Redis caído"
5. Forzar re-deploy de la última imagen estable:
   ```bash
   gcloud run deploy drtpe-api \
     --image ghcr.io/repo-backend:COMMIT_SHA_ESTABLE \
     --region us-central1
   ```

### Cloud SQL caído

1. Verificar estado: `gcloud sql instances describe drtpe-postgres-production`
2. Si está en mantenimiento → esperar (mantenimiento programado domingos 3am UTC)
3. Para failover manual: `gcloud sql instances failover drtpe-postgres-production`
4. Verificar backup más reciente: `gcloud sql backups list --instance drtpe-postgres-production`

### Redis caído

1. Cloud Memorystore STANDARD_HA hace failover automático (< 1 minuto)
2. Si el failover no ocurrió: contactar soporte GCP
3. La caché perderá datos tras el failover — los workers Celery se reconectarán automáticamente

### F1 del modelo bajo (alerta: ModelF1Low en Prometheus)

1. Verificar métricas: `GET /api/v1/admin/model/metrics` (requiere token ADMIN)
2. Verificar drift: `GET /api/v1/admin/model/drift`
3. Reentrenar manualmente si PSI > 0.25:
   ```bash
   # Via Cloud Run Job
   gcloud run jobs execute drtpe-retraining \
     --args="--worker-type=all" \
     --region us-central1 --wait
   ```
4. Si el modelo nuevo supera F1 ≥ 0.75 → se despliega automáticamente

### Restaurar backup de BD

1. Listar backups disponibles:
   ```bash
   gcloud sql backups list --instance drtpe-postgres-production
   ```
2. Restaurar a un punto en el tiempo (PITR):
   ```bash
   gcloud sql instances restore-backup drtpe-postgres-production \
     --backup-instance drtpe-postgres-production \
     --backup-id BACKUP_ID
   ```
3. Notificar al equipo investigador (Rojas Peña W. / Tovar Sanchez C.)

## Monitoreo y alertas

- **Grafana**: https://grafana.drtpe-junin.gob.pe (usuario: admin)
- **Alertas activas**: ver `infra/prometheus/alerts.yml`
- **Rotación de alertas**: configurar en alertmanager con email del equipo

## Escalado manual

```bash
# Aumentar instancias mínimas del API (ante aumento de demanda)
gcloud run services update drtpe-api \
  --min-instances 3 \
  --region us-central1

# Verificar uso de Cloud SQL
gcloud sql instances describe drtpe-postgres-production \
  --format="json" | jq '.settings.tier'
```

## Contactos de emergencia

| Rol | Nombre | Contacto |
|-----|--------|---------|
| Investigador Principal | Rojas Peña, William Mikeiel | [completar] |
| Investigador | Tovar Sanchez, Carlos Alberto | [completar] |
| DRTPE-Junín | Responsable TI | [completar] |
| GCP Support | Soporte técnico | console.cloud.google.com/support |
```

---

## PARTE F — Verificaciones de infraestructura

```bash
# Verificar que Terraform es válido
cd infra/terraform
terraform init
terraform validate
terraform plan -var="project_id=drtpe-junin-2026" -var="db_password=PLACEHOLDER"

# Verificar que los scripts de backup son ejecutables
chmod +x infra/scripts/backup_db.sh infra/scripts/restore_db.sh

# Verificar health probes funcionan localmente
docker-compose up -d
sleep 15
curl -f http://localhost:8000/api/v1/health && echo "✅ Liveness OK"
curl -f http://localhost:8000/api/v1/ready  && echo "✅ Readiness OK"
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `infra/terraform/main.tf` — Cloud Run + Cloud SQL + Redis + GCS + Secret Manager
- `infra/terraform/variables.tf`
- `infra/terraform/cloud_run_jobs.tf` — Jobs de migraciones + seed
- `infra/terraform/terraform.tfvars.example`
- `infra/scripts/backup_db.sh`
- `infra/scripts/restore_db.sh`
- `app/api/v1/health.py` — liveness + readiness probes
- `RUNBOOK.md`

---

**Cuando termines, el agente `api-documenter` recibirá la instrucción 5
para documentar todos los endpoints con OpenAPI, generar la colección Postman y los diagramas Mermaid.**
