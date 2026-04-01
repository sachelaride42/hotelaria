import locale
import sys

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from backend.src.domain.models.produto_servico import ProdutoServico
from backend.src.infra.orm_models.produto_servico_orm import ProdutoServicoORM


class ProdutoDuplicadoError(Exception):
    pass


class ProdutoServicoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def salvar(self, item: ProdutoServico) -> ProdutoServico:
        if item.id is None:
            item_orm = ProdutoServicoORM(
                descricao=item.descricao,
                preco_padrao=item.preco_padrao,
                categoria=item.categoria
            )
            self.session.add(item_orm)
        else:
            stmt = select(ProdutoServicoORM).where(ProdutoServicoORM.id == item.id)
            item_orm = (await self.session.execute(stmt)).scalar_one()

            item_orm.descricao = item.descricao
            item_orm.preco_padrao = item.preco_padrao
            item_orm.categoria = item.categoria

        try:
            await self.session.commit()
            if item.id is None:
                item.id = item_orm.id
            return item
        except IntegrityError:
            await self.session.rollback()
            raise ProdutoDuplicadoError("Já existe um produto ou serviço com esta descrição.")

    async def buscar_por_id(self, item_id: int) -> Optional[ProdutoServico]:
        stmt = select(ProdutoServicoORM).where(ProdutoServicoORM.id == item_id)
        resultado = await self.session.execute(stmt)
        orm = resultado.scalar_one_or_none()
        return orm.to_domain() if orm else None

    async def listar_todos(self) -> List[ProdutoServico]:
        stmt = select(ProdutoServicoORM)
        resultado = await self.session.execute(stmt)
        itens = [orm.to_domain() for orm in resultado.scalars().all()]

        nome_locale = "Portuguese_Brazil.1252" if sys.platform == "win32" else "pt_BR.UTF-8"
        locale.setlocale(locale.LC_COLLATE, nome_locale)

        return sorted(itens, key=lambda p: locale.strxfrm(p.descricao))





