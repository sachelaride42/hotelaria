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
    versao_quarto: int = Field(..., description="Versão atual do quarto para evitar concorrência")
    valor_diaria_negociado: Optional[Decimal] = Field(None, ge=0, description="Preço negociado da diária (sobrescreve o padrão do tipo de quarto)")

class HospedagemOutput(BaseModel):
    id: int
    cliente_id: int
    quarto_id: int
    reserva_id: Optional[int]
    data_checkin: datetime
    data_checkout_previsto: datetime
    data_checkout_real: Optional[datetime]
    valor_total: Decimal
    valor_diaria_negociado: Optional[Decimal]
    status: StatusHospedagem

    model_config = ConfigDict(from_attributes=True)

class HospedagemCheckoutInput(BaseModel):
    """Payload para realizar o Check-out."""
    versao_quarto: int = Field(..., description="Versão atual do quarto para evitar concorrência ao marcá-lo como SUJO")
    data_checkout_real: Optional[datetime] = Field(None, description="Horário real de saída (UC4a). Se omitido, usa datetime.now().")