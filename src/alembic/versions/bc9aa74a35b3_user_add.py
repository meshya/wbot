"""User add

Revision ID: bc9aa74a35b3
Revises: 
Create Date: 2024-11-18 23:36:00.335048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc9aa74a35b3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tid', sa.Integer(), nullable=False),
    sa.Column('tun', sa.String(length=50), nullable=True),
    sa.Column('step', sa.String(length=20), nullable=True),
    sa.Column('ptime', sa.DateTime(), nullable=True),
    sa.Column('p', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tid')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    # ### end Alembic commands ###
