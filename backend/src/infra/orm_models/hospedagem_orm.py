from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, Numeric, Enum as SQLEnum, ForeignKey
from datetime import datetime
from decimal import Decimal
from typing import Optional

from backend.src.infra.database import Base
from backend.src.domain.models.hospedagem import Hospedagem, StatusHospedagem


class HospedagemORM(Base):
    """Mapeamento da tabela de hospedagens (Check-ins ativos e finalizados)."""
    __tablename__ = "hospedagens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Relacoes com os outros Agregados
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    quarto_id: Mapped[int] = mapped_column(ForeignKey("quartos.id"), nullable=False)
    reserva_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reservas.id"), nullable=True)

    # Tempos
    data_checkin: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_checkout_previsto: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_checkout_real: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Valores e Estado
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    valor_diaria_negociado: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[StatusHospedagem] = mapped_column(SQLEnum(StatusHospedagem), default=StatusHospedagem.ATIVA,
                                                     nullable=False)

    def to_domain(self) -> Hospedagem:
        return Hospedagem(
            id=self.id,
            cliente_id=self.cliente_id,
            quarto_id=self.quarto_id,
            reserva_id=self.reserva_id,
            data_checkin=self.data_checkin,
            data_checkout_previsto=self.data_checkout_previsto,
            data_checkout_real=self.data_checkout_real,
            valor_total=self.valor_total,
            valor_diaria_negociado=self.valor_diaria_negociado,
            status=self.status
        )