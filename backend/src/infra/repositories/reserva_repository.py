from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List

from backend.src.domain.models.reserva import Reserva
from backend.src.infra.orm_models.reserva_orm import ReservaORM


class ReservaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def salvar(self, reserva: Reserva) -> Reserva:
        if reserva.id is None:
            reserva_orm = ReservaORM(
                cliente_id=reserva.cliente_id,
                tipo_quarto_id=reserva.tipo_quarto_id,
                data_entrada=reserva.data_entrada,
                data_saida=reserva.data_saida,
                valor_total_previsto=reserva.valor_total_previsto,
                status=reserva.status,
                data_criacao=reserva.data_criacao
            )
            self.session.add(reserva_orm)
        else:
            stmt = select(ReservaORM).where(ReservaORM.id == reserva.id)
            resultado = await self.session.execute(stmt)
            reserva_orm = resultado.scalar_one()

            reserva_orm.status = reserva.status
            reserva_orm.valor_total_previsto = reserva.valor_total_previsto

        await self.session.commit()
        if reserva.id is None:
            reserva.id = reserva_orm.id
        return reserva

    async def buscar_por_id(self, reserva_id: int) -> Optional[Reserva]:
        stmt = select(ReservaORM).where(ReservaORM.id == reserva_id)
        resultado = await self.session.execute(stmt)
        reserva_orm = resultado.scalar_one_or_none()
        return reserva_orm.to_domain() if reserva_orm else None