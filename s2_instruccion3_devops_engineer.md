Eres el agente devops-engineer. Lee el archivo CLAUDE.md en la raíz del repositorio antes de tocar cualquier archivo. Para todo el trabajo usa la herramienta Bash.

Genera y aplica las migraciones nuevas del Sprint 2 y verifica que el entorno Docker sigue funcionando. Sigue exactamente las especificaciones del archivo sprint2_claude_code.md, Bloque 5.

MIGRACIÓN 0002_job_offers: genera con alembic revision --autogenerate -m "0002_job_offers". Edita el archivo para agregar manualmente el índice HNSW sobre job_offers.embedding y el índice único sobre (worker_id, job_offer_id) en applications. El downgrade debe eliminar índices y tablas en orden inverso a las FK.

MIGRACIÓN 0003_worker_profile_fields: genera con alembic revision --autogenerate -m "0003_worker_profile_fields". Agrega en workers: bio TEXT, job_title VARCHAR(100), username VARCHAR(50) UNIQUE, education_level VARCHAR(50) CHECK IN ('primaria','secundaria','tecnico','universitario','ninguno'). Agrega en wizard_progress: job_interests JSONB DEFAULT '[]'. Actualiza app/models/worker.py y app/models/wizard.py con los campos nuevos. Actualiza app/schemas/worker.py para incluir username y education_level en WorkerProfileResponse y WorkerProfileUpdate. Actualiza app/services/onboarding/detector.py para generar username automático con slugify al crear el perfil.

Aplica ambas migraciones:
alembic upgrade head

Verifica con:
alembic history --verbose
docker-compose exec db psql -U postgres -d intermediacion_laboral -c "\d workers"
docker-compose exec db psql -U postgres -d intermediacion_laboral -c "\d job_offers"
docker-compose exec db psql -U postgres -d intermediacion_laboral -c "SELECT indexname FROM pg_indexes WHERE indexname LIKE '%embedding%' OR indexname LIKE '%hnsw%';"

Verifica que Docker sigue funcionando:
docker-compose down -v
docker-compose up -d --build
docker-compose ps

Al terminar muéstrame la salida de todos los comandos anteriores más:
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
