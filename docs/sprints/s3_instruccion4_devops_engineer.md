# SPRINT 3 — INSTRUCCIÓN 4 de 5
# Agente: `devops-engineer`
# Tarea: Celery Beat schedule + docker-compose multi-worker + Prometheus + Grafana

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
Las instrucciones 1–3 del Sprint 3 entregaron:
- Seguridad hardened + tabla `match_events`
- Motor de matching M05 completo
- Generación de CVs PDF + WebSocket + alertas

**Tu trabajo:** Configurar la infraestructura de workers Celery con colas separadas,
el schedule de tareas programadas (Celery Beat), y el stack de monitoreo (Prometheus + Grafana).

---

## PARTE A — Celery Beat — Schedule completo

Actualiza `app/core/celery_app.py`:

```python
# app/core/celery_app.py
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "drtpe_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Lima",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Colas diferenciadas por prioridad
    task_queues={
        "embeddings":     {"exchange": "embeddings",     "routing_key": "embeddings"},
        "cv_generation":  {"exchange": "cv_generation",  "routing_key": "cv_generation"},
        "notifications":  {"exchange": "notifications",  "routing_key": "notifications"},
        "reports":        {"exchange": "reports",        "routing_key": "reports"},
        "default":        {"exchange": "default",        "routing_key": "default"},
    },
    task_default_queue="default",
    task_routes={
        "tasks.generate_embedding":     {"queue": "embeddings"},
        "tasks.generate_cv":            {"queue": "cv_generation"},
        "tasks.send_notification":      {"queue": "notifications"},
        "tasks.generate_report":        {"queue": "reports"},
        "tasks.process_job_alerts":     {"queue": "default"},
        "tasks.reindex_marketplace":    {"queue": "embeddings"},
    },
    # ✅ Schedule completo de tareas programadas
    beat_schedule={
        # Embeddings: regenerar perfiles actualizados (diario 2am Lima)
        "regenerate-stale-embeddings": {
            "task": "tasks.regenerate_stale_embeddings",
            "schedule": crontab(hour=2, minute=0),
            "kwargs": {"max_age_days": 7},
        },
        # Alertas de empleo: verificar nuevas ofertas vs alertas activas (cada hora)
        "process-job-alerts": {
            "task": "tasks.process_all_job_alerts",
            "schedule": crontab(minute=0),
        },
        # KPIs de la tesis: calcular y cachear (diario 6am Lima)
        "calculate-kpis": {
            "task": "tasks.calculate_kpis",
            "schedule": crontab(hour=6, minute=0),
        },
        # Marketplace: reindexar listings activos (diario 3am Lima)
        "reindex-marketplace": {
            "task": "tasks.reindex_listings",
            "schedule": crontab(hour=3, minute=0),
        },
        # Reentrenar modelo ML si hay suficientes datos nuevos (semanal lunes 4am)
        "retrain-matching-model": {
            "task": "tasks.retrain_model_if_needed",
            "schedule": crontab(hour=4, minute=0, day_of_week=1),
        },
        # Limpiar tokens JWT expirados de Redis (diario 1am)
        "cleanup-expired-tokens": {
            "task": "tasks.cleanup_expired_tokens",
            "schedule": crontab(hour=1, minute=0),
        },
    },
)
```

---

## PARTE B — docker-compose.yml completo

Reemplaza o actualiza `docker-compose.yml` con el siguiente contenido:

