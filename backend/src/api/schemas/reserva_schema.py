from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, condecimal, ConfigDict
from datetime import date, datetime
from backend.src.domain.models.reserva import StatusReserva

ValorMonetario = Annotated[Decimal, Field(ge=0, decimal_places=2)]


class ReservaCriarInput(BaseModel):
    cliente_id: int = Field(..., description="ID do Cliente")
    tipo_quarto_id: int = Field(..., description="ID da Categoria do Quarto (Simples, Suíte, etc)")
    data_entrada: date = Field(..., description="Data prevista de chegada")
    data_saida: date = Field(..., description="Data prevista de saída")

class ReservaOutput(BaseModel):
    id: int
    cliente_id: int
    tipo_quarto_id: int
    data_entrada: date
    data_saida: date
    data_criacao: datetime
    valor_total_previsto: ValorMonetario
    status: StatusReserva

    model_config = ConfigDict(from_attributes=True)