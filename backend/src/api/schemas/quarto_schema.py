from pydantic import BaseModel, ConfigDict, Field
from backend.src.domain.models.quarto import StatusOcupacao, StatusLimpeza


class QuartoCriarInput(BaseModel):
    #O que esperamos receber do Frontend (React/Vue) para criar um quarto
    numero: str = Field(..., min_length=1, max_length=10, description="Número identificador, ex: 101A")
    andar: int = Field(..., gt=0, description="Andar do quarto")
    tipo_quarto_id: int = Field(..., gt=0, description="ID do tipo de quarto associado")


class QuartoAtualizarDadosInput(BaseModel):
    numero: str = Field(..., min_length=1, max_length=10, description="Número identificador, ex: 101A")
    andar: int = Field(..., gt=0, description="Andar do quarto")
    tipo_quarto_id: int = Field(..., gt=0, description="ID do tipo de quarto associado")


class QuartoAtualizarStatusOcupacaoInput(BaseModel):
    #Payload para a Recepção ou Manutenção alterar o status de ocupação
    status_ocupacao: StatusOcupacao
    versao: int = Field(..., description="Versão atual em posse do frontend (Optimistic Locking)")


class QuartoAtualizarStatusLimpezaInput(BaseModel):
    #Payload para a Governanta alterar o status de limpeza
    status_limpeza: StatusLimpeza
    versao: int = Field(..., description="Versão atual em posse do frontend (Optimistic Locking)")


class QuartoOutput(BaseModel):
    #Como devolvemos o quarto para o Frontend
    id: int
    numero: str
    andar: int
    tipo_quarto_id: int
    status_ocupacao: StatusOcupacao
    status_limpeza: StatusLimpeza
    versao: int

    model_config = ConfigDict(from_attributes=True)