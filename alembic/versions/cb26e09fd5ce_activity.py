"""activity

Revision ID: cb26e09fd5ce
Revises: ead5a19d416b
Create Date: 2020-03-30 15:46:01.034439

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb26e09fd5ce'
down_revision = 'ead5a19d416b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Activity',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('ACid', sa.String(length=64), nullable=False),
    sa.Column('ADid', sa.String(length=64), nullable=True),
    sa.Column('ACname', sa.String(length=255), nullable=True),
    sa.Column('ACbanner', sa.Text(), nullable=True),
    sa.Column('ACorganizer', sa.String(length=255), nullable=True),
    sa.Column('ACstartTime', sa.DateTime(), nullable=True),
    sa.Column('AClocation', sa.String(length=255), nullable=True),
    sa.Column('ACdetail', sa.Text(), nullable=True),
    sa.Column('ACnumber', sa.Integer(), nullable=True),
    sa.Column('ACstatus', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('ACid')
    )
    op.create_table('UserActivity',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('UAid', sa.String(length=64), nullable=False),
    sa.Column('USid', sa.String(length=64), nullable=True),
    sa.Column('ACid', sa.String(length=64), nullable=True),
    sa.Column('UAstatus', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('UAid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('UserActivity')
    op.drop_table('Activity')
    # ### end Alembic commands ###
