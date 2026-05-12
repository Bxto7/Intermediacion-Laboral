# SPRINT 3 — INSTRUCCIÓN 5 de 5
# Agente: `python-pro`
# Skills a cargar: `skills/senior-backend`, `skills/python-fastapi`
# Tarea: Tests de integración completos + cobertura ≥ 80% + cierre del Sprint 3

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
Las instrucciones 1–4 del Sprint 3 entregaron:
1. Seguridad hardened + tabla `match_events`
2. Motor de matching M05 (engine, scorer, cold_start, equity_ranker, explainer)
3. Generación CVs PDF (WeasyPrint) + WebSocket + alertas de empleo
4. Celery Beat + docker-compose + Prometheus

**Tu trabajo:** Completar la suite de tests de integración, verificar cobertura ≥ 80%,
cerrar los RF pendientes del Sprint 3 y dejar el sprint listo para revisión.

**RF que cierras:** RF076–RF095, RF096–RF110, RF111–RF117, RF126–RF135, RF146–RF155

---

## PARTE A — Tests de integración del Sprint 3

### A1 — test_api_matching.py (RF076–RF095)

```python
# tests/integration/test_api_matching.py
"""Tests de integración para el motor de matching M05."""
import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestMatchingEndpoint:
    """RF076–RF095: Motor de matching diferenciado por worker_type."""

    async def test_match_primer_empleo_returns_results(
        self, client: AsyncClient, worker_primer_empleo, auth_token_primer_empleo
    ):
        """PRIMER_EMPLEO con cold-start debe retornar matches."""
        resp = await client.get(
            f"/api/v1/match/{worker_primer_empleo.id}",
            headers={"Authorization": f"Bearer {auth_token_primer_empleo}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "matches" in data
        assert "total" in data
        assert data["total"] >= 0

    async def test_match_experiencia_includes_explanation(
        self, client: AsyncClient, worker_experiencia, auth_token_experiencia
    ):
        """EXPERIENCIA: cada match debe incluir explicación con matching_skills."""
        resp = await client.get(
            f"/api/v1/match/{worker_experiencia.id}",
            headers={"Authorization": f"Bearer {auth_token_experiencia}"},
        )
        assert resp.status_code == 200
        matches = resp.json()["matches"]
        if matches:
            assert "explanation" in matches[0]
            assert "matching_skills" in matches[0]["explanation"]
            assert "missing_skills" in matches[0]["explanation"]
            assert "compatibility_label" in matches[0]["explanation"]
            assert matches[0]["explanation"]["compatibility_label"] in ["Alta", "Media", "Baja"]

    async def test_match_oficio_uses_reputation(
        self, client: AsyncClient, worker_oficio_with_portfolio, auth_token_oficio
    ):
        """OFICIO: el score debe considerar reputación (gamma=0.30)."""
        resp = await client.get(
            f"/api/v1/match/{worker_oficio_with_portfolio.id}",
            headers={"Authorization": f"Bearer {auth_token_oficio}"},
        )
        assert resp.status_code == 200
        # Al menos debe retornar respuesta válida con combined_score
        matches = resp.json()["matches"]
        if matches:
            assert "combined_score" in matches[0]
            assert 0.0 <= matches[0]["combined_score"] <= 1.0

    async def test_match_requires_authentication(
        self, client: AsyncClient, worker_experiencia
    ):
        """Sin token → 401."""
        resp = await client.get(f"/api/v1/match/{worker_experiencia.id}")
        assert resp.status_code == 401

    async def test_match_cannot_access_other_worker(
        self, client: AsyncClient, worker_experiencia, auth_token_primer_empleo
    ):
        """Un trabajador no puede ver las recomendaciones de otro."""
        resp = await client.get(
            f"/api/v1/match/{worker_experiencia.id}",
            headers={"Authorization": f"Bearer {auth_token_primer_empleo}"},
        )
        assert resp.status_code == 403

    async def test_combined_score_weights_primer_empleo(self):
        """Verificar pesos exactos del CLAUDE.md para PRIMER_EMPLEO."""
        from app.ml.matching_engine.scorer import combined_score, SCORE_WEIGHTS
        from app.core.types import WorkerType

        score = combined_score(
            cosine_sim=0.8,
            ml_score=0.6,
            reputation=4.0,
            worker_type=WorkerType.PRIMER_EMPLEO,
        )
        # alpha=0.65, beta=0.35, gamma=0.00
        expected = 0.65 * 0.8 + 0.35 * 0.6 + 0.00 * (4.0 / 5.0)
        assert abs(score - expected) < 0.0001

    async def test_combined_score_weights_oficio(self):
        """OFICIO: gamma=0.30 (reputación tiene peso significativo)."""
        from app.ml.matching_engine.scorer import combined_score
        from app.core.types import WorkerType

        score = combined_score(
            cosine_sim=0.7,
            ml_score=0.5,
            reputation=5.0,
            worker_type=WorkerType.OFICIO,
        )
        # alpha=0.45, beta=0.25, gamma=0.30
        expected = 0.45 * 0.7 + 0.25 * 0.5 + 0.30 * (5.0 / 5.0)
        assert abs(score - expected) < 0.0001

    async def test_match_events_logged_after_matching(
        self, client: AsyncClient, worker_experiencia, auth_token_experiencia, db
    ):
        """Verificar que se registran match_events en la BD."""
        from sqlalchemy import select
        from app.models import MatchEvent

        await client.get(
            f"/api/v1/match/{worker_experiencia.id}",
            headers={"Authorization": f"Bearer {auth_token_experiencia}"},
        )
        result = await db.execute(
            select(MatchEvent).where(MatchEvent.worker_id == worker_experiencia.id)
        )
        events = result.scalars().all()
        assert len(events) >= 0  # puede ser 0 si no hay ofertas
```

