from pydantic import BaseModel, ConfigDict, Field
from backend.src.domain.models.quarto import StatusOcupacao, StatusLimpeza


class QuartoCriarInput(BaseModel):
    """Schema de entrada para criação de quarto."""
    numero: str = Field(..., min_length=1, max_length=10, description="Número identificador, ex: 101A")
    andar: int = Field(..., gt=0, description="Andar do quarto")
    tipo_quarto_id: int = Field(..., gt=0, description="ID do tipo de quarto associado")


class QuartoAtualizarDadosInput(BaseModel):
    numero: str = Field(..., min_length=1, max_length=10, description="Número identificador, ex: 101A")
    andar: int = Field(..., gt=0, description="Andar do quarto")
    tipo_quarto_id: int = Field(..., gt=0, description="ID do tipo de quarto associado")


class QuartoAtualizarStatusOcupacaoInput(BaseModel):
    """Schema de entrada para alteração do status de ocupação."""
    status_ocupacao: StatusOcupacao
    versao: int = Field(..., description="Versão atual em posse do frontend (Optimistic Locking)")


class QuartoAtualizarStatusLimpezaInput(BaseModel):
    """Schema de entrada para alteração do status de limpeza."""
    status_limpeza: StatusLimpeza
    versao: int = Field(..., description="Versão atual em posse do frontend (Optimistic Locking)")


class QuartoOutput(BaseModel):
    """Schema de saída para quarto."""
    id: int
    numero: str
    andar: int
    tipo_quarto_id: int
    status_ocupacao: StatusOcupacao
    status_limpeza: StatusLimpeza
    versao: int

    model_config = ConfigDict(from_attributes=True)