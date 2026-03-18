from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional
from backend.src.domain.models.hospedagem import StatusHospedagem

class HospedagemCheckinInput(BaseModel):
    """Payload para realizar o Check-in."""
    cliente_id: int = Field(..., description="ID do Cliente no balcão")
    quarto_id: int = Field(..., description="ID do Quarto físico escolhido")
    reserva_id: Optional[int] = Field(None, description="ID da Reserva, se existir")
    data_checkout_previsto: datetime = Field(..., description="Quando o hóspede planeia sair")
    # Para lidar com o Optimistic Locking do Quarto:
    versao_quarto: int = Field(..., description="Versão atual do quarto para evitar concorrência")

class HospedagemOutput(BaseModel):
    id: int
    cliente_id: int
    quarto_id: int
    reserva_id: Optional[int]
    data_checkin: datetime
    data_checkout_previsto: datetime
    data_checkout_real: Optional[datetime]
    valor_total: Decimal
    status: StatusHospedagem

    model_config = ConfigDict(from_attributes=True)

class HospedagemCheckoutInput(BaseModel):
    """Payload para realizar o Check-out."""
    versao_quarto: int = Field(..., description="Versão atual do quarto para evitar concorrência ao marcá-mo como SUJO")