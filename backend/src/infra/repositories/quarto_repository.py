from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
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

    async def salvar3(self, quarto: Quarto) -> Quarto:

        # Salva ou atualiza o quarto.
        # É aqui onde ocorre o Optimistic Locking

        if quarto.id is None:
            # É um quarto novo (Insert)
            quarto_orm = QuartoORM(
                numero=quarto.numero,
                andar=quarto.andar,
                status=quarto.status
            )
            self.session.add(quarto_orm)
        else:
            # É uma atualização (Update)
            stmt = select(QuartoORM).where(QuartoORM.id == quarto.id)
            resultado = await self.session.execute(stmt)
            quarto_orm = resultado.scalar_one()

            # Atualizamos os dados, incluindo a versão que veio do Domínio
            quarto_orm.status = quarto.status
            quarto_orm.versao = quarto.versao

        try:
            # Tentamos commitar a transação no banco
            await self.session.commit()

            # Se der certo, atualizamos o ID e a nova Versão na nossa Entidade
            if quarto.id is None:
                quarto.id = quarto_orm.id
            # O SQLAlchemy incrementou a versão do ORM automaticamente, copiamos de volta:
            quarto.versao = quarto_orm.versao

            return quarto

        except StaleDataError:
            # O banco de dados rejeitou o UPDATE porque a versão não bate (Race Condition)
            await self.session.rollback()
            raise ConcorrenciaQuartoError(
                f"O quarto {quarto.numero} foi modificado por outro usuário. Tente novamente."
            )

    async def salvar(self, quarto: Quarto) -> Quarto:
        if quarto.id is None:
            # INSERT: quarto novo
            quarto_orm = QuartoORM(
                numero=quarto.numero,
                andar=quarto.andar,
                status=quarto.status,
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
                    status=quarto.status,
                    versao=quarto.versao + 1  # ← incrementa a versão
                )
            )

            resultado = await self.session.execute(stmt)
            await self.session.commit()

            # rowcount == 0 significa que a versão não bateu → conflito detectado
            if resultado.rowcount == 0:
                await self.session.rollback()
                raise ConcorrenciaQuartoError(
                    f"O quarto {quarto.numero} foi modificado por outro usuário. Tente novamente."
                )

            quarto.versao += 1
            return quarto

    async def salvar2(self, quarto: Quarto) -> Quarto:

        is_novo = quarto.id is None

        if is_novo:
            orm_obj = QuartoORM(
                numero=quarto.numero,
                andar=quarto.andar,
                status=quarto.status
            )
            self.session.add(orm_obj)

        else:
            stmt = select(QuartoORM).where(QuartoORM.id == quarto.id)
            resultado = await self.session.execute(stmt)
            orm_obj = resultado.scalar_one()

            orm_obj.status = quarto.status
            orm_obj.versao = quarto.versao

        try:
            await self.session.commit()

            quarto.id = orm_obj.id
            quarto.versao = orm_obj.versao

            return quarto

        except StaleDataError:
            await self.session.rollback()
            raise ConcorrenciaQuartoError(
                f"O quarto {quarto.numero} foi modificado por outro usuário."
            )