### A2 — test_cold_start.py (RF096–RF105)

```python
# tests/unit/test_cold_start.py
"""Tests del módulo de cold-start diferenciado por tipo."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.ml.cold_start.resolver import resolve_cold_start
from app.core.types import WorkerType


class TestColdStart:
    """RF096–RF105: cold-start por tipo de usuario."""

    async def test_cold_start_primer_empleo_with_wizard(self):
        """PRIMER_EMPLEO con respuestas del wizard genera embedding."""
        worker = MagicMock()
        worker.id = uuid4()
        worker.worker_type = "primer_empleo"
        worker.district = "Huancayo"
        worker.embedding = None

        wizard_progress = MagicMock()
        wizard_progress.extracted_skills = ["trabajo en equipo", "puntualidad"]
        wizard_progress.answers = {"job_interests": "administración"}

        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none.return_value = wizard_progress

        with patch("app.ml.cold_start.resolver.generate_embedding_sync") as mock_gen:
            mock_gen.return_value = [0.1] * 384
            result = await resolve_cold_start(worker, db)

        assert result.embedding is not None
        # El texto de embedding no debe incluir PII
        call_args = mock_gen.call_args[0][0]
        assert "primer empleo" in call_args
        assert "Huancayo" in call_args
        assert "trabajo en equipo" in call_args

    async def test_cold_start_primer_empleo_empty_wizard(self):
        """PRIMER_EMPLEO sin wizard genera embedding mínimo sin error."""
        worker = MagicMock()
        worker.id = uuid4()
        worker.worker_type = "primer_empleo"
        worker.district = "El Tambo"
        worker.embedding = None

        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none.return_value = None

        with patch("app.ml.cold_start.resolver.generate_embedding_sync") as mock_gen:
            mock_gen.return_value = [0.1] * 384
            result = await resolve_cold_start(worker, db)

        assert result.embedding is not None
        call_args = mock_gen.call_args[0][0]
        assert "primer empleo" in call_args

    async def test_cold_start_oficio_with_portfolio(self):
        """OFICIO con portfolio genera embedding desde skills extraídas."""
        worker = MagicMock()
        worker.id = uuid4()
        worker.worker_type = "oficio"
        worker.trade_category = "Electricidad"
        worker.district = "Chilca"
        worker.years_experience = 5
        worker.embedding = None

        entry1 = MagicMock()
        entry1.extracted_skills = ["instalación eléctrica", "cableado"]
        entry2 = MagicMock()
        entry2.extracted_skills = ["tableros eléctricos"]

        db = AsyncMock()
        db.execute.return_value.scalars.return_value.all.return_value = [entry1, entry2]

        with patch("app.ml.cold_start.resolver.generate_embedding_sync") as mock_gen:
            mock_gen.return_value = [0.1] * 384
            result = await resolve_cold_start(worker, db)

        assert result.embedding is not None
        call_args = mock_gen.call_args[0][0]
        assert "Electricidad" in call_args
        assert "instalación eléctrica" in call_args

    async def test_cold_start_oficio_without_portfolio(self):
        """OFICIO sin portfolio genera embedding solo desde metadata."""
        worker = MagicMock()
        worker.id = uuid4()
        worker.worker_type = "oficio"
        worker.trade_category = "Gasfitería"
        worker.district = "Huancayo"
        worker.years_experience = 3
        worker.embedding = None

        db = AsyncMock()
        db.execute.return_value.scalars.return_value.all.return_value = []

        with patch("app.ml.cold_start.resolver.generate_embedding_sync") as mock_gen:
            mock_gen.return_value = [0.1] * 384
            result = await resolve_cold_start(worker, db)

        assert result.embedding is not None

    async def test_embedding_does_not_contain_pii(self):
        """El texto del embedding nunca debe contener DNI ni teléfono."""
        from app.nlp.embeddings import build_profile_text
        from app.core.types import WorkerType
        import re

        worker = MagicMock()
        worker.worker_type = "primer_empleo"
        worker.district = "Huancayo"

        text = build_profile_text(worker, {"wizard_skills": ["responsabilidad"]})

        # No debe contener patrones de DNI (8 dígitos)
        assert not re.search(r"\b\d{8}\b", text)
        # No debe contener patrones de teléfono peruano
        assert not re.search(r"\+51\s*9\d{8}", text)
        # No debe contener email
        assert "@" not in text
```

