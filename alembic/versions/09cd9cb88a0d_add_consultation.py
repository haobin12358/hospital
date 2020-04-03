"""'add_consultation'

Revision ID: 09cd9cb88a0d
Revises: b0b3b5162488
Create Date: 2020-04-04 02:57:51.590999

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09cd9cb88a0d'
down_revision = 'b0b3b5162488'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Consultation',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('CONid', sa.String(length=64), nullable=False),
    sa.Column('DOid', sa.String(length=64), nullable=True),
    sa.Column('CONstartTime', sa.DateTime(), nullable=True),
    sa.Column('CONendTime', sa.DateTime(), nullable=True),
    sa.Column('CONlimit', sa.Integer(), nullable=True),
    sa.Column('CONstatus', sa.Integer(), nullable=True),
    sa.Column('CONnote', sa.Text(), nullable=True),
    sa.Column('DOname', sa.String(length=255), nullable=False),
    sa.Column('DOtel', sa.String(length=13), nullable=True),
    sa.Column('DOtitle', sa.String(length=255), nullable=True),
    sa.Column('DOdetails', sa.Text(), nullable=True),
    sa.Column('DOwxid', sa.String(length=255), nullable=True),
    sa.Column('DOskilledIn', sa.Text(), nullable=True),
    sa.Column('DEname', sa.String(length=255), nullable=True),
    sa.Column('DEid', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('CONid')
    )
    op.create_table('Enroll',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('ENid', sa.String(length=64), nullable=False),
    sa.Column('CONid', sa.String(length=64), nullable=True),
    sa.Column('USid', sa.String(length=64), nullable=True),
    sa.Column('USname', sa.String(length=255), nullable=True),
    sa.Column('UStelphone', sa.String(length=13), nullable=True),
    sa.PrimaryKeyConstraint('ENid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Enroll')
    op.drop_table('Consultation')
    # ### end Alembic commands ###
