# RF: RNF005 — Ley N° 29733 Protección de Datos Personales
from fastapi import HTTPException, status


def require_consent(consent_given: bool, data_purpose: str) -> None:
    """Verificar consentimiento informado antes de recolectar datos personales."""
    if not consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Se requiere consentimiento informado para {data_purpose}. "
                "Ley N° 29733 — Ley de Protección de Datos Personales del Perú."
            ),
        )
