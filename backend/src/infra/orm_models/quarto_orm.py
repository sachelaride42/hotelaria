from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Enum as SQLEnum, ForeignKey
from backend.src.domain.models.quarto import StatusQuarto, Quarto
from backend.src.infra.database import Base

# Base declarativa padrão do SQLAlchemy
#class Base(DeclarativeBase):
    #pass


class QuartoORM(Base):

    #Mapeamento ORM da tabela de quartos.
    #Esta classe é usada exclusivamente pela camada de Infraestrutura (Repositórios).

    __tablename__ = "quartos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    andar: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[StatusQuarto] = mapped_column(SQLEnum(StatusQuarto), default=StatusQuarto.LIVRE, nullable=False)

    tipo_quarto_id: Mapped[int] = mapped_column(ForeignKey("tipos_quarto.id"), nullable=False)
    # Optimistic Locking
    versao: Mapped[int] = mapped_column(default=1, nullable=False)

    # Essa configuração diz ao SQLAlchemy para gerenciar a coluna 'versao' automaticamente
    __mapper_args__ = {
        "version_id_col": versao
    }

    def to_domain(self):
        #Converte o objeto do banco para a entidade pura do domínio
        return Quarto(
            id=self.id,
            numero=self.numero,
            andar=self.andar,
            status=self.status,
            tipo_quarto_id=self.tipo_quarto_id,
            versao=self.versao
        )