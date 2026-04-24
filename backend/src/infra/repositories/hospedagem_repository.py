from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List

from backend.src.domain.models.hospedagem import Hospedagem, StatusHospedagem
from backend.src.infra.orm_models.hospedagem_orm import HospedagemORM


class HospedagemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def salvar(self, hospedagem: Hospedagem) -> Hospedagem:
        if hospedagem.id is None:
            hosp_orm = HospedagemORM(
                cliente_id=hospedagem.cliente_id,
                quarto_id=hospedagem.quarto_id,
                reserva_id=hospedagem.reserva_id,
                data_checkin=hospedagem.data_checkin,
                data_checkout_previsto=hospedagem.data_checkout_previsto,
                data_checkout_real=hospedagem.data_checkout_real,
                valor_total=hospedagem.valor_total,
                valor_diaria_negociado=hospedagem.valor_diaria_negociado,
                status=hospedagem.status
            )
            self.session.add(hosp_orm)
        else:
            stmt = select(HospedagemORM).where(HospedagemORM.id == hospedagem.id)
            hosp_orm = (await self.session.execute(stmt)).scalar_one()

            hosp_orm.data_checkout_real = hospedagem.data_checkout_real
            hosp_orm.valor_total = hospedagem.valor_total
            hosp_orm.status = hospedagem.status

        await self.session.commit()
        if hospedagem.id is None:
            hospedagem.id = hosp_orm.id
        return hospedagem

    async def buscar_por_id(self, hospedagem_id: int) -> Optional[Hospedagem]:
        stmt = select(HospedagemORM).where(HospedagemORM.id == hospedagem_id)
        resultado = await self.session.execute(stmt)
        orm = resultado.scalar_one_or_none()
        return orm.to_domain() if orm else None

    async def deletar(self, hospedagem_id: int) -> None:
        stmt = select(HospedagemORM).where(HospedagemORM.id == hospedagem_id)
        orm_obj = (await self.session.execute(stmt)).scalar_one_or_none()
        if orm_obj:
            await self.session.delete(orm_obj)
            await self.session.commit()

    async def listar(
        self,
        cliente_id: Optional[int] = None,
        status: Optional[StatusHospedagem] = None,
        quarto_id: Optional[int] = None,
    ) -> List[Hospedagem]:
        stmt = select(HospedagemORM)
        if cliente_id is not None:
            stmt = stmt.where(HospedagemORM.cliente_id == cliente_id)
        if status is not None:
            stmt = stmt.where(HospedagemORM.status == status)
        if quarto_id is not None:
            stmt = stmt.where(HospedagemORM.quarto_id == quarto_id)
        resultado = await self.session.execute(stmt)
        return [orm.to_domain() for orm in resultado.scalars().all()]

    async def buscar_ativa_por_quarto(self, quarto_id: int) -> Optional[Hospedagem]:
        """Retorna a hospedagem ativa de um quarto, ou None se não houver."""
        stmt = select(HospedagemORM).where(
            HospedagemORM.quarto_id == quarto_id,
            HospedagemORM.status == StatusHospedagem.ATIVA
        )
        resultado = await self.session.execute(stmt)
        orm = resultado.scalar_one_or_none()
        return orm.to_domain() if orm else None