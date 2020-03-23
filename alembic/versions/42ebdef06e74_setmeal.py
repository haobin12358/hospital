"""'setmeal'

Revision ID: 42ebdef06e74
Revises: 403626b2f4a2
Create Date: 2020-03-23 15:18:08.943763

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '42ebdef06e74'
down_revision = '403626b2f4a2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Setmeal',
    sa.Column('isdelete', sa.Boolean(), nullable=True, comment='是否删除'),
    sa.Column('createtime', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updatetime', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.Column('SMid', sa.String(length=64), nullable=False),
    sa.Column('CLid', sa.String(length=64), nullable=True, comment='课程id'),
    sa.Column('CLname', sa.String(length=128), nullable=True, comment='课程名称'),
    sa.Column('SMnum', sa.Integer(), nullable=False, comment='课时数'),
    sa.Column('SMprice', sa.Float(), nullable=False, comment='套餐价格'),
    sa.PrimaryKeyConstraint('SMid')
    )
    op.add_column('Classes', sa.Column('CLprice', sa.Float(), nullable=True, comment='课时价格'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Classes', 'CLprice')
    op.drop_table('Setmeal')
    # ### end Alembic commands ###
