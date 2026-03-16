from dataclasses import dataclass
from enum import Enum
from typing import Optional


# Definidos os estados possíveis baseados nas regras de negócio e governança
class StatusQuarto(str, Enum):
    LIVRE = "LIVRE"
    OCUPADO = "OCUPADO"
    SUJO = "SUJO"
    MANUTENCAO = "MANUTENCAO"


@dataclass
class Quarto:

    #Entidade de Domínio representando um Quarto do hotel.

    numero: str
    andar: int
    tipo_quarto_id: int
    status: StatusQuarto = StatusQuarto.LIVRE

    # Controle de concorrência (Optimistic Locking)
    versao: int = 1

    # O ID é opcional na criação, pois só é gerado após salvar no banco
    id: Optional[int] = None

    def atualizarStatus(self, novoStatus: StatusQuarto):
        # Primeira regra: Um quarto sujo não pode ir direto para ocupado
        if self.status == StatusQuarto.SUJO and novoStatus == StatusQuarto.OCUPADO:
            raise ValueError("Quarto precisa ser limpo antes de ser ocupado.")
        elif novoStatus == StatusQuarto.OCUPADO and self.status != StatusQuarto.LIVRE:
            raise ValueError(f"O quarto {self.numero} não pode ser ocupado pois está {self.status.value}.")
        self.status = novoStatus