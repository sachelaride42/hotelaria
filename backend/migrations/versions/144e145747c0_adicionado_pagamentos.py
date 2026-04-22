"""adicionado pagamentos

Revision ID: 144e145747c0
Revises: 216f4e56ef08
Create Date: 2026-04-22 14:09:15.624298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '144e145747c0'
down_revision: Union[str, Sequence[str], None] = '216f4e56ef08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'pagamentos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hospedagem_id', sa.Integer(), nullable=False),
        sa.Column('valor_pago', sa.Numeric(10, 2), nullable=False),
        sa.Column('forma_pagamento', sa.Enum('DINHEIRO', 'CARTAO_CREDITO', 'CARTAO_DEBITO', 'PIX', 'BOLETO', name='formadepagamento'), nullable=False),
        sa.Column('data_hora_pagamento', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['hospedagem_id'], ['hospedagens.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('pagamentos')
    sa.Enum(name='formadepagamento').drop(op.get_bind())
