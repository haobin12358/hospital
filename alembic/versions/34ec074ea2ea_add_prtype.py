"""'add_prtype'

Revision ID: 34ec074ea2ea
Revises: 0c27c91931bb
Create Date: 2020-04-12 10:57:35.574778

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '34ec074ea2ea'
down_revision = '0c27c91931bb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('OrderMain', sa.Column('PRtype', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('OrderMain', 'PRtype')
    # ### end Alembic commands ###
