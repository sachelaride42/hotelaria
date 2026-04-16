from sqlalchemy import update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.exc import StaleDataError

from backend.src.domain.models.quarto import Quarto
from backend.src.infra.orm_models.quarto_orm import QuartoORM


class ConcorrenciaQuartoError(Exception):
    """Exceção customizada para isolar o erro do SQLAlchemy da nossa API"""
    pass


class QuartoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def buscar_por_id(self, quarto_id: int) -> Quarto | None:
        #Busca um quarto no banco e o converte para a Entidade de Domínio pura
        stmt = select(QuartoORM).where(QuartoORM.id == quarto_id)
        resultado = await self.session.execute(stmt)
        quarto_orm = resultado.scalar_one_or_none()

        if quarto_orm:
            return quarto_orm.to_domain()
        return None


    async def salvar(self, quarto: Quarto) -> Quarto:
        if quarto.id is None:
            # INSERT: quarto novo
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
            # UPDATE com verificação de versão manual (Optimistic Locking real)
            stmt = (
                update(QuartoORM)
                .where(
                    QuartoORM.id == quarto.id,
                    QuartoORM.versao == quarto.versao  # ← coração do Optimistic Locking
                )
                .values(
                    status_ocupacao=quarto.status_ocupacao,
                    status_limpeza=quarto.status_limpeza,
                    versao=quarto.versao + 1  # ← incrementa a versão
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

    async def contar_por_tipo(self, tipo_quarto_id: int) -> int:
        """Conta quantos quartos físicos existem de um determinado tipo."""
        # O teste desse metodo esta feito em test_tipo_quarto_repository.py
        stmt = select(func.count(QuartoORM.id)).where(QuartoORM.tipo_quarto_id == tipo_quarto_id)
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one()

