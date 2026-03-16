from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class TipoDeQuarto:
    nome: str
    precoBaseDiaria: Decimal
    capacidade: int
    descricao: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self):
        if self.precoBaseDiaria <= 0:
            raise ValueError("O preço base da diária deve ser maior que zero.")
        if self.capacidade <= 0:
            raise ValueError("A capacidade do quarto deve ser de pelo menos 1 pessoa.")