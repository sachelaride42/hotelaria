from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from decimal import Decimal

from backend.src.domain.models.item_consumo import ItemConsumo
from backend.src.infra.orm_models.item_consumo_orm import ItemConsumoORM


class ItemConsumoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def salvar(self, item: ItemConsumo) -> ItemConsumo:
        if item.id is None:
            item_orm = ItemConsumoORM(
                hospedagem_id=item.hospedagem_id,
                descricao=item.descricao,
                quantidade=item.quantidade,
                valor_unitario=item.valor_unitario,
                data_registro=item.data_registro
            )
            self.session.add(item_orm)
        else:
            stmt = select(ItemConsumoORM).where(ItemConsumoORM.id == item.id)
            item_orm = (await self.session.execute(stmt)).scalar_one()
            item_orm.descricao = item.descricao
            item_orm.quantidade = item.quantidade
            item_orm.valor_unitario = item.valor_unitario

        await self.session.commit()
        if item.id is None:
            item.id = item_orm.id
        return item

    async def buscar_por_id(self, item_id: int) -> Optional[ItemConsumo]:
        stmt = select(ItemConsumoORM).where(ItemConsumoORM.id == item_id)
        resultado = await self.session.execute(stmt)
        orm = resultado.scalar_one_or_none()
        return orm.to_domain() if orm else None

    async def deletar(self, item_id: int) -> None:
        stmt = select(ItemConsumoORM).where(ItemConsumoORM.id == item_id)
        orm_obj = (await self.session.execute(stmt)).scalar_one_or_none()
        if orm_obj:
            await self.session.delete(orm_obj)
            await self.session.commit()

    async def buscar_por_hospedagem(self, hospedagem_id: int) -> List[ItemConsumo]:
        """Retorna todos os itens consumidos na hospedagem especificada."""
        stmt = select(ItemConsumoORM).where(ItemConsumoORM.hospedagem_id == hospedagem_id)
        resultado = await self.session.execute(stmt)
        return [orm.to_domain() for orm in resultado.scalars().all()]

    async def somar_total_por_hospedagem(self, hospedagem_id: int) -> Decimal:
        """Calcula a soma total dos itens consumidos na hospedagem via agregação SQL."""
        stmt = select(
            func.sum(ItemConsumoORM.quantidade * ItemConsumoORM.valor_unitario)
        ).where(ItemConsumoORM.hospedagem_id == hospedagem_id)

        resultado = await self.session.execute(stmt)
        total = resultado.scalar_one_or_none()

        return Decimal(total) if total else Decimal("0.00")