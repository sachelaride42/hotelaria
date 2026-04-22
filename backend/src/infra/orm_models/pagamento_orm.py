from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Numeric, DateTime, Enum as SQLEnum, ForeignKey
from datetime import datetime
from decimal import Decimal

from backend.src.infra.database import Base
from backend.src.domain.models.pagamento import Pagamento, FormaDePagamento


class PagamentoORM(Base):
    __tablename__ = "pagamentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hospedagem_id: Mapped[int] = mapped_column(ForeignKey("hospedagens.id"), nullable=False)
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    forma_pagamento: Mapped[FormaDePagamento] = mapped_column(SQLEnum(FormaDePagamento), nullable=False)
    data_hora_pagamento: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def to_domain(self) -> Pagamento:
        return Pagamento(
            id=self.id,
            hospedagem_id=self.hospedagem_id,
            valor_pago=self.valor_pago,
            forma_pagamento=self.forma_pagamento,
            data_hora_pagamento=self.data_hora_pagamento,
        )
