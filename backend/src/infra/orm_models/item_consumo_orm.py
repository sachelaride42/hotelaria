from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Numeric, DateTime, ForeignKey
from datetime import datetime
from decimal import Decimal

from backend.src.infra.database import Base
from backend.src.domain.models.item_consumo import ItemConsumo


class ItemConsumoORM(Base):
    __tablename__ = "itens_consumo"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Chave estrangeira que liga este consumo à estadia ativa
    hospedagem_id: Mapped[int] = mapped_column(ForeignKey("hospedagens.id"), nullable=False)

    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    data_registro: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def to_domain(self) -> ItemConsumo:
        return ItemConsumo(
            id=self.id,
            hospedagem_id=self.hospedagem_id,
            descricao=self.descricao,
            quantidade=self.quantidade,
            valor_unitario=self.valor_unitario,
            data_registro=self.data_registro
        )