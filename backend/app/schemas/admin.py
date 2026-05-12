# RF: RF136-RF145 (M09) — Schemas del panel admin DRTPE
from pydantic import BaseModel, ConfigDict


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vil: dict   # Velocidad Inserción Laboral por worker_type
    ivp: dict   # Índice Visibilidad Perfil
    tf: dict    # Tasa Formalización
    rbs: dict   # Reducción Brecha Salarial
    tcc: dict   # Tasa Completitud CV
    ivm: dict   # Índice Visibilidad Marketplace (solo OFICIO)
    tcss: dict  # Tasa Cold-Start Superado
    calculated_at: str


class WorkerStatsResponse(BaseModel):
    stats: list[dict]
