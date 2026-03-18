from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

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

    async def buscar_ativa_por_quarto(self, quarto_id: int) -> Optional[Hospedagem]:
        """Útil para encontrar quem está no quarto no momento do Check-out."""
        stmt = select(HospedagemORM).where(
            HospedagemORM.quarto_id == quarto_id,
            HospedagemORM.status == StatusHospedagem.ATIVA
        )
        resultado = await self.session.execute(stmt)
        orm = resultado.scalar_one_or_none()
        return orm.to_domain() if orm else None