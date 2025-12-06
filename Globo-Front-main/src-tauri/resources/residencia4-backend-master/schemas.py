from pydantic import BaseModel
from enum import Enum

class StatusEnum(str, Enum):
    aprovado = "Aprovado"
    rejeitado = "Rejeitado"

class StatusUpdate(BaseModel):
    status: StatusEnum