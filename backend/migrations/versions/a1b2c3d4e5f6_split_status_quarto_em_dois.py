"""split_status_quarto_em_dois

Separa o campo 'status' de Quarto em duas máquinas de estado independentes:
- status_ocupacao: LIVRE | OCUPADO | MANUTENCAO
- status_limpeza:  LIMPO | SUJO

Revision ID: a1b2c3d4e5f6
Revises: c1a438c6dcf0
Create Date: 2026-04-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c1a438c6dcf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Adiciona coluna status_limpeza (nullable por enquanto para permitir data migration)
    op.add_column('quartos', sa.Column('status_limpeza', sa.String(5), nullable=True))

    # 2. Preenche status_limpeza com base no status atual
    #    - Rows com status='SUJO' → status_limpeza='SUJO'
    #    - Demais → status_limpeza='LIMPO'
    op.execute("""
        UPDATE quartos
        SET status_limpeza = CASE WHEN status = 'SUJO' THEN 'SUJO' ELSE 'LIMPO' END
    """)

    # 3. Torna status_limpeza NOT NULL após o preenchimento
    op.alter_column('quartos', 'status_limpeza', nullable=False)

    # 4. Para PostgreSQL: criar o novo enum statusocupacao e statuslimpeza,
    #    alterar o tipo da coluna status_ocupacao e dropar o enum antigo statusquarto.
    #    Usamos op.execute para operações DDL que o Alembic não suporta diretamente.
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # Cria o novo tipo de enum para ocupação (sem SUJO)
        op.execute("CREATE TYPE statusocupacao AS ENUM ('LIVRE', 'OCUPADO', 'MANUTENCAO')")

        # Renomeia coluna status → status_ocupacao mantendo os dados
        op.execute("ALTER TABLE quartos RENAME COLUMN status TO status_ocupacao")

        # Converte os valores SUJO existentes para LIVRE antes de mudar o tipo
        op.execute("UPDATE quartos SET status_ocupacao = 'LIVRE' WHERE status_ocupacao = 'SUJO'")

        # Altera o tipo da coluna para o novo enum
        op.execute("""
            ALTER TABLE quartos
            ALTER COLUMN status_ocupacao TYPE statusocupacao
            USING status_ocupacao::text::statusocupacao
        """)

        # Remove o enum antigo
        op.execute("DROP TYPE statusquarto")

        # Converte status_limpeza de VARCHAR para o tipo enum statuslimpeza
        op.execute("CREATE TYPE statuslimpeza AS ENUM ('LIMPO', 'SUJO')")
        op.execute("""
            ALTER TABLE quartos
            ALTER COLUMN status_limpeza TYPE statuslimpeza
            USING status_limpeza::text::statuslimpeza
        """)
    else:
        # SQLite e outros: rename simples via recreate (Alembic batch mode)
        with op.batch_alter_table('quartos') as batch_op:
            batch_op.alter_column('status', new_column_name='status_ocupacao')

        # Para SQLite, converte valores SUJO → LIVRE em status_ocupacao
        op.execute("UPDATE quartos SET status_ocupacao = 'LIVRE' WHERE status_ocupacao = 'SUJO'")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # Recria o enum antigo com todos os 4 valores
        op.execute("CREATE TYPE statusquarto AS ENUM ('LIVRE', 'OCUPADO', 'SUJO', 'MANUTENCAO')")

        # Renomeia status_ocupacao → status
        op.execute("ALTER TABLE quartos RENAME COLUMN status_ocupacao TO status")

        # Recombina status_limpeza=SUJO + status_ocupacao=LIVRE → status=SUJO
        op.execute("""
            UPDATE quartos
            SET status = 'SUJO'
            WHERE status = 'LIVRE' AND status_limpeza = 'SUJO'
        """)

        # Altera o tipo da coluna de volta para statusquarto
        op.execute("""
            ALTER TABLE quartos
            ALTER COLUMN status TYPE statusquarto
            USING status::text::statusquarto
        """)

        # Remove os novos enums
        op.execute("DROP TYPE statusocupacao")
        op.execute("DROP TYPE statuslimpeza")
    else:
        # Para SQLite: reverte o rename
        with op.batch_alter_table('quartos') as batch_op:
            batch_op.alter_column('status_ocupacao', new_column_name='status')

        # Recombina: onde status_limpeza=SUJO e status=LIVRE, volta para SUJO
        op.execute("""
            UPDATE quartos
            SET status = 'SUJO'
            WHERE status = 'LIVRE' AND status_limpeza = 'SUJO'
        """)

    # Remove a coluna status_limpeza
    op.drop_column('quartos', 'status_limpeza')
