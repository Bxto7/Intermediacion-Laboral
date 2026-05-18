# Plan de Despliegue a Producción — Linku

**Proyecto:** Sistema de Intermediación Laboral ML/NLP — DRTPE-Junín
**Versión del plan:** 2.1 (Tier 2 — producción ajustada)
**Presupuesto objetivo:** ~$140 USD/mes (con margen para picos hasta $160)
**Proveedor cloud:** Google Cloud Platform (GCP) + Firebase Hosting + Cloudflare (DNS/WAF gratis)
**Última actualización:** 2026-05-18

---

## 0. Resumen ejecutivo

Linku se despliega bajo un modelo **híbrido optimizado**: serverless para el tráfico HTTP/WebSocket, una VM dedicada para los workers ML, y servicios gestionados para los datos. El plan prioriza **rendimiento estable y observabilidad** sin gastar de más mientras el tráfico se mantiene en el orden de cientos de usuarios/día. El presupuesto se ubica en **~$140/mes con margen real de ±$20** y un camino de escalado claro a Tier 1 (~$230/mes) si el tráfico lo justifica (ver sección 15).

### Trade-offs aceptados en Tier 2

- **WAF**: Cloud Armor reemplazado por Cloudflare gratis (CDN + DDoS L3/L4 + WAF básico). Mitigación suficiente para tráfico institucional.
- **DB**: tier de Cloud SQL reducido a 1 vCPU / 3.75 GiB. Adecuado para decenas de miles de filas con pgvector + HNSW. Escalado vertical en ~5 minutos cuando duela.
- **Compromiso anual**: GCE workers contratados con **Committed Use Discount (CUD) 1 año** para bajar 40% el costo.
- **Logging**: retención 7 días + sampling 30% de INFO. Errores siempre 100%, sink a BigQuery para histórico.

### Objetivos de nivel de servicio (SLOs)

| SLI | Target | Medición |
|-----|--------|----------|
| Disponibilidad API (`/api/v1/*`) | 99.5% mensual | Uptime check cada 60s desde 3 regiones |
| Latencia p95 endpoints síncronos | < 400 ms | Cloud Monitoring + middleware `X-Process-Time` |
| Latencia p95 endpoints NLP (cuando son síncronos) | < 1500 ms | Métrica custom por endpoint |
| Tiempo de procesamiento de embeddings (worker) | p95 < 8 s | Celery task duration |
| Error rate 5xx | < 0.5% | Logs estructurados con `level=error` |
| Disponibilidad WebSocket notificaciones | 99.0% mensual | Healthcheck WS cada 30s |
| RPO (Recovery Point Objective) | 5 minutos | PITR de Cloud SQL |
| RTO (Recovery Time Objective) | 1 hora | Runbook validado mensualmente |

---

## 1. Arquitectura objetivo

### 1.1. Diagrama lógico

```
                        ┌─────────────────────────────────────┐
                        │           Internet                  │
                        └──────────────┬──────────────────────┘
                                       │ HTTPS
                ┌──────────────────────┴──────────────────────┐
                │                                             │
                ▼                                             ▼
       ┌────────────────┐                          ┌─────────────────────┐
       │ Firebase       │                          │ Cloudflare (free)   │
       │ Hosting        │                          │ DNS + CDN + WAF     │
       │ React SPA + CDN│                          │ + DDoS L3/L4        │
       └────────────────┘                          └──────────┬──────────┘
                                                              │ Cloudflare
                                                              │ → Cloud Run
                                                              ▼
                                                  ┌──────────────────────┐
                                                  │ Cloud Run (FastAPI)  │
                                                  │ min=1, max=10        │
                                                  │ 1 vCPU, 1 GiB        │
                                                  │ cpu_always_allocated │
                                                  │ + Startup CPU boost  │
                                                  └──────────┬───────────┘
                                                             │ Serverless VPC
                                                             │ Access Connector
                          ┌──────────────────────────────────┼──────────────────────────────┐
                          │                                  │                              │
                          ▼                                  ▼                              ▼
                ┌──────────────────┐              ┌────────────────────┐         ┌──────────────────────┐
                │ Cloud SQL        │              │ GCE VM (CUD 1 año) │         │ Cloud Storage (GCS)  │
                │ PostgreSQL 15    │              │ e2-standard-2      │         │ - CVs PDF            │
                │ + pgvector       │◄────────────►│ 2 vCPU / 8 GiB     │◄───────►│ - Fotos portfolio    │
                │ db-custom-1-3840 │              │                    │         │ - Signed URLs        │
                │ Zonal + PITR     │              │ Docker compose:    │         └──────────────────────┘
                └──────────────────┘              │  - celery workers  │
                                                  │  - redis 7 (AOF)   │
                                                  │  - prometheus      │
                                                  │  - flower (interno)│
                                                  └────────────────────┘
                                                             │
                                                             │ scrape
                                                             ▼
                                                  ┌──────────────────────┐
                                                  │ Cloud Monitoring     │
                                                  │ + Cloud Logging      │
                                                  │ + Alertas → Slack    │
                                                  └──────────────────────┘
```

### 1.2. Decisiones de arquitectura clave (ADRs comprimidos)

