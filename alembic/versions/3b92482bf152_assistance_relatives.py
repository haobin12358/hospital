"""assistance_relatives

Revision ID: 3b92482bf152
Revises: 9f04b8b00d33
Create Date: 2020-03-29 22:32:05.882121

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b92482bf152'
down_revision = '9f04b8b00d33'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Assistance',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('ATid', sa.String(length=64), nullable=False),
    sa.Column('USid', sa.String(length=64), nullable=False),
    sa.Column('ATname', sa.String(length=10), nullable=True),
    sa.Column('ATbirthday', sa.Date(), nullable=True),
    sa.Column('ATgender', sa.Integer(), nullable=True),
    sa.Column('AThousehold', sa.String(length=255), nullable=True),
    sa.Column('ATaddress', sa.String(length=255), nullable=True),
    sa.Column('ATtelphone', sa.String(length=16), nullable=True),
    sa.Column('ARids', sa.Text(), nullable=True),
    sa.Column('ATcondition', sa.Text(), nullable=True),
    sa.Column('ATtreatment', sa.Text(), nullable=True),
    sa.Column('AThospital', sa.String(length=100), nullable=True),
    sa.Column('ATdetail', sa.Text(), nullable=True),
    sa.Column('ATdate', sa.Date(), nullable=True),
    sa.Column('ATstatus', sa.Integer(), nullable=True),
    sa.Column('Reviewer', sa.String(length=64), nullable=True),
    sa.Column('RejectReason', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('ATid')
    )
    op.create_table('AssistancePicture',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('APid', sa.String(length=64), nullable=False),
    sa.Column('ATid', sa.String(length=64), nullable=True),
    sa.Column('APtype', sa.Integer(), nullable=True),
    sa.Column('APimg', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('APid')
    )
    op.create_table('AssistanceRelatives',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('ARid', sa.String(length=64), nullable=False),
    sa.Column('USid', sa.String(length=64), nullable=False),
    sa.Column('ARtype', sa.Integer(), nullable=True),
    sa.Column('ARname', sa.String(length=20), nullable=True),
    sa.Column('ARage', sa.Integer(), nullable=True),
    sa.Column('ARcompany', sa.String(length=100), nullable=True),
    sa.Column('ARsalary', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('ARid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('AssistanceRelatives')
    op.drop_table('AssistancePicture')
    op.drop_table('Assistance')
    # ### end Alembic commands ###