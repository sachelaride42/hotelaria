from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, Enum as SQLEnum
from decimal import Decimal

from backend.src.infra.database import Base
from backend.src.domain.models.produto_servico import ProdutoServico, CategoriaItem

class ProdutoServicoORM(Base):
    __tablename__ = "produtos_servicos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    descricao: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    preco_padrao: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    categoria: Mapped[CategoriaItem] = mapped_column(SQLEnum(CategoriaItem), nullable=False)

    def to_domain(self) -> ProdutoServico:
        return ProdutoServico(
            id=self.id,
            descricao=self.descricao,
            preco_padrao=self.preco_padrao,
            categoria=self.categoria
        )