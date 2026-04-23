from sqlalchemy import update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.exc import StaleDataError
from typing import Optional

from backend.src.domain.models.quarto import Quarto, StatusOcupacao, StatusLimpeza
from backend.src.infra.orm_models.quarto_orm import QuartoORM


class ConcorrenciaQuartoError(Exception):
    """Exceção de conflito de versão no Optimistic Locking do quarto."""
    pass


class QuartoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def buscar_por_id(self, quarto_id: int) -> Quarto | None:
        """Retorna o quarto pelo ID, ou None se não encontrado."""
        stmt = select(QuartoORM).where(QuartoORM.id == quarto_id)
        resultado = await self.session.execute(stmt)
        quarto_orm = resultado.scalar_one_or_none()

        if quarto_orm:
            return quarto_orm.to_domain()
        return None


    async def salvar(self, quarto: Quarto) -> Quarto:
        if quarto.id is None:
            quarto_orm = QuartoORM(
                numero=quarto.numero,
                andar=quarto.andar,
                status_ocupacao=quarto.status_ocupacao,
                status_limpeza=quarto.status_limpeza,
                tipo_quarto_id=quarto.tipo_quarto_id,
                versao=1
            )
            self.session.add(quarto_orm)
            await self.session.commit()
            await self.session.refresh(quarto_orm)
            quarto.id = quarto_orm.id
            quarto.versao = quarto_orm.versao
            return quarto

        else:
            stmt = (
                update(QuartoORM)
                .where(
                    QuartoORM.id == quarto.id,
                    QuartoORM.versao == quarto.versao  # Optimistic Locking: rejeita se a versão divergiu
                )
                .values(
                    status_ocupacao=quarto.status_ocupacao,
                    status_limpeza=quarto.status_limpeza,
                    versao=quarto.versao + 1
                )
            )

            resultado = await self.session.execute(stmt)
            if resultado.rowcount == 0:
                raise ConcorrenciaQuartoError(
                    f"O quarto {quarto.numero} foi modificado por outro usuário. Tente novamente."
                )  # sessão será descartada pelo contexto
            await self.session.commit()
            quarto.versao += 1

            return quarto

    async def atualizar_dados_basicos(self, quarto_id: int, numero: str, andar: int, tipo_quarto_id: int) -> Quarto | None:
        stmt = select(QuartoORM).where(QuartoORM.id == quarto_id)
        quarto_orm = (await self.session.execute(stmt)).scalar_one_or_none()
        if not quarto_orm:
            return None
        quarto_orm.numero = numero
        quarto_orm.andar = andar
        quarto_orm.tipo_quarto_id = tipo_quarto_id
        await self.session.commit()
        await self.session.refresh(quarto_orm)
        return quarto_orm.to_domain()

    async def deletar(self, quarto_id: int) -> None:
        stmt = select(QuartoORM).where(QuartoORM.id == quarto_id)
        quarto_orm = (await self.session.execute(stmt)).scalar_one_or_none()
        if quarto_orm:
            await self.session.delete(quarto_orm)
            await self.session.commit()

    async def contar_por_tipo(self, tipo_quarto_id: int) -> int:
        """Conta quantos quartos físicos existem de um determinado tipo."""
        stmt = select(func.count(QuartoORM.id)).where(QuartoORM.tipo_quarto_id == tipo_quarto_id)
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one()

    async def listar_todos(
        self,
        status_ocupacao: Optional[StatusOcupacao] = None,
        status_limpeza: Optional[StatusLimpeza] = None,
        andar: Optional[int] = None,
        tipo_quarto_id: Optional[int] = None,
    ) -> list[Quarto]:
        stmt = select(QuartoORM)
        if status_ocupacao is not None:
            stmt = stmt.where(QuartoORM.status_ocupacao == status_ocupacao)
        if status_limpeza is not None:
            stmt = stmt.where(QuartoORM.status_limpeza == status_limpeza)
        if andar is not None:
            stmt = stmt.where(QuartoORM.andar == andar)
        if tipo_quarto_id is not None:
            stmt = stmt.where(QuartoORM.tipo_quarto_id == tipo_quarto_id)
        resultado = await self.session.execute(stmt)
        return [q.to_domain() for q in resultado.scalars().all()]

