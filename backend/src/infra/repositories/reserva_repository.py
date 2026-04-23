from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from sqlalchemy import and_, func, select as nselect

from backend.src.domain.models.reserva import Reserva, StatusReserva
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
            reserva_orm.data_entrada = reserva.data_entrada
            reserva_orm.data_saida = reserva.data_saida

        await self.session.commit()
        if reserva.id is None:
            reserva.id = reserva_orm.id
        return reserva

    async def buscar_por_id(self, reserva_id: int) -> Optional[Reserva]:
        stmt = select(ReservaORM).where(ReservaORM.id == reserva_id)
        resultado = await self.session.execute(stmt)
        reserva_orm = resultado.scalar_one_or_none()
        return reserva_orm.to_domain() if reserva_orm else None


    async def listar(
        self,
        cliente_id: Optional[int] = None,
        status: Optional[StatusReserva] = None,
        data_entrada: Optional[date] = None,
        data_saida: Optional[date] = None,
    ) -> List[Reserva]:
        stmt = select(ReservaORM)
        if cliente_id is not None:
            stmt = stmt.where(ReservaORM.cliente_id == cliente_id)
        if status is not None:
            stmt = stmt.where(ReservaORM.status == status)
        if data_entrada is not None:
            stmt = stmt.where(ReservaORM.data_entrada >= data_entrada)
        if data_saida is not None:
            stmt = stmt.where(ReservaORM.data_saida <= data_saida)
        resultado = await self.session.execute(stmt)
        return [orm.to_domain() for orm in resultado.scalars().all()]

    async def deletar(self, reserva_id: int) -> None:
        stmt = select(ReservaORM).where(ReservaORM.id == reserva_id)
        orm_obj = (await self.session.execute(stmt)).scalar_one_or_none()
        if orm_obj:
            await self.session.delete(orm_obj)
            await self.session.commit()

    async def contar_reservas_conflitantes(self, tipo_quarto_id: int, entrada: date, saida: date) -> int:
        """Busca no banco quantas reservas já existem nesse período para esse tipo de quarto."""
        stmt = nselect(func.count(ReservaORM.id)).where(
            and_(
                ReservaORM.tipo_quarto_id == tipo_quarto_id,
                ReservaORM.status == StatusReserva.CONFIRMADA,
                # Sobreposição de datas: entrada < saida_existente AND saida > entrada_existente
                ReservaORM.data_entrada < saida,
                ReservaORM.data_saida > entrada
            )
        )
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one()