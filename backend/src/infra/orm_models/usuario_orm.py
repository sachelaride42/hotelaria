from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Enum as SQLEnum
from backend.src.infra.database import Base
from backend.src.domain.models.usuario import Gerente, Recepcionista, TipoUsuario

class UsuarioORM(Base):
    """Mapeamento da tabela única de usuários (Single Table Inheritance)."""
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # coluna discriminadora
    tipo: Mapped[TipoUsuario] = mapped_column(SQLEnum(TipoUsuario), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": "tipo",
        "polymorphic_identity": "USUARIO"
    }

class GerenteORM(UsuarioORM):
    __mapper_args__ = {"polymorphic_identity": TipoUsuario.GERENTE}

    def to_domain(self) -> Gerente:
        return Gerente(id=self.id, nome=self.nome, email=self.email, senha_hash=self.senha_hash)

class RecepcionistaORM(UsuarioORM):
    __mapper_args__ = {"polymorphic_identity": TipoUsuario.RECEPCIONISTA}

    def to_domain(self) -> Recepcionista:
        return Recepcionista(id=self.id, nome=self.nome, email=self.email, senha_hash=self.senha_hash)