"""'pointtask'

Revision ID: cb53b24eb2a5
Revises: ce19e637f8f0
Create Date: 2020-04-04 01:40:17.294584

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'cb53b24eb2a5'
down_revision = 'ce19e637f8f0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('PointTask',
    sa.Column('isdelete', sa.Boolean(), nullable=True, comment='是否删除'),
    sa.Column('createtime', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updatetime', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.Column('PTid', sa.String(length=64), nullable=False, comment='任务id'),
    sa.Column('PTname', sa.String(length=255), nullable=True, comment='任务内容'),
    sa.Column('PTtype', sa.Integer(), nullable=True, comment='701登录702邀请新用户703完善个人信息704完善家人信息705购买会员706充值707看视频708挂号709评论710积分购物711报名活动712公益援助713健康测评'),
    sa.Column('PTnumber', sa.Integer(), nullable=True, comment='积分数'),
    sa.Column('PTtime', sa.Integer(), nullable=True, comment='限制次数， -表示限制次数+表示每日次数'),
    sa.PrimaryKeyConstraint('PTid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('PointTask')
    # ### end Alembic commands ###
