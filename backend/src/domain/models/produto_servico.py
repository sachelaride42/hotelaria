from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from enum import Enum

class CategoriaItem(str, Enum):
    PRODUTO = "PRODUTO" # Itens físicos (Refrigerante, Salgadinho)
    SERVICO = "SERVICO" # Ações (Lavanderia, Massagem, Taxa Pet)

@dataclass
class ProdutoServico:
    """
    Entidade de Catálogo. Representa os itens e serviços que o hotel oferece.
    """
    descricao: str
    preco_padrao: Decimal
    categoria: CategoriaItem
    id: Optional[int] = None

    def __post_init__(self):
        """Invariantes de Domínio"""
        if not self.descricao or not self.descricao.strip():
            raise ValueError("A descrição do produto/serviço é obrigatória.")
        if self.preco_padrao < 0:
            raise ValueError("O preço padrão não pode ser negativo.")