from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.models.pagamento import Pagamento
from backend.src.infra.orm_models.pagamento_orm import PagamentoORM


class PagamentoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def salvar(self, pagamento: Pagamento) -> Pagamento:
        orm = PagamentoORM(
            hospedagem_id=pagamento.hospedagem_id,
            valor_pago=pagamento.valor_pago,
            forma_pagamento=pagamento.forma_pagamento,
            data_hora_pagamento=pagamento.data_hora_pagamento,
        )
        self.session.add(orm)
        await self.session.commit()
        pagamento.id = orm.id
        return pagamento

    async def listar_por_hospedagem(self, hospedagem_id: int) -> List[Pagamento]:
        stmt = select(PagamentoORM).where(PagamentoORM.hospedagem_id == hospedagem_id)
        resultado = await self.session.execute(stmt)
        return [p.to_domain() for p in resultado.scalars().all()]

    async def somar_total_pago(self, hospedagem_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(PagamentoORM.valor_pago), 0)).where(
            PagamentoORM.hospedagem_id == hospedagem_id
        )
        resultado = await self.session.execute(stmt)
        return Decimal(str(resultado.scalar()))

    async def buscar_por_id(self, pagamento_id: int) -> Optional[Pagamento]:
        stmt = select(PagamentoORM).where(PagamentoORM.id == pagamento_id)
        resultado = await self.session.execute(stmt)
        orm = resultado.scalar_one_or_none()
        return orm.to_domain() if orm else None

    async def deletar(self, pagamento_id: int) -> None:
        stmt = select(PagamentoORM).where(PagamentoORM.id == pagamento_id)
        orm = (await self.session.execute(stmt)).scalar_one_or_none()
        if orm:
            await self.session.delete(orm)
            await self.session.commit()