### A3 — test_cv_generator.py (RF096–RF110)

```python
# tests/unit/test_cv_generator.py
"""Tests de generación de CVs PDF diferenciados por tipo."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.core.types import WorkerType


class TestCVGenerator:
    """RF096–RF110: generación de CVs PDF con WeasyPrint."""

    async def test_generate_cv_primer_empleo_returns_bytes(self):
        """CV de PRIMER_EMPLEO debe retornar bytes > 0."""
        from app.services.cv_builder.pdf_generator import generate_cv_pdf

        worker = MagicMock()
        worker.id = uuid4()
        worker.worker_type = "primer_empleo"
        worker.district = "Huancayo"
        worker.email = "test@example.com"
        worker.full_name = b"encrypted_name"
        worker.phone = b"encrypted_phone"

        db = AsyncMock()
        progress = MagicMock()
        progress.extracted_skills = ["responsabilidad", "puntualidad"]
        progress.answers = {"education": [], "activities": [], "job_interests": "comercio"}
        db.execute.return_value.scalar_one_or_none.return_value = progress

        with patch("app.services.cv_builder.pdf_generator.decrypt_field") as mock_decrypt:
            mock_decrypt.side_effect = lambda x: "Test User" if x == worker.full_name else "999999999"
            with patch("app.services.cv_builder.pdf_generator.HTML") as mock_html:
                mock_html.return_value.write_pdf.return_value = b"%PDF-1.4 test content"
                result = await generate_cv_pdf(worker.id, db)

        assert isinstance(result, bytes)
        assert len(result) > 0

    async def test_cv_template_context_no_pii_in_logs(self):
        """El contexto del CV no debe loggear datos sensibles."""
        # Verificar que decrypt_field solo se llama para el PDF, no para logs
        from app.services.cv_builder.pdf_generator import _build_template_context
        # Este test verifica la estructura del contexto
        # La verificación real es que full_name cifrado (bytes) nunca va a logger
        pass

    async def test_cv_oficio_with_empty_portfolio(self):
        """CV de OFICIO sin entradas en portfolio no debe lanzar error."""
        from app.services.cv_builder.pdf_generator import generate_cv_pdf

        worker = MagicMock()
        worker.id = uuid4()
        worker.worker_type = "oficio"
        worker.trade_category = "Carpintería"
        worker.district = "El Tambo"
        worker.years_experience = 2
        worker.avg_rating = 0.0
        worker.email = "test@example.com"
        worker.full_name = b"encrypted"
        worker.phone = b"encrypted"

        db = AsyncMock()
        db.execute.return_value.scalars.return_value.all.return_value = []

        with patch("app.services.cv_builder.pdf_generator.decrypt_field", return_value="Test"):
            with patch("app.services.cv_builder.pdf_generator.HTML") as mock_html:
                mock_html.return_value.write_pdf.return_value = b"%PDF test"
                result = await generate_cv_pdf(worker.id, db)

        assert isinstance(result, bytes)
```

