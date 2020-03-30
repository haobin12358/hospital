"""add_ATincomeProof

Revision ID: ead5a19d416b
Revises: bb07362aaf4c
Create Date: 2020-03-30 01:18:24.943214

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ead5a19d416b'
down_revision = 'bb07362aaf4c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Assistance', sa.Column('ATincomeProof', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Assistance', 'ATincomeProof')
    # ### end Alembic commands ###