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
        item_orm = ItemConsumoORM(
            hospedagem_id=item.hospedagem_id,
            descricao=item.descricao,
            quantidade=item.quantidade,
            valor_unitario=item.valor_unitario,
            data_registro=item.data_registro
        )
        self.session.add(item_orm)
        await self.session.commit()
        item.id = item_orm.id
        return item

    async def buscar_por_hospedagem(self, hospedagem_id: int) -> List[ItemConsumo]:
        """Devolve a lista detalhada para a impressão do Extrato da Conta."""
        stmt = select(ItemConsumoORM).where(ItemConsumoORM.hospedagem_id == hospedagem_id)
        resultado = await self.session.execute(stmt)
        return [orm.to_domain() for orm in resultado.scalars().all()]

    async def somar_total_por_hospedagem(self, hospedagem_id: int) -> Decimal:
        """
        O coração financeiro do Check-out!
        Delega para a base de dados (PostgreSQL) o trabalho de multiplicar a quantidade
        pelo valor unitário e somar tudo numa única operação ultrarrápida.
        """
        stmt = select(
            func.sum(ItemConsumoORM.quantidade * ItemConsumoORM.valor_unitario)
        ).where(ItemConsumoORM.hospedagem_id == hospedagem_id)

        resultado = await self.session.execute(stmt)
        total = resultado.scalar_one_or_none()

        # Se não houver consumos, devolve 0.00
        return Decimal(total) if total else Decimal("0.00")