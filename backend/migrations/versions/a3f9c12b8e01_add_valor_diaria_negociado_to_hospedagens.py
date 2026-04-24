"""add valor_diaria_negociado to hospedagens

Revision ID: a3f9c12b8e01
Revises: 144e145747c0
Create Date: 2026-04-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f9c12b8e01'
down_revision: Union[str, Sequence[str], None] = '144e145747c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hospedagens',
        sa.Column('valor_diaria_negociado', sa.Numeric(10, 2), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('hospedagens', 'valor_diaria_negociado')
