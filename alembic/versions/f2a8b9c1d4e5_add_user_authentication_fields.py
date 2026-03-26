"""add user authentication fields

Revision ID: f2a8b9c1d4e5
Revises: e5c9f2b1c7d3
Create Date: 2026-03-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a8b9c1d4e5'
down_revision: Union[str, Sequence[str], None] = 'e5c9f2b1c7d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('pin_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('must_change_password', sa.Boolean(), nullable=False, default=False))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'must_change_password')
    op.drop_column('users', 'pin_hash')
