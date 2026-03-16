from decimal import Decimal
from typing import Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict

PrecoValido = Annotated[Decimal, Field(gt=0, decimal_places=2)]

class TipoQuartoBase(BaseModel):
    nome: str = Field(..., description="Ex: Suíte Presidencial")
    descricao: Optional[str] = None
    precoBaseDiaria: PrecoValido
    capacidade: int = Field(..., gt=0)

class TipoQuartoOutput(TipoQuartoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)