| # | Decisión | Por qué | Trade-off aceptado |
|---|----------|---------|--------------------|
| ADR-01 | Frontend en **Firebase Hosting** | CDN global, SSL gratis, $0 base, escalado infinito | Acoplamiento a Firebase (mitigable) |
| ADR-02 | API en **Cloud Run** con `min_instances=1` y `cpu_always_allocated=true` | WebSocket persistente requiere CPU asignado siempre. `min=1` elimina cold-starts del happy path | +$25/mes vs `min=0`, pero evita 30–60s de latencia en arranques |
| ADR-03 | Workers Celery + Redis en **una sola VM** GCE `e2-standard-2` con **CUD 1 año** | sentence-transformers necesita 2GB RAM residentes. CUD baja el costo ~40%. Memorystore Basic cuesta $40 que se ahorran self-hosting Redis | Redis no es HA. Mitigado con AOF + snapshot diario a GCS. Compromiso anual con GCP. |
| ADR-04 | Cloud SQL **`db-custom-1-3840` Zonal** (1 vCPU / 3.75 GiB) | Suficiente para decenas de miles de filas con pgvector + HNSW. HA regional duplica el costo de DB. | Aceptamos ~30 min de downtime ante falla zonal extrema. Escalable vertical en 5 min cuando duela. |
| ADR-05 | **PITR habilitado** en Cloud SQL | RPO de 5 min sin costo significativo adicional | ~$3/mes extra de almacenamiento de WAL |
| ADR-06 | **Mover `load_embedding_model()` fuera del API** (queda solo en workers) | El API no debe cargar 1.5GB de modelos. Los embeddings se hacen async vía Celery | Requiere refactor de [backend/app/main.py:32](backend/app/main.py#L32) — incluido en Fase 0 |
| ADR-07 | **Workload Identity Federation** (OIDC) entre GitHub Actions y GCP | Elimina claves JSON estáticas de Service Account (vector de leak #1) | Setup inicial más complejo, beneficio recurrente |
| ADR-08 | **Cloudflare (free tier)** delante de Cloud Run en lugar de Cloud Armor | DNS + CDN + WAF básico + DDoS L3/L4 gratis. Ahorra $5–8/mes y reemplaza también Cloud DNS ($1). Rate limiting fino ya está en la app. | Reglas WAF menos sofisticadas que Cloud Armor managed rules. Sin Adaptive Protection ni reglas L7 avanzadas. Suficiente para tráfico institucional. |
| ADR-09 | **Artifact Registry** (no Container Registry, deprecado) | Soporte nativo Cloud Run, vulnerability scanning automático | Mínimo ($2/mes) |
| ADR-10 | **Cloud Run Jobs** para migraciones Alembic | Permite ejecutar migrations antes del deploy del API, en una task one-off | Job adicional en el pipeline |
| ADR-11 | **Logging retención 7 días + sampling INFO 30%** + sink BigQuery de errores | Contiene el costo de Logging por debajo de $2/mes incluso bajo carga | Debug histórico de eventos no-error queda solo 7 días en Cloud Logging. Errores en BigQuery indefinido. |

---

## 2. Estimación de costos detallada

Todos los valores en USD/mes, región `us-central1`, precios públicos 2026.

| Componente | SKU | Configuración | Costo |
|------------|-----|---------------|-------|
| Cloud Run (API) | `min=1, max=10, cpu_always_allocated` | 1 vCPU, 1 GiB, ~300k req/mes | $28–32 |
| Compute Engine (Workers + Redis) | `e2-standard-2` 730h/mes **con CUD 1 año** | 2 vCPU, 8 GiB, 30 GiB SSD | $28–32 |
| Cloud SQL | `db-custom-1-3840` Zonal | 1 vCPU, 3.75 GiB RAM, 20 GiB SSD | $30–35 |
| Cloud SQL backups + PITR | Standard | 7 días retención | $3–5 |
| Serverless VPC Access | Connector mínimo (200 Mbps) | 2 instancias | $9–10 |
| Cloud Storage | Standard class, multi-region | 50 GiB + egress mínimo | $5–8 |
| Cloudflare (DNS + CDN + WAF) | **Free tier** | Plan Free | **$0** |
| Cloud Logging | Retención 7 días, sampling INFO al 30% | ~5 GiB/mes | $1–3 |
| Cloud Monitoring | Métricas custom + alertas | Standard | $0–3 |
| Artifact Registry | Standard | 20 GiB de imágenes | $2 |
| Secret Manager | 15 secretos, ~50k accesos/mes | Standard | $1–2 |
| Firebase Hosting | Spark/Blaze | 5 GiB storage + 10 GiB egress | $0–3 |
| Egress fuera de GCP | Internet egress (mitigado por CDN Cloudflare) | ~15 GiB/mes | $2–4 |
| Cloud DNS | **Eliminado** (DNS gestionado por Cloudflare) | — | **$0** |
| **TOTAL estimado** | | | **$109–139** |
| **Buffer operativo (15%)** | Picos, logs extras, snapshots | | **+$15–20** |
| **TOTAL con buffer** | | | **~$125–160** |

> **Ahorros vs Tier 1:**
> - CUD 1 año en GCE: **-$20/mes**
> - Cloud SQL más pequeña: **-$25/mes**
> - Cloudflare en lugar de Cloud Armor + Cloud DNS: **-$8/mes**
> - Logging más agresivo: **-$5/mes**
> - Egress reducido por CDN: **-$3/mes**
> - **Ahorro total: ~$60–90/mes**

> **Camino de escalado (cuando el tráfico lo justifique):**
> Ver sección 15 para upgrade a Tier 1 (~$230/mes) o tier enterprise con HA regional (~$285/mes).

---

## 3. Stack tecnológico y servicios

### 3.1. Capa de presentación — Frontend

**Servicio:** Firebase Hosting (plan Blaze pay-as-you-go).
- Build artifact: `frontend/dist/` generado por `npm run build` (Vite).
- CDN global automático, SSL Let's Encrypt renovado por Firebase.
- Headers de caché: `Cache-Control: max-age=31536000` para `/assets/*`, `no-cache` para `index.html`.
- Rewrites de SPA: todo lo no-archivo redirige a `index.html`.
- Connect dominio custom (ej. `linku.pe`) con DNS verificado.
- Preview channels por PR mediante `firebase hosting:channel:deploy <branch>`.

### 3.2. Capa de aplicación — Backend API

**Servicio:** Google Cloud Run (fully managed).

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| CPU | 1 vCPU | Suficiente para FastAPI async sin carga ML pesada |
| RAM | 1 GiB | Holgado tras sacar el modelo de embeddings del lifespan |
| Min instances | 1 | Elimina cold-start del happy path |
| Max instances | 10 | Permite escalar bajo picos sin descontrolar costo |
| Concurrency | 80 req/instancia | Default; ajustar tras load test |
| Timeout | 300 s | Permite uploads de CV y reportes largos |
| Execution environment | Second generation (gen2) | Soporta WebSocket, mejor performance |
| CPU allocation | `cpu_always_allocated = true` | **Obligatorio para WebSocket persistente** |
| Startup CPU boost | Habilitado | Reduce tiempo de readiness inicial |
| Service Account | `sa-cloud-run-api@...` con roles mínimos | Least privilege |
| VPC egress | Via Serverless VPC Connector → all-traffic | Acceso a Cloud SQL y Redis sin IP pública |
| Liveness | `/api/v1/health` cada 30s | Detecta hangs |
| Startup probe | `/api/v1/health` con `initial_delay=20s` | Permite que FastAPI termine de bootear |

### 3.3. Capa de procesamiento — Workers + Redis

**Servicio:** Compute Engine `e2-standard-2` (2 vCPU, 8 GiB RAM).

**Software stack en la VM:**
- Container OS: Ubuntu 22.04 LTS Minimal
- Docker Engine + Docker Compose v2
- Systemd unit `linku-workers.service` que ejecuta `docker compose up -d`
- Watchtower para auto-pull de imágenes nuevas (etiqueta `production`)
- Node exporter + cAdvisor para métricas a Prometheus
- Logrotate diario, retención 7 días

**Composición de containers en la VM (`docker-compose.production.yml`):**

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  worker-embeddings:
    image: <ar-host>/linku-backend:production
    command: celery -A app.tasks worker --queues=embeddings --concurrency=2 -n embeddings@%h
    deploy:
      resources:
        limits: { memory: 2.5G }
    environment:
      - REDIS_URL=redis://redis:6379/0
    restart: always

  worker-cv:
    image: <ar-host>/linku-backend:production
    command: celery -A app.tasks worker --queues=cv_generation --concurrency=2 -n cv@%h
    deploy:
      resources:
        limits: { memory: 700M }
    restart: always

  worker-notifications:
    image: <ar-host>/linku-backend:production
    command: celery -A app.tasks worker --queues=notifications,default --concurrency=4 -n notif@%h
    restart: always

  worker-reports:
    image: <ar-host>/linku-backend:production
    command: celery -A app.tasks worker --queues=reports --concurrency=1 -n reports@%h
    restart: always

  celery-beat:
    image: <ar-host>/linku-backend:production
    command: celery -A app.tasks beat --loglevel=info
    restart: always

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - prometheus_data:/prometheus
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    restart: always

  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 300 --label-enable
    restart: always

volumes:
  redis_data:
  prometheus_data:
```

**Backup de Redis:**
- Snapshot `dump.rdb` enviado a GCS cada 6 horas vía cron en la VM.
- AOF activo para durabilidad de tareas Celery en curso.
- Restauración: copiar `dump.rdb` de GCS al volumen y reiniciar Redis (< 5 min).

### 3.4. Capa de datos — PostgreSQL

**Servicio:** Cloud SQL for PostgreSQL 15 con extensión `pgvector`.

| Parámetro | Valor |
|-----------|-------|
| Tier | `db-custom-1-3840` (1 vCPU, 3.75 GiB RAM) |
| Disponibilidad | Zonal (Single-Zone) |
| Almacenamiento | 20 GiB SSD, auto-resize habilitado |
| Backups | Diarios a las 03:00 -05 (Lima), retención 7 días |
| PITR | Habilitado, retención 7 días de WAL |
| Maintenance window | Domingo 04:00 -05 |
| Flags | `cloudsql.iam_authentication=on`, `max_connections=100`, `shared_buffers=960MB` |
| IP pública | **Deshabilitada** |
| Authorized networks | Vacío (solo VPC privada) |
| SSL | `require` |

**Umbral de upgrade a Tier 1** (`db-custom-2-4096`):
- CPU sostenido > 70% durante 1 semana, **o**
- Memoria sostenida > 80% durante 1 semana, **o**
- Conexiones promedio > 70 (del límite de 100), **o**
- Latencia p95 de queries > 200 ms en endpoints de matching.

Upgrade en caliente vía `gcloud sql instances patch` — downtime de ~3–5 min.

**Extensiones a habilitar (post-provisioning):**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
```

**Índices HNSW críticos** (ya en migraciones, validar en post-deploy):
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workers_embedding_hnsw
  ON workers USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolio_embedding_hnsw
  ON portfolio_entries USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_listings_embedding_hnsw
  ON service_listings USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_embedding_hnsw
  ON job_offers USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
```

### 3.5. Capa de almacenamiento — GCS

**Buckets:**

| Bucket | Clase | Uso | Lifecycle |
|--------|-------|-----|-----------|
| `linku-cvs-prod` | Standard, multi-region | CVs PDF generados | Mover a Nearline tras 90d, eliminar a 365d |
| `linku-portfolio-prod` | Standard, multi-region | Fotos portfolio OFICIO | Mover a Nearline tras 180d |
| `linku-backups-prod` | Nearline | Dumps Redis + exports BD ad-hoc | Eliminar tras 30d |
| `linku-tf-state-prod` | Standard, single-region us-central1, versioning ON | Terraform state | Permanente |

**Configuración común:**
- Acceso público **bloqueado** a nivel bucket (Public Access Prevention enforced).
- Acceso por **Signed URLs** generadas por el backend con expiración 15 min.
- Uniform bucket-level access habilitado.
- Encryption at rest: claves gestionadas por Google (default) — opcional CMEK más adelante.

---

## 4. Red y seguridad

### 4.1. Topología de red

```
VPC: linku-vpc-prod (custom mode)
├── Subnet: subnet-private-us-central1 (10.20.0.0/24)
│   ├── Cloud SQL (private service connection)
│   ├── GCE VM workers (interfaz interna)
│   └── Serverless VPC Connector (10.20.1.0/28)
└── Firewall rules:
    ├── allow-internal: ingress 10.20.0.0/24 → all (TCP/UDP/ICMP)
    ├── allow-ssh-iap: ingress 35.235.240.0/20 → tag:ssh-iap (tcp:22)
    ├── deny-all-ingress: catch-all explícito
    └── allow-egress-all: default (a revisar para hardening)
```

**Cloud NAT:** habilitado en `us-central1` para que la VM y el VPC Connector tengan egress a internet (pull de imágenes, llamadas a APIs externas).

**Acceso SSH a la VM:** solo vía **Identity-Aware Proxy (IAP)**. Sin IP pública en la VM. Auditoría completa por Cloud Audit Logs.

### 4.2. Cloudflare (DNS + CDN + WAF gratis)

Cloudflare reemplaza a Cloud Armor y a Cloud DNS en Tier 2. Se configura el dominio `linku.pe` con DNS en Cloudflare apuntando al hostname de Cloud Run (vía registro `CNAME` proxied).

**Configuración Cloudflare (plan Free):**

| Feature | Configuración |
|---------|---------------|
| DNS | Zona gestionada en Cloudflare, propagación global |
| Proxy (orange cloud) | Habilitado en `api.linku.pe` → enmascara IP real de Cloud Run |
| SSL/TLS mode | `Full (strict)` — válida cert end-to-end |
| Always Use HTTPS | ON |
| HSTS | Max-age 6 meses, includeSubDomains, preload |
| WAF managed rules | Cloudflare Managed Ruleset (free tier) + OWASP Core Ruleset (paranoia 1) |
| Rate limiting | 10 req/10s por IP a `/api/v1/auth/*` (regla gratuita) |
| Bot Fight Mode | ON (mitigación bots básicos gratis) |
| Browser Integrity Check | ON |
| Security Level | Medium |
| Caching | Standard. Reglas de page rule: cachear `/static/*` agresivo, bypass `/api/*` |
| DDoS L3/L4 | Automático (incluido en free) |

**Limitaciones del free tier vs Cloud Armor:**
- Sin Adaptive Protection ML-based
- Sin reCAPTCHA Enterprise integrado
- Sin geo-blocking granular (solo countries en página de error)
- WAF custom rules limitadas a 5

**Mitigación a nivel aplicación** (ya existe):
- Rate limiting fino por endpoint en [backend/app/core/rate_limit.py](backend/app/core/rate_limit.py)
- JWT con expiración corta + blacklist en Redis
- Validación de input con Pydantic v2

**Importante:** dado que Cloudflare actúa como proxy, el `X-Forwarded-For` que llega a Cloud Run trae la IP del cliente real. El refactor **R7** debe confirmar que [backend/app/core/rate_limit.py](backend/app/core/rate_limit.py) lo lea correctamente. Adicionalmente, agregar middleware que valide el header `CF-Connecting-IP` (más confiable que XFF cuando viene de Cloudflare).

**Cuándo migrar a Cloud Armor** (escalado a Tier 1):
- Tráfico legítimo > 50k req/día sostenido
- Necesidad de bot management avanzado o reCAPTCHA Enterprise
- Requerimiento de compliance que exija WAF dentro de GCP (auditoría DRTPE formal)

### 4.3. Gestión de secretos

**Todos los secretos viven en Secret Manager**, ninguno en `.env`, ningún env var crudo en Cloud Run / VM.

| Secret | Consumido por | Rotación |
|--------|---------------|----------|
| `database-url-prod` | Cloud Run API, VM workers (via gcloud) | Manual al rotar password |
| `redis-url-prod` | Cloud Run API, workers | Anual |
| `jwt-private-key-prod` | Cloud Run API | Cada 6 meses |
| `jwt-public-key-prod` | Cloud Run API | Cada 6 meses |
| `aes-field-encryption-key-prod` | Cloud Run API, workers | **NUNCA** (datos cifrados se perderían) — versionar con cuidado |
| `gcs-bucket-cvs-name` | Cloud Run API, workers | N/A |
| `smtp-credentials-prod` | Workers (emails) | Anual |
| `drtpe-api-token-prod` | Cloud Run API | Según contrato DRTPE |
| `firebase-admin-key-prod` | Cloud Run API (si aplica) | Anual |
| `grafana-admin-password-prod` | VM workers | Trimestral |
| `slack-webhook-alerts-prod` | Cloud Monitoring | Anual |

**Acceso:** Service Accounts con rol `roles/secretmanager.secretAccessor` solo sobre los secretos que cada uno necesita. Auditado en Cloud Audit Logs.

### 4.4. IAM — Service Accounts

| SA | Roles | Usado por |
|----|-------|-----------|
| `sa-cloud-run-api` | `cloudsql.client`, `secretmanager.secretAccessor` (subset), `storage.objectAdmin` (subset), `monitoring.metricWriter`, `logging.logWriter` | Cloud Run service del API |
| `sa-cloud-run-jobs` | `cloudsql.client`, `secretmanager.secretAccessor` (subset), `logging.logWriter` | Cloud Run Job de migrations Alembic |
| `sa-gce-workers` | `cloudsql.client`, `secretmanager.secretAccessor` (subset), `storage.objectAdmin` (subset), `monitoring.metricWriter`, `logging.logWriter`, `artifactregistry.reader` | VM de workers |
| `sa-github-actions-ci` | `run.developer`, `iam.serviceAccountUser`, `artifactregistry.writer`, `storage.objectAdmin` (TF state), `cloudbuild.builds.editor` | GitHub Actions vía Workload Identity Federation |
| `sa-github-actions-tf` | `editor` (limitado a recursos del proyecto) | Solo workflow de `terraform apply` |

### 4.5. Workload Identity Federation (OIDC)

GitHub Actions se autentica contra GCP **sin claves JSON estáticas**:

```yaml
# Workflow snippet
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-pool/providers/github-provider
    service_account: sa-github-actions-ci@<PROJECT>.iam.gserviceaccount.com
```

Provider configurado con condición `assertion.repository == 'MikeielRP/Intermediacion-Laboral'`.

---

## 5. CI/CD — Pipelines necesarios

### 5.1. Estado actual y gaps

El workflow [.github/workflows/ci.yml](.github/workflows/ci.yml) actual:
- ✅ Lint, tests backend, tests frontend, build de imágenes a GHCR.
- ❌ Usa `GCP_SA_KEY` plano (debe migrar a OIDC).
- ❌ Despliega frontend a Cloud Run en vez de Firebase.
- ❌ No corre Alembic migrations antes del deploy.
- ❌ No despliega los workers a la VM.
- ❌ No tiene container scanning (Trivy).
- ❌ No tiene workflow de Terraform.

### 5.2. Workflows a crear / modificar

| Archivo | Trigger | Responsabilidad |
|---------|---------|-----------------|
| `.github/workflows/ci.yml` (refactor) | PR + push | Lint + tests + coverage + Trivy scan |
| `.github/workflows/terraform.yml` (nuevo) | PR/push en `infra/terraform/**` | `terraform fmt`, `validate`, `plan` (PR), `apply` (main con approval) |
| `.github/workflows/deploy-api.yml` (nuevo) | Push a `main` con cambios en `backend/**` | Build → push Artifact Registry → Cloud Run Job (migrate) → Cloud Run deploy (API) → smoke test → rollback automático si falla |
| `.github/workflows/deploy-workers.yml` (nuevo) | Push a `main` con cambios en `backend/**` | Build → push Artifact Registry. Watchtower en la VM hace pull cada 5 min. Workflow notifica a Slack al pushear |
| `.github/workflows/deploy-frontend.yml` (nuevo) | Push a `main` con cambios en `frontend/**` | `npm run build` → `firebase deploy --only hosting` |
| `.github/workflows/security.yml` (mantener + extender) | Cron semanal + push | Trivy en imágenes, OWASP ZAP baseline contra staging, dependency review |
| `.github/workflows/restore-drill.yml` (nuevo) | Cron mensual (día 1, 06:00 UTC) | Restaurar último backup a instancia temporal, ejecutar smoke tests, destruir. Falla → alerta crítica |

### 5.3. Deploy del API — flujo detallado

```
Push a main (backend/**)
  ↓
1. Lint + tests (re-corre)
  ↓
2. Build imagen Docker → tag = SHA + 'production'
  ↓
3. Trivy scan → falla si CVE HIGH/CRITICAL sin fix
  ↓
4. Push a Artifact Registry: us-central1-docker.pkg.dev/<proj>/linku/backend:<sha>
  ↓
5. Cloud Run Job 'linku-migrate' ejecuta `alembic upgrade head`
   → si falla, abortar y NO deployar API
  ↓
6. gcloud run deploy linku-api --image=...:<sha> --no-traffic --tag=candidate
   → despliega revisión sin recibir tráfico
  ↓
7. Smoke test contra URL de la revisión candidate
   → curl /api/v1/health, /api/v1/jobs/feed, /api/v1/auth/ping
  ↓
8. Migrate tráfico al candidate (gradual: 10% → 50% → 100% con 2 min entre pasos)
   → monitorear error rate; si > 1% rollback automático
  ↓
9. Tag revisión como 'stable', limpiar revisiones viejas (mantener últimas 5)
```

### 5.4. Estrategia de release del frontend

- Branch `main` → producción.
- Branch `develop` → staging (preview channel de Firebase: `staging.linku.web.app`).
- PRs → preview channel automático `pr-<n>.linku.web.app` con expiración 7 días.

---

## 6. Infrastructure as Code — Terraform

### 6.1. Estructura del directorio (a crear, NO existe hoy)

```
infra/terraform/
├── versions.tf                # Providers + required versions
├── backend.tf                 # GCS backend para state
├── variables.tf
├── outputs.tf
├── main.tf                    # Composición de módulos
├── environments/
│   ├── staging.tfvars
│   └── production.tfvars
└── modules/
    ├── network/               # VPC, subnets, firewall, Cloud NAT, VPC Connector
    ├── cloud_sql/             # Instance, DB, user, backups, PITR, flags
    ├── cloud_run/             # Service API + Job de migrations
    ├── compute_engine/        # VM workers + startup script + systemd unit
    ├── storage/               # Buckets GCS con lifecycle + IAM
    ├── secrets/               # Secret Manager (recursos vacíos, valores cargados aparte)
    ├── iam/                   # Service Accounts y bindings
    ├── load_balancer/         # HTTPS LB + Cloud Armor delante de Cloud Run
    ├── monitoring/            # Uptime checks, alertas, dashboards, log sinks
    └── workload_identity/     # WIF pool + provider para GitHub Actions
```

### 6.2. Backend de state

```hcl
# backend.tf
terraform {
  backend "gcs" {
    bucket = "linku-tf-state-prod"
    prefix = "production"
  }
}
```

Bucket creado **manualmente una sola vez** con versioning ON y lifecycle de borrado para versiones > 90 días.

### 6.3. Pipeline de Terraform

- PR con cambios en `infra/terraform/**` → `terraform plan` ejecutado por GitHub Actions, output comentado en el PR vía `actions/github-script`.
- Merge a `main` → `terraform apply` con **environment protection rule** que requiere approval manual.
- Drift detection semanal (`terraform plan` programado), si hay drift → alerta a Slack.

---

## 7. Refactors de código requeridos antes del deploy

Estos cambios deben mergearse **antes** de la primera fase de despliegue:

| # | Archivo | Cambio | Razón |
|---|---------|--------|-------|
| R1 | [backend/app/main.py:32](backend/app/main.py#L32) | Quitar `load_embedding_model()` del `lifespan`. Mantenerlo solo en los workers Celery (importación lazy donde se use) | El API no debe cargar 1.5GB de modelo. Reduce cold start de 60s a <5s |
| R2 | [backend/app/core/config.py](backend/app/core/config.py) | Agregar `JWT_PRIVATE_KEY` y `JWT_PUBLIC_KEY` como variables (no paths a archivos) leídas de Secret Manager | Cloud Run no tiene filesystem persistente; Secret Manager inyecta como env vars |
| R3 | [backend/Dockerfile](backend/Dockerfile) | Multi-stage build, usuario `nonroot`, healthcheck explícito, no instalar `build-essential` en stage final | Imagen más liviana y segura |
| R4 | `backend/Dockerfile.worker` (nuevo) | Imagen separada para workers que SÍ incluye spaCy model preinstalado y sentence-transformers cacheado | Evita pull del modelo en cada arranque del worker |
| R5 | `frontend/firebase.json` (nuevo) | Configuración de hosting + rewrites + headers de caché | Requerido por Firebase Hosting |
| R6 | `backend/app/api/v1/health.py` | Agregar endpoint `/api/v1/health/ready` que valide BD + Redis | Cloud Run startup probe requiere readiness real, no solo liveness |
| R7 | [backend/app/core/rate_limit.py](backend/app/core/rate_limit.py) | Confirmar que lee `X-Forwarded-For` correctamente cuando viene del HTTPS LB con Cloud Armor | El LB inyecta headers distintos a Cloud Run directo |

---

## 8. Observabilidad

### 8.1. Logging

- Todos los componentes loguean a **stdout/stderr** en formato **JSON estructurado** (structlog ya configurado en backend).
- Cloud Run + GCE → Cloud Logging automáticamente.
- **Log sink** de logs `severity >= ERROR` exportado a BigQuery (`linku_logs.errors`) para análisis histórico indefinido.
- **Retención agresiva** (Tier 2):
  - `_Default` bucket: **7 días** (en vez de los 30 días por defecto que cobran como almacenamiento extra)
  - `errors` sink BigQuery: indefinido (BigQuery cobra ~$0.02/GB/mes — los errores son volumen bajo)
- **Sampling Tier 2**: logs `INFO` reducidos al **30%** en producción. Logs `WARNING+` siempre al 100%. Logs `ERROR+` siempre al 100% + duplicados al sink BigQuery.
- **Exclusion filters** para reducir ruido sin perder señal:
  - Excluir healthchecks de `/api/v1/health` y `/api/v1/health/ready`
  - Excluir requests OPTIONS de CORS preflight
  - Excluir scrapes de `/metrics` de Prometheus
- **Budget**: target <$3/mes para Logging. Si excede, revisar volumen y endurecer sampling.

### 8.2. Métricas

**Cloud Monitoring (nativo):**
- Métricas estándar de Cloud Run (req/s, latencia, instancias, memoria, CPU).
- Métricas estándar de Cloud SQL (conexiones, lag, IOPS, CPU, RAM).
- Métricas estándar de GCE (CPU, memoria via OpsAgent, disco).

**Métricas custom (vía Prometheus en VM):**
- `celery_task_duration_seconds{queue, task}` — histograma por tarea.
- `celery_queue_length{queue}` — gauge.
- `redis_connected_clients`, `redis_memory_used_bytes`.
- `nlp_embedding_generation_duration_seconds{type}`.
- `ml_matching_score_distribution`.

Prometheus en la VM expone `/metrics` que un **stackdriver-exporter** envía a Cloud Monitoring como métricas externas, evitando hospedar Grafana en otra VM.

### 8.3. Alertas (Cloud Monitoring → Slack webhook)

| Alerta | Condición | Severidad | Canal |
|--------|-----------|-----------|-------|
| API 5xx rate alto | error_rate > 2% durante 5 min | CRITICAL | `#alerts-prod` + email |
| API latencia p95 | p95 > 1s durante 10 min | WARNING | `#alerts-prod` |
| Cloud Run sin instancias healthy | healthy_instance_count == 0 durante 2 min | CRITICAL | `#alerts-prod` + PagerDuty (futuro) |
| Cloud SQL CPU | cpu_utilization > 80% durante 15 min | WARNING | `#alerts-prod` |
| Cloud SQL conexiones | connections > 150 (de 200 max) | WARNING | `#alerts-prod` |
| Cloud SQL disk | disk_utilization > 75% | WARNING | `#alerts-prod` |
| VM workers RAM | mem_used > 90% durante 10 min | WARNING | `#alerts-prod` |
| VM workers desconectada | instance_up == 0 durante 3 min | CRITICAL | `#alerts-prod` |
| Celery queue length | queue_length > 100 durante 10 min | WARNING | `#alerts-prod` |
| Redis memoria | mem_used > 80% del max | WARNING | `#alerts-prod` |
| ML F1-score | f1 < 0.70 (custom metric) | WARNING | `#alerts-ml` |
| Disparate impact | ratio < 0.80 (custom metric) | CRITICAL | `#alerts-ml` |
| Restore drill failure | job de restore mensual falló | CRITICAL | `#alerts-prod` |
| Budget alert | 80% / 100% / 120% del budget | INFO / WARNING / CRITICAL | `#alerts-budget` |

### 8.4. Dashboards Cloud Monitoring

- **Overview Linku**: tráfico API, latencia, error rate, instancias activas, queue lengths.
- **ML/NLP**: throughput embeddings, F1-score, drift PSI, disparate impact, top sectors matched.
- **Infraestructura**: CPU/RAM/disco de VM y Cloud SQL, conexiones BD, hits/misses Redis.
- **Negocio (KPIs)**: VIL, IVP, tasa formalización, registros nuevos/día (consumidas vía `kpi_calculator.py`).

---

## 9. Backups, recuperación y DR

### 9.1. Estrategia de backups

| Recurso | Mecanismo | Frecuencia | Retención | Lugar |
|---------|-----------|------------|-----------|-------|
| Cloud SQL | Backup automático managed | Diario 03:00 -05 | 7 días | Cloud SQL backup storage |
| Cloud SQL WAL (PITR) | Continuo | Real-time | 7 días | Cloud SQL backup storage |
| Cloud SQL export lógico | `pg_dump` vía Cloud Run Job | Semanal (domingo) | 4 semanas | `linku-backups-prod` GCS |
| Redis | `BGSAVE` + rsync a GCS | Cada 6 h | 7 días | `linku-backups-prod` GCS |
| GCS buckets | Object Versioning + soft delete | Continuo | 30 días | Mismo bucket |
| Terraform state | GCS versioning | Continuo | 90 días | `linku-tf-state-prod` |
| Secret Manager | Versionado nativo | Por cambio | Versiones previas accesibles | Secret Manager |

### 9.2. Plan de Recuperación de Desastre

**Escenario 1: Falla zonal de Cloud SQL**
- Acción: failover manual a backup más reciente, restaurar en zona alternativa.
- RTO: ~30 min, RPO: 5 min (PITR).
- Responsable: ingeniería de guardia.

**Escenario 2: Pérdida de la VM de workers**
- Acción: Terraform recrea la VM con startup script idéntico. Watchtower pull las imágenes. Redis restaurado desde último snapshot en GCS.
- RTO: ~20 min, RPO: 6 h para Redis (tareas en cola pueden perderse — Celery hace retry de las idempotentes).

**Escenario 3: Compromiso de credenciales**
- Acción: rotación inmediata de **todos** los secretos (excepto AES_KEY), revoke de Service Accounts, audit log review.
- RTO: ~2 h.

**Escenario 4: Borrado accidental de la BD**
- Acción: restaurar desde PITR al punto anterior al borrado.
- RTO: ~45 min, RPO: 5 min.

**Escenario 5: Cuenta de GCP comprometida o cerrada**
- Acción: backups lógicos `pg_dump` viven en GCS dentro del mismo proyecto. Riesgo residual: si el proyecto se cierra se pierde todo.
- Mitigación: **export mensual a GCS de un proyecto/cuenta separada** (organización del usuario). Costo marginal.

### 9.3. Restore drill obligatorio

- Workflow `restore-drill.yml` corre el día 1 de cada mes:
  1. Crea instancia Cloud SQL temporal `linku-drill-<timestamp>`.
  2. Restaura backup más reciente.
  3. Conecta y valida: número de tablas, conteo de filas en `users`, `workers`, `contracts`.
  4. Ejecuta smoke tests de queries críticas (matching, marketplace).
  5. Destruye la instancia.
  6. Si cualquier paso falla → alerta CRITICAL.
- Costo del drill: ~$2/mes (instancia viva ~1 hora).
- **Sin drill mensual exitoso, NO hay garantía de DR.**

---

## 10. Runbook de incidentes (resumen)

Archivo completo a producir como `docs/runbook_produccion.md` antes del go-live. Estructura mínima:

1. **Detección**: alerta dispara en Cloud Monitoring → Slack `#alerts-prod`.
2. **Triage**: revisar dashboard "Overview Linku" → identificar componente afectado.
3. **Playbooks por componente**:
   - API caída: rollback a revisión `stable` (`gcloud run services update-traffic linku-api --to-revisions=stable=100`).
   - BD lenta: revisar Query Insights, identificar query top, vacuum/analyze si aplica.
   - Workers atascados: `docker compose restart` en la VM vía IAP SSH.
   - Redis lleno: `redis-cli FLUSHDB` solo de DB de caché (NO la del broker), evaluar subir `maxmemory`.
4. **Comunicación**: status page (estática en Firebase) actualizada manualmente; mensaje a stakeholders DRTPE si downtime > 30 min.
5. **Post-mortem**: dentro de 48 h del cierre del incidente. Template en `docs/postmortem_template.md`.

---

## 11. Roadmap de implementación

### Fase 0 — Preparación de código (1 semana)

1. R1 a R7 de la sección 7 (refactors de código).
2. Crear `frontend/firebase.json`.
3. Crear `backend/Dockerfile.worker` separado.
4. Tests de los nuevos endpoints `/health/ready`.

### Fase 1 — Infraestructura base con Terraform (1 semana)

1. Crear proyecto GCP `linku-prod` con **billing alerts a $100, $140 y $180** y hard cap a $200.
2. Crear manualmente: bucket de state, Workload Identity Pool.
3. **Comprar CUD 1 año** para `e2-standard-2` en `us-central1` (descuento ~40% sobre el on-demand).
4. Escribir módulos Terraform en orden: `network`, `iam`, `secrets`, `storage`, `cloud_sql`, `compute_engine`, `cloud_run`, `monitoring`. (No se incluye `load_balancer` ni `cloud_armor` en Tier 2 — Cloudflare hace el fronting.)
5. `terraform apply` desde laptop por primera vez (provisión inicial).
6. Cargar valores reales de secretos en Secret Manager (manualmente, una vez).
7. Configurar Workload Identity Federation para GitHub Actions.

### Fase 1.5 — Configuración de Cloudflare (1 día)

1. Crear cuenta Cloudflare gratis y agregar dominio `linku.pe`.
2. Cambiar nameservers del dominio en el registrador a los de Cloudflare.
3. Crear registros DNS:
   - `linku.pe` → CNAME a Firebase Hosting (proxied)
   - `api.linku.pe` → CNAME al hostname de Cloud Run (proxied)
   - `www.linku.pe` → redirect a `linku.pe`
4. Configurar SSL/TLS: modo `Full (strict)`, certificado origen instalado en Cloud Run vía dominio custom.
5. Habilitar WAF managed rules, Bot Fight Mode, rate limiting básico.
6. Configurar page rules para caché de estáticos.
7. Validar end-to-end: `curl -v https://api.linku.pe/api/v1/health` debe responder con headers `cf-ray` y `cf-cache-status`.

### Fase 2 — Datos y migración (3 días)

1. Cloud Run Job `linku-migrate` ejecuta Alembic contra Cloud SQL → todas las migraciones existentes aplicadas.
2. Habilitar extensiones `vector`, `pg_trgm`, `unaccent`.
3. Validar índices HNSW creados.
4. Seed mínimo de datos (diccionario Huancayo, sectores DRTPE).
5. Generar JWT keypair y subir a Secret Manager.
6. Generar AES key (32 bytes, base64) y subir a Secret Manager **con respaldo offline en gestor de passwords personal**.

### Fase 3 — Despliegue de aplicaciones (1 semana)

1. CI: refactor de `ci.yml` para OIDC + Trivy.
2. CI: crear `deploy-api.yml`, `deploy-workers.yml`, `deploy-frontend.yml`.
3. Deploy a **staging** primero (mismo Terraform, `environments/staging.tfvars` con tier reducido: `db-f1-micro`, VM `e2-small`).
4. Validar en staging: registro, login, wizard, búsqueda marketplace, generación CV.
5. Deploy a **production**.

### Fase 4 — Observabilidad y go-live (3 días)

1. Crear dashboards Cloud Monitoring (4 dashboards de sección 8.4).
2. Configurar alertas con webhook a Slack.
3. Configurar uptime checks externos.
4. Smoke test E2E completo en producción.
5. Restore drill manual (primera vez).
6. Configurar workflow `restore-drill.yml` para corrida automática mensual.
7. Documentar runbook completo.

### Fase 5 — Hardening post-go-live (continuo)

1. Configurar OWASP ZAP en CI semanal contra staging.
2. Habilitar Cloud Armor adaptive protection.
3. Revisar logs de auditoría semanalmente.
4. Optimizar consultas tras 2 semanas de tráfico real (Query Insights de Cloud SQL).
5. Evaluar mover a HA regional de Cloud SQL si DAU crece consistentemente.

---

## 12. Checklist pre-go-live

Antes de exponer la URL pública:

### Infraestructura
- [ ] Terraform `apply` exitoso en producción
- [ ] State en GCS con versioning
- [ ] WIF configurado, sin SA keys estáticas en GitHub
- [ ] VPC privada, sin IPs públicas en DB ni Redis
- [ ] **CUD 1 año comprado** para `e2-standard-2`
- [ ] **Cloudflare configurado**: DNS, proxy proxied, SSL Full strict, WAF + Bot Fight Mode + rate limit en `/auth/*`
- [ ] Dominio custom validado en Cloud Run (`api.linku.pe`)
- [ ] Cert SSL end-to-end validado (Cloudflare → Cloud Run)

### Datos
- [ ] Migraciones Alembic aplicadas
- [ ] Extensiones `vector`, `pg_trgm`, `unaccent` habilitadas
- [ ] Índices HNSW creados y `EXPLAIN ANALYZE` validado
- [ ] PITR habilitado, backup diario verificado
- [ ] Restore drill manual exitoso al menos una vez

### Aplicación
- [ ] `load_embedding_model()` removido del lifespan del API
- [ ] Workers en la VM corriendo todos los 4 queues + beat
- [ ] WebSocket de notificaciones probado E2E
- [ ] Generación de CV PDF probada
- [ ] Matching ML probado con datos reales

### Seguridad
- [ ] AES_KEY de producción generada y respaldada offline
- [ ] JWT keypair RS256 generado, claves en Secret Manager
- [ ] Todos los secretos en Secret Manager, ningún `.env` deployado
- [ ] Rate limiting validado bajo carga (10 req/s sostenido por IP)
- [ ] CORS configurado solo con orígenes de producción
- [ ] Headers de seguridad validados (HSTS, CSP, X-Frame-Options)
- [ ] DNI no aparece en ningún log ni response

### Observabilidad
- [ ] Dashboards creados
- [ ] Alertas activas y testeadas (disparar manualmente al menos una de cada severidad)
- [ ] Slack webhook recibiendo correctamente
- [ ] Uptime checks externos configurados
- [ ] Budget alerts a $100/$140/$180, hard cap a $200

### Operación
- [ ] Runbook completo en `docs/runbook_produccion.md`
- [ ] Contactos de guardia documentados
- [ ] Status page preparada (puede ser estática en Firebase)
- [ ] DRTPE notificada de fecha de go-live y URL

---

## 13. Riesgos residuales aceptados

| Riesgo | Probabilidad | Impacto | Mitigación / decisión |
|--------|--------------|---------|-----------------------|
| Falla zonal extendida de Cloud SQL | Baja | Alto | Aceptado. PITR + restore en zona alterna en ~30 min. HA regional descartada por costo. |
| Pérdida de tareas Celery en vuelo si Redis se cae | Baja | Medio | Aceptado. AOF reduce ventana a < 1s. Las tareas críticas tienen idempotencia + retry. |
| Cold start de Cloud Run al escalar de 1 a 2 | Media | Bajo | Aceptado tras R1. Sin el modelo de embeddings, startup < 5s. |
| Single point of failure de la VM de workers | Media | Medio | Aceptado. Recreación automatizable por Terraform en ~20 min. Workers no son real-time-críticos. |
| Costo se dispara por logs en incidente prolongado | Media | Bajo | Mitigado por sampling + exclusion filters + budget alert + hard cap del proyecto. |
| Compromiso del repo GitHub | Baja | Crítico | Mitigado por WIF (sin keys), branch protection, required reviews, audit logs. |
| Pérdida de AES_KEY | Muy baja | Crítico (datos cifrados irrecuperables) | Mitigado por backup offline en password manager personal + versionado en Secret Manager. |
| **Cloudflare degrada o cambia su free tier** | Baja | Medio | Aceptado. Migración a Cloud Armor + HTTPS LB es ~1 día de trabajo. Plan documentado en sección 15. |
| **Cloud SQL `db-custom-1-3840` insuficiente** bajo crecimiento de usuarios | Media | Medio | Mitigado por umbrales de upgrade definidos en §3.4. Upgrade en caliente ~5 min. |
| **CUD comprado y proyecto se cancela** antes del año | Baja | Medio | Pérdida máxima ~$240 (precio comprometido). Aceptable vs $240/año de ahorro garantizado si el proyecto continúa. |
| **DRTPE requiere auditoría con WAF dentro de GCP** | Baja | Medio | Migración a Cloud Armor planeada. Cloudflare free no aplica para compliance estricto. |

---

## 14. Camino de escalado — de Tier 2 a Tier 1 (y más allá)

El Tier 2 está diseñado para vivir cómodo entre **0 y ~500 usuarios activos/día**. Cuando el tráfico crezca, el upgrade es gradual y sin reescribir nada.

### 15.1. Señales de upgrade (qué mirar)

| Señal | Umbral | Acción |
|-------|--------|--------|
| Cloud SQL CPU sostenido | > 70% durante 1 semana | Upgrade tier DB |
| Cloud SQL conexiones | > 70/100 promedio diario | Upgrade tier DB + revisar pool de SQLAlchemy |
| Latencia p95 endpoints matching | > 200 ms | Upgrade tier DB |
| Cloud Run instancias activas | > 5 sostenidas | Revisar concurrency; subir `max_instances` |
| Tráfico legítimo | > 50k req/día sostenido | Migrar a Cloud Armor |
| Compliance/auditoría DRTPE formal | Requerimiento contractual | Migrar a Cloud Armor + HA regional |
| Bot abuse persistente | > 1000 bots/día bloqueados | Activar Cloudflare paid o Cloud Armor |

### 15.2. Upgrade incremental (con costos delta)

**Paso 1 — Subir Cloud SQL** (+$25/mes → total ~$165)
```bash
gcloud sql instances patch linku-pg-prod \
  --tier=db-custom-2-4096 \
  --cpu=2 --memory=4096
```
Downtime: ~3–5 min. Hacerlo en ventana de baja actividad.

**Paso 2 — Migrar WAF a Cloud Armor + HTTPS LB** (+$15/mes → total ~$180)
1. Provisionar External HTTPS Load Balancer en Terraform (módulo `load_balancer`).
2. Crear política `linku-armor-prod` con reglas managed (sección 4.2 del plan v2.0 original).
3. Apuntar Cloudflare a la IP del LB en modo **DNS-only** (gray cloud) o desactivar proxy.
4. Validar que `X-Forwarded-For` lleguen correctamente vía Cloud Armor.

**Paso 3 — Cloud SQL HA regional** (+$55/mes → total ~$235, equivalente a Tier 1 enterprise)
```bash
gcloud sql instances patch linku-pg-prod \
  --availability-type=REGIONAL
```
Failover automático ante falla zonal. RTO baja a < 60 s.

**Paso 4 — Read replica para offload de queries pesadas** (+$60/mes)
Cuando los dashboards de KPIs DRTPE empiecen a competir con el tráfico transaccional. Configurar SQLAlchemy con engine separado de solo-lectura para `app/services/reports/kpi_calculator.py`.

**Paso 5 — Workers en MIG (Managed Instance Group)** (+$50/mes)
Reemplazar la VM única por un MIG con `target_size=2` y auto-healing. Elimina el SPOF. Redis se mueve a Memorystore en este punto (+$40 adicional).

### 15.3. Matriz comparativa

| Característica | Tier 2 actual | Tier 1 (~$230) | Enterprise (~$320+) |
|----------------|---------------|----------------|---------------------|
| Cloud SQL | 1 vCPU/3.75GB Zonal | 2 vCPU/4GB Zonal | 2 vCPU/4GB **Regional HA** + replica |
| WAF | Cloudflare Free | Cloud Armor + Cloudflare DNS-only | Cloud Armor Adaptive + reCAPTCHA Enterprise |
| Workers | 1 VM `e2-standard-2` con CUD | 1 VM `e2-standard-2` | MIG 2x `e2-standard-2` + Memorystore |
| Redis | Self-hosted en VM (AOF + snapshot) | Self-hosted | **Memorystore HA** |
| HA Cloud Run | min=1 | min=2 | min=2 multi-region |
| Backups | PITR 7d + snapshot semanal | + snapshot diario a proyecto separado | + cross-region replication |
| SLO disponibilidad | 99.5% | 99.9% | 99.95% |
| **Costo/mes** | **~$140** | **~$230** | **~$320+** |

### 15.4. Cuándo NO escalar

- Si el costo crece pero los KPIs de uso no → optimizar app antes que infra.
- Si las latencias se degradan en un endpoint específico → optimizar la query, no subir la DB.
- Si Cloud Run escala mucho → revisar `concurrency` antes de subir `max_instances`.

**Regla:** el upgrade se justifica solo si **una métrica de SLO está fallando** o **el negocio pide algo que Tier 2 no soporta** (compliance, HA estricta). Subir tier por miedo es desperdicio.

---

## 15. Anexo — Comandos de referencia rápida

```bash
# Conectar a Cloud SQL desde la laptop (vía Cloud SQL Auth Proxy)
cloud-sql-proxy <PROJECT>:us-central1:linku-pg-prod &
psql "host=127.0.0.1 dbname=linku user=linku_admin"

# SSH a la VM de workers (vía IAP)
gcloud compute ssh linku-workers-vm --zone=us-central1-a --tunnel-through-iap

# Ver logs de Cloud Run en tiempo real
gcloud run services logs tail linku-api --region=us-central1

# Forzar rollout al revision anterior
gcloud run services update-traffic linku-api --to-revisions=PREVIOUS=100 --region=us-central1

# Ejecutar Cloud Run Job de migración
gcloud run jobs execute linku-migrate --region=us-central1 --wait

# Restaurar BD a punto en el tiempo
gcloud sql backups restore <BACKUP_ID> --restore-instance=linku-pg-prod-restored \
  --backup-instance=linku-pg-prod

# Snapshot manual de Redis (en la VM)
docker exec linku-redis redis-cli BGSAVE
gsutil cp /var/lib/redis/dump.rdb gs://linku-backups-prod/redis/manual-$(date +%F).rdb

# Disparar deploy desde local (último recurso)
gcloud run deploy linku-api \
  --image=us-central1-docker.pkg.dev/<PROJECT>/linku/backend:<sha> \
  --region=us-central1 --no-traffic --tag=hotfix
```

---

*Plan elaborado siguiendo la skill `devops-engineer` y los lineamientos de la sección 4.3.2 (RF/RNF). Cualquier desviación durante la implementación debe reflejarse aquí y aprobarse en review.*
