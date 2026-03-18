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

    # Se originada de uma reserva, guardamos o vínculo. Se for "Walk-in" (balcão), fica None.
    reserva_id: Optional[int] = None

    # O momento exato em que a pessoa pegou a chave
    data_checkin: datetime = field(default_factory=datetime.now)

    # Só é preenchido no momento do check-out (UC5)
    data_checkout_real: Optional[datetime] = None
    valor_total: Decimal = Decimal("0.00")

    status: StatusHospedagem = StatusHospedagem.ATIVA
    id: Optional[int] = None

    def __post_init__(self):
        """Invariantes de Domínio"""
        # A data prevista de saída não pode ser no passado em relação ao check-in
        if self.data_checkout_previsto <= self.data_checkin:
            raise ValueError("A data de checkout previsto deve ser posterior ao check-in.")

    def realizar_checkout(self, data_saida: datetime, valor_calculado: Decimal):
        """
        Encapsula a transição de estado do Check-out.
        Garante que a hospedagem seja fechada corretamente com o valor final cobrado.
        """
        if self.status != StatusHospedagem.ATIVA:
            raise ValueError(f"Não é possível fazer check-out de uma hospedagem {self.status.value}.")

        if data_saida < self.data_checkin:
            raise ValueError("A data de checkout real não pode ser anterior ao check-in.")

        self.data_checkout_real = data_saida
        self.valor_total = valor_calculado
        self.status = StatusHospedagem.FINALIZADA