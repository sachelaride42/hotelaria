from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class StatusHospedagem(str, Enum):
    ATIVA = "ATIVA"  # Hóspede está no hotel agora
    FINALIZADA = "FINALIZADA"  # Check-out realizado e pago
    CANCELADA = "CANCELADA"  # Erro de lançamento ou desistência logo após entrar


@dataclass
class Hospedagem:
    """
    Entidade de Domínio representando a estadia real de um cliente em um quarto físico.
    """
    cliente_id: int
    quarto_id: int
    data_checkout_previsto: datetime

    # Vínculo com reserva; None em check-ins diretos (walk-in)
    reserva_id: Optional[int] = None

    data_checkin: datetime = field(default_factory=datetime.now)
    data_checkout_real: Optional[datetime] = None
    valor_total: Decimal = Decimal("0.00")
    valor_diaria_negociado: Optional[Decimal] = None

    status: StatusHospedagem = StatusHospedagem.ATIVA
    id: Optional[int] = None

    def __post_init__(self):
        """Valida invariantes de domínio na criação da hospedagem."""
        if self.data_checkout_previsto <= self.data_checkin:
            raise ValueError("A data de checkout previsto deve ser posterior ao check-in.")

    def realizar_checkout(self, data_saida: datetime, valor_calculado: Decimal):
        """Aplica a transição de estado do check-out, registrando data de saída e valor final."""
        if self.status != StatusHospedagem.ATIVA:
            raise ValueError(f"Não é possível fazer check-out de uma hospedagem {self.status.value}.")

        if data_saida < self.data_checkin:
            raise ValueError("A data de checkout real não pode ser anterior ao check-in.")

        self.data_checkout_real = data_saida
        self.valor_total = valor_calculado
        self.status = StatusHospedagem.FINALIZADA