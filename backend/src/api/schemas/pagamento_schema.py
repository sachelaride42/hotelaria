from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal

from backend.src.domain.models.pagamento import FormaDePagamento


class PagamentoInput(BaseModel):
    hospedagem_id: int = Field(..., description="ID da hospedagem vinculada")
    valor_pago: Decimal = Field(..., gt=0, description="Valor pago nesta transação")
    forma_pagamento: FormaDePagamento = Field(..., description="Forma de pagamento utilizada")


class PagamentoOutput(BaseModel):
    id: int
    hospedagem_id: int
    valor_pago: Decimal
    forma_pagamento: FormaDePagamento
    data_hora_pagamento: datetime

    model_config = ConfigDict(from_attributes=True)
