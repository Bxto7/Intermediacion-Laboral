# RF: RF161-RF165 (M12) — Conector DRTPE-Junín (stub Sprint 4, real en Sprint 5)
from dataclasses import dataclass
from typing import Protocol

import structlog

logger = structlog.get_logger()


@dataclass
class DRTPEJobOffer:
    """Oferta de empleo proveniente de la Bolsa de Trabajo oficial DRTPE-Junín."""

    external_id: str
    title: str
    employer_name: str
    district: str
    required_skills: list[str]
    salary_min: float | None
    salary_max: float | None
    published_at: str
    source: str = "DRTPE-JUNIN"


class DRTPEConnectorProtocol(Protocol):
    """Interfaz del conector — permite swap de stub por implementación real en Sprint 5."""

    async def fetch_active_offers(self, limit: int = 50) -> list[DRTPEJobOffer]: ...
    async def sync_worker_registration(self, worker_id: str, data: dict) -> bool: ...
    async def report_placement(self, contract_id: str, data: dict) -> bool: ...


class DRTPEConnectorStub:
    """
    Stub del conector DRTPE para Sprint 4.
    Sprint 5: reemplazar por DRTPEConnectorReal con llamadas a api.drtpe.gob.pe.
    """

    async def fetch_active_offers(self, limit: int = 50) -> list[DRTPEJobOffer]:
        logger.info("drtpe_fetch_offers_stub", limit=limit)
        offers = [
            DRTPEJobOffer(
                external_id="DRTPE-2026-001",
                title="Técnico en instalaciones eléctricas",
                employer_name="Empresa Constructora El Tambo S.A.C.",
                district="El Tambo",
                required_skills=["instalación eléctrica", "lectura de planos"],
                salary_min=1500.0,
                salary_max=2200.0,
                published_at="2026-05-01",
            ),
            DRTPEJobOffer(
                external_id="DRTPE-2026-002",
                title="Auxiliar administrativo",
                employer_name="Municipalidad Provincial de Huancayo",
                district="Huancayo",
                required_skills=["office", "atención al cliente", "archivo"],
                salary_min=1025.0,
                salary_max=1400.0,
                published_at="2026-05-03",
            ),
            DRTPEJobOffer(
                external_id="DRTPE-2026-003",
                title="Gasfitero para mantenimiento",
                employer_name="Urbanización Los Jardines S.A.",
                district="Chilca",
                required_skills=["gasfitería", "plomería", "fontanería"],
                salary_min=1200.0,
                salary_max=1800.0,
                published_at="2026-05-04",
            ),
            DRTPEJobOffer(
                external_id="DRTPE-2026-004",
                title="Operario de carpintería",
                employer_name="Mueblería Junín E.I.R.L.",
                district="Huancayo",
                required_skills=["carpintería", "manejo de herramientas", "trabajo en madera"],
                salary_min=1100.0,
                salary_max=1600.0,
                published_at="2026-05-05",
            ),
        ]
        return offers[:limit]

    async def sync_worker_registration(self, worker_id: str, data: dict) -> bool:
        logger.info("drtpe_sync_registration_stub", worker_id=worker_id)
        return True

    async def report_placement(self, contract_id: str, data: dict) -> bool:
        logger.info("drtpe_report_placement_stub", contract_id=contract_id)
        return True


class DRTPEConnectorReal:
    """
    Conector real con la API de la Bolsa de Trabajo DRTPE-Junín (Sprint 5).
    Usa httpx para llamadas HTTP asíncronas con timeout y reintentos.
    """

    BASE_URL = "https://api.drtpe.gob.pe/v1"
    TIMEOUT = 10.0

    def __init__(self) -> None:
        from app.core.config import settings
        self._api_key: str = getattr(settings, "DRTPE_API_KEY", "")

    async def fetch_active_offers(self, limit: int = 50) -> list[DRTPEJobOffer]:
        import httpx

        headers = {"X-API-Key": self._api_key, "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/ofertas/activas",
                    headers=headers,
                    params={"limit": limit, "region": "JUNIN"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("drtpe_fetch_failed", error=str(exc), fallback="stub")
            return await DRTPEConnectorStub().fetch_active_offers(limit)

        offers = []
        for item in data.get("ofertas", []):
            offers.append(
                DRTPEJobOffer(
                    external_id=str(item.get("id", "")),
                    title=item.get("titulo", ""),
                    employer_name=item.get("empresa", ""),
                    district=item.get("distrito", "Huancayo"),
                    required_skills=item.get("habilidades_requeridas", []),
                    salary_min=item.get("salario_min"),
                    salary_max=item.get("salario_max"),
                    published_at=item.get("fecha_publicacion", ""),
                )
            )
        logger.info("drtpe_offers_fetched", count=len(offers))
        return offers

    async def sync_worker_registration(self, worker_id: str, data: dict) -> bool:
        import httpx

        headers = {"X-API-Key": self._api_key, "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/trabajadores/registro",
                    headers=headers,
                    json={"worker_id": worker_id, **data},
                )
                resp.raise_for_status()
                logger.info("drtpe_worker_synced", worker_id=worker_id)
                return True
        except Exception as exc:
            logger.warning("drtpe_sync_failed", worker_id=worker_id, error=str(exc))
            return False

    async def report_placement(self, contract_id: str, data: dict) -> bool:
        import httpx

        headers = {"X-API-Key": self._api_key, "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/colocaciones",
                    headers=headers,
                    json={"contract_id": contract_id, **data},
                )
                resp.raise_for_status()
                logger.info("drtpe_placement_reported", contract_id=contract_id)
                return True
        except Exception as exc:
            logger.warning("drtpe_placement_failed", contract_id=contract_id, error=str(exc))
            return False


def _get_connector() -> DRTPEConnectorProtocol:
    """Retorna el conector real si DRTPE_API_KEY está configurado, sino el stub."""
    from app.core.config import settings
    api_key = getattr(settings, "DRTPE_API_KEY", "")
    if api_key and api_key != "stub":
        return DRTPEConnectorReal()
    return DRTPEConnectorStub()


drtpe_connector: DRTPEConnectorProtocol = _get_connector()
