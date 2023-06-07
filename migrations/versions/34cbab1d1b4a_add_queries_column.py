"""add_queries_column

Revision ID: 34cbab1d1b4a
Revises: 57c73c97c70f
Create Date: 2023-06-07 13:16:28.100323

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '34cbab1d1b4a'
down_revision = '57c73c97c70f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('servers', sa.Column('queries', sa.BigInteger(), default=0))


def downgrade() -> None:
    op.drop_column('servers', 'queries')
