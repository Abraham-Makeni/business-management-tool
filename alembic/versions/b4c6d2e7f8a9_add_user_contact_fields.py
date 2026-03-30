"""add user contact fields

Revision ID: b4c6d2e7f8a9
Revises: f2a8b9c1d4e5
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4c6d2e7f8a9'
down_revision: Union[str, Sequence[str], None] = 'f2a8b9c1d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(length=120), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'phone')
    op.drop_column('users', 'email')
