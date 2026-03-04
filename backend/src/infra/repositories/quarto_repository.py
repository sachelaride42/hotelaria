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

    async def salvar(self, quarto: Quarto) -> Quarto:

        # Salva ou atualiza o quarto.
        # É aqui onde ocorre o Optimistic Locking

        if quarto.id is None:
            # É um quarto novo (Insert)
            novo_quarto_orm = QuartoORM(
                numero=quarto.numero,
                andar=quarto.andar,
                status=quarto.status
            )
            self.session.add(novo_quarto_orm)
        else:
            # É uma atualização (Update)
            stmt = select(QuartoORM).where(QuartoORM.id == quarto.id)
            resultado = await self.session.execute(stmt)
            quarto_orm = resultado.scalar_one()

            # Atualizamos os dados, incluindo a versão que veio do nosso Domínio
            quarto_orm.status = quarto.status
            quarto_orm.versao = quarto.versao

        try:
            # Tentamos commitar a transação no banco
            await self.session.commit()

            # Se der certo, atualizamos o ID e a nova Versão na nossa Entidade
            if quarto.id is None:
                quarto.id = novo_quarto_orm.id
            # O SQLAlchemy incrementou a versão do ORM automaticamente, copiamos de volta:
            quarto.versao = novo_quarto_orm.versao if quarto.id is None else quarto_orm.versao

            return quarto

        except StaleDataError:
            # O banco de dados rejeitou o UPDATE porque a versão não bate (Race Condition)
            await self.session.rollback()
            raise ConcorrenciaQuartoError(
                f"O quarto {quarto.numero} foi modificado por outro usuário. Tente novamente."
            )