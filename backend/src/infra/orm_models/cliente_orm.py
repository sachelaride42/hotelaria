from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from typing import Optional
from backend.src.infra.database import Base
from backend.src.domain.models.cliente import Cliente


class ClienteORM(Base):
    """Mapeamento da tabela de clientes no banco de dados."""
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    nome: Mapped[str] = mapped_column(String(150), nullable=False)

    # Telefone é obrigatório (nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)

    # CPF é opcional (nullable=True), mas continua único se for preenchido
    cpf: Mapped[Optional[str]] = mapped_column(String(14), unique=True, nullable=True)

    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def to_domain(self) -> Cliente:
        """Converte o registro do banco para a Entidade pura."""
        return Cliente(
            id=self.id,
            nome=self.nome,
            telefone=self.telefone,
            cpf=self.cpf,
            email=self.email
        )