```yaml
version: "3.9"

x-backend-common: &backend-common
  build:
    context: ./backend
    dockerfile: Dockerfile
  environment:
    DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@db:5432/drtpe
    REDIS_URL: redis://redis:6379/0
    SECRET_KEY: ${SECRET_KEY}
    GCS_BUCKET: ${GCS_BUCKET}
    ENV: ${ENV:-development}
    CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000}
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
  volumes:
    - ./backend:/app
  networks:
    - drtpe_net

services:
  # ─── Base de datos ───────────────────────────────────────────
  db:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: drtpe
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d drtpe"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - drtpe_net

  # ─── Redis ───────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - drtpe_net

  # ─── Backend API ──────────────────────────────────────────────
  api:
    <<: *backend-common
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ─── Celery Workers (colas separadas) ────────────────────────
  worker-embeddings:
    <<: *backend-common
    command: >
      celery -A app.core.celery_app worker
      --loglevel=info
      --queues=embeddings
      --concurrency=2
      --hostname=worker-embeddings@%h
    deploy:
      resources:
        limits:
          memory: 1G   # sentence-transformers es pesado

  worker-cv:
    <<: *backend-common
    command: >
      celery -A app.core.celery_app worker
      --loglevel=info
      --queues=cv_generation
      --concurrency=2
      --hostname=worker-cv@%h
    deploy:
      resources:
        limits:
          memory: 512M

  worker-notifications:
    <<: *backend-common
    command: >
      celery -A app.core.celery_app worker
      --loglevel=info
      --queues=notifications,default
      --concurrency=4
      --hostname=worker-notifications@%h

  worker-reports:
    <<: *backend-common
    command: >
      celery -A app.core.celery_app worker
      --loglevel=info
      --queues=reports
      --concurrency=1
      --hostname=worker-reports@%h

  # ─── Celery Beat (scheduler) ─────────────────────────────────
  celery-beat:
    <<: *backend-common
    command: >
      celery -A app.core.celery_app beat
      --loglevel=info
      --scheduler django_celery_beat.schedulers:DatabaseScheduler
    # Solo UNA instancia de beat — nunca escalar

  # ─── Flower (monitoreo Celery) ────────────────────────────────
  flower:
    <<: *backend-common
    command: >
      celery -A app.core.celery_app flower
      --port=5555
      --basic_auth=${FLOWER_USER:-admin}:${FLOWER_PASSWORD:-changeme}
    ports:
      - "5555:5555"

  # ─── Frontend ────────────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000
      VITE_WS_URL: ws://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - drtpe_net

  # ─── Prometheus ──────────────────────────────────────────────
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=15d"
    networks:
      - drtpe_net

  # ─── Grafana ────────────────────────────────────────────────
  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_USER:-admin}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-changeme}
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    networks:
      - drtpe_net

networks:
  drtpe_net:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

---

## PARTE C — Configuración de Prometheus

Crea `infra/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "drtpe-api"
    static_configs:
      - targets: ["api:8000"]
    metrics_path: "/metrics"

  - job_name: "celery"
    static_configs:
      - targets: ["flower:5555"]
    metrics_path: "/metrics"

  - job_name: "postgres"
    static_configs:
      - targets: ["db:5432"]

  - job_name: "redis"
    static_configs:
      - targets: ["redis:6379"]
```

Crea `infra/grafana/provisioning/datasources/prometheus.yml`:

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

---

## PARTE D — Exponer métricas Prometheus en FastAPI

Agrega en `app/main.py`:

```python
from prometheus_fastapi_instrumentator import Instrumentator

# Después de crear la app FastAPI
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

Actualizar `requirements.txt`: `prometheus-fastapi-instrumentator>=6.0.0`

---

## PARTE E — Endpoint de salud

Implementar `GET /api/v1/health` si no existe:

```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from redis.asyncio import Redis
from app.core.db import get_redis

router = APIRouter(tags=["health"])

@router.get("/api/v1/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Health check para Docker + load balancer."""
    # Verificar BD
    try:
        await db.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    # Verificar Redis
    try:
        await redis.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "db": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
```

---

## PARTE F — .env.example actualizado

Actualiza `.env.example`:

```bash
# Base de datos
POSTGRES_PASSWORD=changeme_in_production

# Seguridad
SECRET_KEY=generate_with_openssl_rand_hex_32

# CORS
CORS_ORIGINS=http://localhost:3000

# GCS
GCS_BUCKET=drtpe-junin-bucket
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-key.json

# Flower
FLOWER_USER=admin
FLOWER_PASSWORD=changeme

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=changeme

# Entorno
ENV=development
```

Verificar que `credentials/gcp-key.json` está en `.gitignore`:

```bash
echo "backend/credentials/" >> .gitignore
echo "*.json" >> .gitignore   # NO — demasiado amplio
# Específico:
echo "backend/credentials/gcp-key.json" >> .gitignore
```

---

## VERIFICACIONES FINALES

```bash
# Levantar el stack completo
docker-compose up -d

# Verificar que todos los servicios están saludables
docker-compose ps

# Health check del API
curl http://localhost:8000/api/v1/health
# Esperado: {"status":"ok","db":"ok","redis":"ok"}

# Verificar que los workers Celery están procesando
docker-compose logs worker-embeddings | tail -20
docker-compose logs worker-notifications | tail -20

# Flower (monitoreo Celery)
open http://localhost:5555

# Prometheus
open http://localhost:9090

# Grafana
open http://localhost:3001

# Métricas del API
curl http://localhost:8000/metrics | grep http_requests

# Verificar que el beat scheduler está corriendo
docker-compose logs celery-beat | grep "Scheduler"
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `app/core/celery_app.py` — schedule completo con 6 tareas programadas
- `docker-compose.yml` — 4 workers Celery con colas separadas
- `infra/prometheus/prometheus.yml` — scraping API + Celery
- `infra/grafana/provisioning/datasources/prometheus.yml`
- `app/api/v1/health.py` — health check BD + Redis
- `app/main.py` — instrumentación Prometheus
- `.env.example` — completo y actualizado
- `.gitignore` — credentials GCP excluidas
- `requirements.txt` — prometheus-fastapi-instrumentator

---

**Cuando termines, el agente `python-pro` con skill `senior-backend` recibirá la instrucción 5
para implementar los tests de integración completos del Sprint 3 y verificar cobertura ≥ 80%.**
