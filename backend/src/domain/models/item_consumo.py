from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class ItemConsumo:
    """
    Entidade de Domínio que representa um produto ou serviço consumido
    durante a estadia (Hospedagem) do cliente.
    """
    hospedagem_id: int
    descricao: str  # Ex: "Água Mineral", "Menu Executivo"
    quantidade: int
    valor_unitario: Decimal

    data_registro: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None

    def __post_init__(self):
        """Invariantes: Impede a criação de um consumo com dados logicamente incorretos."""
        if self.quantidade <= 0:
            raise ValueError("A quantidade consumida deve ser maior que zero.")
        if self.valor_unitario < 0:
            raise ValueError("O valor unitário não pode ser negativo.")

    @property
    def subtotal(self) -> Decimal:
        """Calcula automaticamente o valor total desta linha de consumo."""
        return Decimal(self.quantidade) * self.valor_unitario