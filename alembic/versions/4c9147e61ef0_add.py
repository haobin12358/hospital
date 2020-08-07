"""'add'

Revision ID: 4c9147e61ef0
Revises: b040ab62ef85
Create Date: 2020-08-07 19:09:58.298741

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c9147e61ef0'
down_revision = 'b040ab62ef85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Register', sa.Column('REreports', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Register', 'REreports')
    # ### end Alembic commands ###
