from decimal import Decimal
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

ValorMonetario = Annotated[Decimal, Field(ge=0, decimal_places=2)]

class ItemConsumoCriarInput(BaseModel):
    hospedagem_id: int = Field(..., description="ID da Hospedagem ativa")
    descricao: str = Field(..., min_length=2, description="Ex: Coca-Cola Lata")
    quantidade: int = Field(..., gt=0)
    valor_unitario: ValorMonetario

class ItemConsumoOutput(BaseModel):
    id: int
    hospedagem_id: int
    descricao: str
    quantidade: int
    valor_unitario: Decimal
    data_registro: datetime
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)