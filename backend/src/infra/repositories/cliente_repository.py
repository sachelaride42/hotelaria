from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from backend.src.domain.models.cliente import Cliente
from backend.src.infra.orm_models.cliente_orm import ClienteORM


class CPFDuplicadoError(Exception):
    """Exceção customizada para isolar o erro de banco de dados da API."""
    pass


class ClienteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def salvar(self, cliente: Cliente) -> Cliente:
        """Insere um novo cliente ou atualiza um existente."""
        if cliente.id is None:
            # Ajustado para mapear os campos conforme a nova entidade
            cliente_orm = ClienteORM(
                nome=cliente.nome,
                telefone=cliente.telefone,
                cpf=cliente.cpf,
                email=cliente.email
            )
            self.session.add(cliente_orm)
        else:
            stmt = select(ClienteORM).where(ClienteORM.id == cliente.id)
            resultado = await self.session.execute(stmt)
            cliente_orm = resultado.scalar_one()

            cliente_orm.nome = cliente.nome
            cliente_orm.telefone = cliente.telefone
            cliente_orm.cpf = cliente.cpf
            cliente_orm.email = cliente.email

        try:
            await self.session.commit()
            if cliente.id is None:
                cliente.id = cliente_orm.id
            return cliente
        except IntegrityError:
            await self.session.rollback()
            raise CPFDuplicadoError("Erro: CPF já cadastrado. Por favor, utilize a busca para encontrar o cliente.")

    async def buscar_por_id(self, cliente_id: int) -> Optional[Cliente]:
        stmt = select(ClienteORM).where(ClienteORM.id == cliente_id)
        resultado = await self.session.execute(stmt)
        cliente_orm = resultado.scalar_one_or_none()
        return cliente_orm.to_domain() if cliente_orm else None

    async def buscar_por_cpf(self, cpf: str) -> Optional[Cliente]:
        """Busca pelo CPF. Retorna None se não achar."""
        stmt = select(ClienteORM).where(ClienteORM.cpf == cpf)
        resultado = await self.session.execute(stmt)
        cliente_orm = resultado.scalar_one_or_none()
        return cliente_orm.to_domain() if cliente_orm else None

    async def buscar_por_nome(self, nome: str) -> List[Cliente]:
        """Busca parcial de clientes ignorando maiúsculas e minúsculas."""
        stmt = select(ClienteORM).where(ClienteORM.nome.ilike(f"%{nome}%"))
        resultado = await self.session.execute(stmt)
        clientes_orm = resultado.scalars().all()
        return [c.to_domain() for c in clientes_orm]