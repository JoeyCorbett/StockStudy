"""Prepare for production

Revision ID: 9791c3e027f0
Revises: f5e5bd79f0b1
Create Date: 2024-12-16 05:18:32.630672

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9791c3e027f0'
down_revision = 'f5e5bd79f0b1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('membership_requests', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='Timestamp when the request was created',
               existing_comment='Timestamp when the request was creted',
               existing_nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('membership_requests', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='Timestamp when the request was creted',
               existing_comment='Timestamp when the request was created',
               existing_nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))

    # ### end Alembic commands ###