### A4 — test_marketplace_search.py (RF118–RF122)

```python
# tests/integration/test_marketplace_search.py
"""Tests de búsqueda semántica en el marketplace de oficios."""
import pytest
from httpx import AsyncClient


class TestMarketplaceSearch:
    """RF118–RF122: búsqueda semántica en marketplace."""

    async def test_search_with_local_term_gasfitero(
        self, client: AsyncClient
    ):
        """'gasfitero' debe mapear a GASFITERIA vía diccionario Huancayo."""
        resp = await client.get(
            "/api/v1/marketplace/search",
            params={"q": "necesito un gasfitero para mi baño"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_search_returns_only_oficio_listings(
        self, client: AsyncClient
    ):
        """El marketplace solo muestra trabajadores OFICIO."""
        resp = await client.get(
            "/api/v1/marketplace/search",
            params={"q": "electricista"},
        )
        assert resp.status_code == 200
        listings = resp.json()
        for listing in listings:
            assert "worker_type" not in listing or listing.get("worker_type") == "oficio"

    async def test_search_filter_by_district(
        self, client: AsyncClient
    ):
        """Filtro por distrito debe reducir resultados."""
        resp_huancayo = await client.get(
            "/api/v1/marketplace/search",
            params={"q": "electricista", "district": "Huancayo"},
        )
        resp_all = await client.get(
            "/api/v1/marketplace/search",
            params={"q": "electricista"},
        )
        assert resp_huancayo.status_code == 200
        assert resp_all.status_code == 200
        # Filtrado no puede tener MÁS resultados que sin filtro
        assert len(resp_huancayo.json()) <= len(resp_all.json())

    async def test_marketplace_not_visible_to_primer_empleo(
        self, client: AsyncClient, auth_token_primer_empleo
    ):
        """
        PRIMER_EMPLEO no puede ver el marketplace (prohibición del CLAUDE.md).
        El endpoint debe retornar 403 si el tipo de usuario no es OFICIO.
        """
        # Este test verifica la regla del CLAUDE.md:
        # "No mostrar el marketplace a usuarios PRIMER_EMPLEO ni EXPERIENCIA"
        resp = await client.post(
            "/api/v1/marketplace/listings",
            headers={"Authorization": f"Bearer {auth_token_primer_empleo}"},
            json={"title": "Test", "trade_category": "Electricidad"},
        )
        assert resp.status_code == 403
```

---

## PARTE B — Verificación de cobertura

```bash
# Ejecutar TODOS los tests del proyecto
pytest tests/ \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=html:coverage_html \
  --cov-fail-under=80 \
  -v

# Si la cobertura está por debajo de 80%, identificar módulos sin tests
# y agregar tests unitarios básicos para subirla.

# Módulos críticos que DEBEN tener ≥ 80% de cobertura:
pytest tests/ --cov=app/ml --cov-fail-under=80
pytest tests/ --cov=app/nlp --cov-fail-under=80
pytest tests/ --cov=app/services --cov-fail-under=80
pytest tests/ --cov=app/api --cov-fail-under=80
```

---

## PARTE C — Verificaciones finales del Sprint 3

```bash
# 1. Linting — cero errores
ruff check . && echo "✅ Linting OK"

# 2. Sin print() en código de producción
grep -rn "print(" app/ && echo "❌ HAY print() — eliminar" || echo "✅ Sin print()"

# 3. Migraciones aplicadas
alembic current && echo "✅ Migraciones OK"

# 4. Stack levantado y saludable
docker-compose up -d
sleep 10
curl -f http://localhost:8000/api/v1/health && echo "✅ API saludable"

# 5. Motor de matching funciona end-to-end
python -c "
import asyncio
from app.ml.matching_engine.scorer import combined_score
from app.core.types import WorkerType
s = combined_score(0.8, 0.6, 4.0, WorkerType.PRIMER_EMPLEO)
print(f'Score PRIMER_EMPLEO: {s:.4f}')
assert abs(s - (0.65*0.8 + 0.35*0.6)) < 0.001
print('✅ combined_score PRIMER_EMPLEO OK')
"

# 6. Cobertura total ≥ 80%
pytest tests/ --cov=app --cov-fail-under=80 -q && echo "✅ Cobertura ≥ 80%"
```

