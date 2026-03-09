from dataclasses import dataclass
from typing import Optional


@dataclass
class Cliente:
    """
    Entidade de Domínio representando um Hóspede/Cliente.
    """
    nome: str
    telefone: str
    cpf: Optional[str] = None
    email: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Validação básica de domínio (Invariantes)"""
        if not self.nome or not self.nome.strip():
            raise ValueError("O campo 'Nome' é obrigatório.")

        if not self.telefone or not self.telefone.strip():
            raise ValueError("O campo 'Telefone' é obrigatório")

        if self.cpf:
            self._validar_cpf(self.cpf)

    def _validar_cpf(self, cpf: str):
        cpf = cpf.replace(".", "").replace("-", "")
        if not cpf.isdigit() or len(cpf) != 11:
            raise ValueError("CPF inválido.")
