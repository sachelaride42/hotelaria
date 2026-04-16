from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StatusOcupacao(str, Enum):
    LIVRE = "LIVRE"
    OCUPADO = "OCUPADO"
    MANUTENCAO = "MANUTENCAO"


class StatusLimpeza(str, Enum):
    LIMPO = "LIMPO"
    SUJO = "SUJO"


@dataclass
class Quarto:

    #Entidade de Domínio representando um Quarto do hotel.

    numero: str
    andar: int
    tipo_quarto_id: int
    status_ocupacao: StatusOcupacao = StatusOcupacao.LIVRE
    status_limpeza: StatusLimpeza = StatusLimpeza.LIMPO

    # Controle de concorrência (Optimistic Locking)
    versao: int = 1

    # O ID é opcional na criação, pois só é gerado após salvar no banco
    id: Optional[int] = None

    def atualizarStatusOcupacao(self, novo: StatusOcupacao):
        if novo == StatusOcupacao.OCUPADO:
            if self.status_ocupacao != StatusOcupacao.LIVRE:
                raise ValueError(f"O quarto {self.numero} não pode ser ocupado pois está {self.status_ocupacao.value}.")
            if self.status_limpeza == StatusLimpeza.SUJO:
                raise ValueError("Quarto precisa ser limpo antes de ser ocupado.")
        elif novo == StatusOcupacao.MANUTENCAO:
            if self.status_ocupacao == StatusOcupacao.OCUPADO:
                raise ValueError(f"O quarto {self.numero} está ocupado e não pode entrar em manutenção.")
        elif novo == StatusOcupacao.LIVRE and self.status_ocupacao == StatusOcupacao.OCUPADO:
            # Check-out: quarto recém desocupado fica sujo
            self.status_limpeza = StatusLimpeza.SUJO
        self.status_ocupacao = novo

    def atualizarStatusLimpeza(self, novo: StatusLimpeza):
        self.status_limpeza = novo