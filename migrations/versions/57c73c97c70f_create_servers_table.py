"""create_servers_table

Revision ID: 57c73c97c70f
Revises: 
Create Date: 2023-06-05 10:49:09.774065

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '57c73c97c70f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('servers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('server_id', sa.BigInteger(), nullable=True),
        sa.Column('api_key', sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('server_id')
    )


def downgrade() -> None:
    op.drop_table('servers')
