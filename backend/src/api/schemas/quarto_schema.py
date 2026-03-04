from pydantic import BaseModel, Field
from backend.src.domain.models.quarto import StatusQuarto

#DTO - Data Transfer Object
class QuartoCriarInput(BaseModel):
    """O que esperamos receber do Frontend (React/Vue) para criar um quarto"""
    numero: str = Field(..., min_length=1, max_length=10, description="Número identificador, ex: 101A")
    andar: int = Field(..., gt=0, description="Andar do quarto")


class QuartoAtualizarStatusInput(BaseModel):
    """Payload para quando a Governanta ou Recepção alterar o status"""
    status: StatusQuarto
    versao: int = Field(..., description="Versão atual em posse do frontend (Optimistic Locking)")


class QuartoOutput(BaseModel):
    """Como devolvemos o quarto para o Frontend"""
    id: int
    numero: str
    andar: int
    status: StatusQuarto
    versao: int

    class Config:
        from_attributes = True  # Permite converter nossa Entidade Quarto para Pydantic facilmente