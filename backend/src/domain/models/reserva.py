from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional
from decimal import Decimal


class StatusReserva(str, Enum):
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    LISTA_ESPERA = "LISTA_ESPERA"
    UTILIZADA = "UTILIZADA"  # Quando o check-in é efetuado


@dataclass
class Reserva:
    """
    Entidade de Domínio representando uma intenção de estadia.
    Relaciona um Cliente a um Tipo de Quarto (não a um quarto físico).
    """
    cliente_id: int
    tipo_quarto_id: int
    data_entrada: date
    data_saida: date
    valor_total_previsto: Decimal = Decimal("0.00")
    status: StatusReserva = StatusReserva.CONFIRMADA
    data_criacao: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None

    def __post_init__(self):
        """Invariantes: Validações de regra de negócio que impedem estado inválido"""
        # Exceção E2 do UC1: Data de saída anterior à de entrada
        if self.data_saida <= self.data_entrada:
            raise ValueError("A data de saída não pode ser anterior ou igual à data de entrada.")

    def cancelar(self):
        if self.status == StatusReserva.UTILIZADA:
            raise ValueError("Não é possível cancelar uma reserva que já realizou check-in.")
        self.status = StatusReserva.CANCELADA