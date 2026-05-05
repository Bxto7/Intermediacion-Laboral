from enum import Enum

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class WorkerType(str, Enum):
    PRIMER_EMPLEO = "primer_empleo"
    EXPERIENCIA = "experiencia"
    OFICIO = "oficio"


class TradeCategory(str, Enum):
    ELECTRICIDAD = "Electricidad"
    GASFITERIA = "Gasfiteria"
    CARPINTERIA = "Carpinteria"
    ALBANILERIA = "Albanileria"
    PINTURA = "Pintura"
    MECANICA = "Mecanica automotriz"
    TECHADO = "Techado"
    SOLDADURA = "Soldadura y metalurgia"
    JARDINERIA = "Jardineria"
    LIMPIEZA = "Limpieza y mantenimiento"
    COCINA = "Cocina y pasteleria"
    COSTURA = "Costura y confeccion"
    OTROS = "Otros oficios"


class District(str, Enum):
    HUANCAYO = "Huancayo"
    EL_TAMBO = "El Tambo"
    CHILCA = "Chilca"
    OTRO = "Otro"


class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYER = "employer"
    WORKER = "worker"
    MODERATOR = "moderator"
