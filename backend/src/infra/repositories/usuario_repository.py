from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import Optional

from backend.src.domain.models.usuario import Usuario, Gerente, Recepcionista
from backend.src.infra.orm_models.usuario_orm import UsuarioORM, GerenteORM, RecepcionistaORM

class EmailDuplicadoError(Exception):
    pass

class UsuarioRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def salvar(self, usuario: Usuario) -> Usuario:
        if usuario.id is None:
            # Identifica a classe da Entidade para instanciar o ORM filho correto
            if isinstance(usuario, Gerente):
                orm_obj = GerenteORM(nome=usuario.nome, email=usuario.email, senha_hash=usuario.senha_hash)
            elif isinstance(usuario, Recepcionista):
                orm_obj = RecepcionistaORM(nome=usuario.nome, email=usuario.email, senha_hash=usuario.senha_hash)
            else:
                raise ValueError("Tipo de usuário não suportado para persistência.")
            
            self.session.add(orm_obj)
        else:
            stmt = select(UsuarioORM).where(UsuarioORM.id == usuario.id)
            orm_obj = (await self.session.execute(stmt)).scalar_one()
            orm_obj.nome = usuario.nome
            orm_obj.email = usuario.email
            orm_obj.senha_hash = usuario.senha_hash

        try:
            await self.session.commit()
            if usuario.id is None:
                usuario.id = orm_obj.id
            return usuario
        except IntegrityError:
            await self.session.rollback()
            raise EmailDuplicadoError("Já existe um utilizador com este e-mail.")

    async def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """
        Devolve a entidade já instanciada como Gerente ou Recepcionista,
        graças ao mapeamento polimórfico do SQLAlchemy.
        """
        stmt = select(UsuarioORM).where(UsuarioORM.email == email)
        resultado = await self.session.execute(stmt)
        orm_obj = resultado.scalar_one_or_none()
        
        return orm_obj.to_domain() if orm_obj else None