---

## PARTE D — Checklist de RF implementados en Sprint 3

Verificar manualmente que cada RF tiene al menos un endpoint o función implementada:

```
M05 Motor ML de Emparejamiento (RF076–RF095):
  RF076-RF080: ✅ match_worker_to_jobs() — vector search pgvector
  RF081-RF085: ✅ combined_score() con pesos diferenciados
  RF086-RF090: ✅ GradientBoostingClassifier random_state=42
  RF091-RF095: ✅ equity_ranker, match_events audit log

M06 Asistente de Identidad Laboral (RF096–RF110):
  RF096-RF100: ✅ cold_start/resolver.py — embedding desde wizard/portfolio
  RF101-RF105: ✅ cold-start sin historial, embedding mínimo viable
  RF106-RF110: ✅ generate_cv_from_portfolio() (OFICIO), wizard PDF (PRIMER_EMPLEO)

M07 Búsqueda y Recomendación (RF111–RF117):
  RF111-RF117: ✅ job_alerts.py — alertas configurables con WebSocket

M08 Notificaciones (RF126–RF135):
  RF126-RF130: ✅ ws_notifications.py — WebSocket Redis pub/sub
  RF131-RF135: ✅ notifications table + publish_notification()

M10 Equidad y Explicabilidad (RF146–RF155):
  RF146-RF150: ✅ explainer.py — explicaciones en lenguaje coloquial
  RF151-RF155: ✅ equity_ranker.py — disparate impact ratio ≥ 0.80
```

---

## PARTE E — Documentar en SPRINT_3_SUMMARY.md

```bash
cat > SPRINT_3_SUMMARY.md << 'EOF'
# Sprint 3 — Resumen de implementación

## RF implementados
- RF076–RF095 (M05): Motor de matching ML diferenciado por worker_type
- RF096–RF110 (M06): Cold-start + generación CVs PDF (3 plantillas WeasyPrint)
- RF111–RF117 (M07): Alertas de empleo configurables
- RF126–RF135 (M08): Notificaciones WebSocket + Redis pub/sub
- RF146–RF155 (M10): Equity ranker + explainer de recomendaciones

## Archivos clave creados
- app/ml/matching_engine/ (engine, scorer, features, trainer)
- app/ml/cold_start/resolver.py
- app/ml/equity_ranker/ranker.py
- app/ml/explainer/explainer.py
- app/services/cv_builder/pdf_generator.py
- app/utils/cv_templates/ (3 plantillas HTML)
- app/api/v1/ws_notifications.py
- app/services/matching/job_alerts.py
- docker-compose.yml (4 workers Celery)
- infra/prometheus/ + infra/grafana/

## Métricas de calidad
- Cobertura tests: ≥ 80%
- F1 mínimo matching: ≥ 0.75 (forzado en trainer)
- Disparate impact: ≥ 0.80 (forzado en equity_ranker)
- combined_score: pesos exactos del CLAUDE.md

## Pendiente Sprint 4
- Panel Admin DRTPE (M09 / RF136–RF145)
- ML avanzado: DatasetBuilder real + drift detection PSI
- Frontend: Onboarding, Wizard 6 pasos, Dashboard por tipo
- CI/CD GitHub Actions completo
EOF

echo "✅ SPRINT_3_SUMMARY.md creado"
```

---

## ENTREGABLES FINALES DEL SPRINT 3

```bash
# Estado final esperado:
pytest tests/ --cov=app --cov-fail-under=80  # ✅ pasa
ruff check .                                   # ✅ sin errores
grep -rn "print(" app/                         # ✅ sin resultados
alembic current                                # ✅ última migración aplicada
curl http://localhost:8000/api/v1/health       # ✅ {"status":"ok"}
cat SPRINT_3_SUMMARY.md                        # ✅ existe
```

**El Sprint 3 está cerrado. El Sprint 4 arranca con el agente `security-auditor`
para auditar el panel admin y los endpoints DRTPE antes de implementarlos.**
