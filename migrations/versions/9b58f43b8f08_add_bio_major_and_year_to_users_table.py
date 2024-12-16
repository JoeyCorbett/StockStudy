"""Add bio, major, and year to users table

Revision ID: 9b58f43b8f08
Revises: af02fbd32ff4
Create Date: 2024-12-15 03:33:32.334718

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b58f43b8f08'
down_revision = 'af02fbd32ff4'
branch_labels = None
depends_on = None


def upgrade():
    year_enum = sa.Enum('FRESHMAN', 'SOPHMORE', 'JUNIOR', 'SENIOR', 'GRADUATE', name='yearenum')
    year_enum.create(op.get_bind()) 
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bio', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('major', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('year', sa.Enum('FRESHMAN', 'SOPHMORE', 'JUNIOR', 'SENIOR', 'GRADUATE', name='yearenum'), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('year')
        batch_op.drop_column('major')
        batch_op.drop_column('bio')


    year_enum = sa.Enum('FRESHMAN', 'SOPHMORE', 'JUNIOR', 'SENIOR', 'GRADUATE', name='yearenum')
    year_enum.drop(op.get_bind())
    # ### end Alembic commands ###
