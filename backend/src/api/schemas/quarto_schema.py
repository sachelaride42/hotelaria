from pydantic import BaseModel, ConfigDict, Field
from backend.src.domain.models.quarto import StatusQuarto


class QuartoCriarInput(BaseModel):
    #O que esperamos receber do Frontend (React/Vue) para criar um quarto
    numero: str = Field(..., min_length=1, max_length=10, description="Número identificador, ex: 101A")
    andar: int = Field(..., gt=0, description="Andar do quarto")
    tipo_quarto_id: int = Field(..., gt=0, description="ID do tipo de quarto associado")


class QuartoAtualizarStatusInput(BaseModel):
    #Payload para quando a Governanta ou Recepção alterar o status
    status: StatusQuarto
    versao: int = Field(..., description="Versão atual em posse do frontend (Optimistic Locking)")


class QuartoOutput(BaseModel):
    #Como devolvemos o quarto para o Frontend
    id: int
    numero: str
    andar: int
    tipo_quarto_id: int
    status: StatusQuarto
    versao: int

    model_config = ConfigDict(from_attributes=True)