from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from backend.src.domain.models.tipo_quarto import TipoDeQuarto
from backend.src.infra.orm_models.tipo_quarto_orm import TipoDeQuartoORM


class TipoQuartoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def salvar(self, tipo: TipoDeQuarto) -> TipoDeQuarto:
        if tipo.id is None:
            tipo_orm = TipoDeQuartoORM(
                nome=tipo.nome, descricao=tipo.descricao,
                precoBaseDiaria=tipo.precoBaseDiaria, capacidade=tipo.capacidade
            )
            self.session.add(tipo_orm)
        else:
            stmt = select(TipoDeQuartoORM).where(TipoDeQuartoORM.id == tipo.id)
            tipo_orm = (await self.session.execute(stmt)).scalar_one()
            tipo_orm.nome = tipo.nome
            tipo_orm.descricao = tipo.descricao
            tipo_orm.precoBaseDiaria = tipo.precoBaseDiaria
            tipo_orm.capacidade = tipo.capacidade

        await self.session.commit()
        await self.session.refresh(tipo_orm)
        if tipo.id is None:
            tipo.id = tipo_orm.id
        return tipo

    async def buscar_por_id(self, tipo_id: int) -> Optional[TipoDeQuarto]:
        stmt = select(TipoDeQuartoORM).where(TipoDeQuartoORM.id == tipo_id)
        resultado = await self.session.execute(stmt)
        orm = resultado.scalar_one_or_none()
        return orm.to_domain() if orm else None