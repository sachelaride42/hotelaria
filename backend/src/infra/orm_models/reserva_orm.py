from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Date, DateTime, Numeric, String, Enum as SQLEnum, ForeignKey
from datetime import date, datetime
from decimal import Decimal

from backend.src.infra.database import Base
from backend.src.domain.models.reserva import Reserva, StatusReserva


class ReservaORM(Base):
    """Mapeamento da tabela de reservas."""
    __tablename__ = "reservas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Chaves estrangeiras conectando as entidades
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)

    tipo_quarto_id: Mapped[int] = mapped_column(Integer, nullable=False)

    data_entrada: Mapped[date] = mapped_column(Date, nullable=False)
    data_saida: Mapped[date] = mapped_column(Date, nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    valor_total_previsto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[StatusReserva] = mapped_column(SQLEnum(StatusReserva), default=StatusReserva.CONFIRMADA,
                                                  nullable=False)

    def to_domain(self) -> Reserva:
        return Reserva(
            id=self.id,
            cliente_id=self.cliente_id,
            tipo_quarto_id=self.tipo_quarto_id,
            data_entrada=self.data_entrada,
            data_saida=self.data_saida,
            valor_total_previsto=self.valor_total_previsto,
            status=self.status,
            data_criacao=self.data_criacao
        )