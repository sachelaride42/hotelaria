from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, Integer
from decimal import Decimal
from backend.src.infra.database import Base
from backend.src.domain.models.tipo_quarto import TipoDeQuarto

class TipoDeQuartoORM(Base):
    __tablename__ = "tipos_quarto"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=True)
    precoBaseDiaria: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False)

    def to_domain(self) -> TipoDeQuarto:
        return TipoDeQuarto(
            id=self.id,
            nome=self.nome,
            descricao=self.descricao,
            precoBaseDiaria=self.precoBaseDiaria,
            capacidade=self.capacidade
        )