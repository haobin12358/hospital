"""banner

Revision ID: ea1987be79ff
Revises: d0ede120be35
Create Date: 2020-03-12 16:41:37.710850

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'ea1987be79ff'
down_revision = 'd0ede120be35'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Banner',
    sa.Column('isdelete', sa.Boolean(), nullable=True, comment='是否删除'),
    sa.Column('createtime', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updatetime', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.Column('BNid', sa.String(length=64), nullable=False),
    sa.Column('ADid', sa.String(length=64), nullable=True, comment='创建者id'),
    sa.Column('BNpicture', sa.Text(), nullable=False, comment='图片'),
    sa.Column('BNsort', sa.Integer(), nullable=True, comment='顺序'),
    sa.Column('contentlink', mysql.LONGTEXT(), nullable=True, comment='跳转链接'),
    sa.PrimaryKeyConstraint('BNid')
    )
    op.drop_table('MiniProgramBanner')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('MiniProgramBanner',
    sa.Column('isdelete', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True, comment='是否删除'),
    sa.Column('createtime', mysql.DATETIME(), nullable=True, comment='创建时间'),
    sa.Column('updatetime', mysql.DATETIME(), nullable=True, comment='更新时间'),
    sa.Column('BNid', mysql.VARCHAR(collation='utf8_bin', length=64), nullable=False),
    sa.Column('ADid', mysql.VARCHAR(collation='utf8_bin', length=64), nullable=True, comment='创建者id'),
    sa.Column('BNpicture', mysql.TEXT(collation='utf8_bin'), nullable=False, comment='图片'),
    sa.Column('BNsort', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True, comment='顺序'),
    sa.Column('contentlink', mysql.LONGTEXT(collation='utf8_bin'), nullable=True, comment='跳转链接'),
    sa.PrimaryKeyConstraint('BNid'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.drop_table('Banner')
    # ### end Alembic commands ###
