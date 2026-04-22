from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class FormaDePagamento(str, Enum):
    DINHEIRO = "DINHEIRO"
    CARTAO_CREDITO = "CARTAO_CREDITO"
    CARTAO_DEBITO = "CARTAO_DEBITO"
    PIX = "PIX"
    BOLETO = "BOLETO"


@dataclass
class Pagamento:
    hospedagem_id: int
    valor_pago: Decimal
    forma_pagamento: FormaDePagamento
    data_hora_pagamento: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None

    def __post_init__(self):
        if self.valor_pago <= Decimal("0"):
            raise ValueError("O valor pago deve ser maior que zero.")
