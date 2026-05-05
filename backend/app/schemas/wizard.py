# RF: RF096-RF100
from pydantic import BaseModel, Field


class WizardStepRequest(BaseModel):
    step: int = Field(..., ge=1, le=6)
    data: dict


class WizardStepResponse(BaseModel):
    current_step: int
    is_complete: bool
    extracted_skills: list[str]
    next_step_hint: str


STEP_HINTS = {
    1: "Completa tus datos personales (nombre, distrito, foto).",
    2: "Ingresa tu informacion educativa (colegio, instituto o universidad).",
    3: "Cuéntanos tus habilidades: ¿qué haces bien? ¿eres puntual, responsable?",
    4: "Describe actividades previas: voluntariado, proyectos escolares, ayuda familiar.",
    5: "Elige tus intereses laborales para recibir recomendaciones.",
    6: "Revisa tu CV generado y descargalo en PDF.",
}
