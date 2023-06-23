"""create account table

Revision ID: fb7eb6fcd7b3
Revises: 
Create Date: 2023-06-20 11:12:22.113168

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb7eb6fcd7b3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.BigInteger(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('events',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.Column('date_event', sa.Text(), nullable=False),
                    sa.Column('time_event', sa.Text(), nullable=False),
                    sa.Column('place', sa.Text(), nullable=False),
                    sa.Column('link', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('events')
