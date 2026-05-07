"""Initial migration - create roi_records table

Revision ID: 0001
Revises: 
Create Date: 2026-05-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create roi_records table
    op.create_table(
        'roi_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('frame_seq', sa.BigInteger(), nullable=False),
        sa.Column('captured_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('x', sa.Integer(), nullable=False),
        sa.Column('y', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('frame_w', sa.Integer(), nullable=False),
        sa.Column('frame_h', sa.Integer(), nullable=False),
        sa.Column('has_face', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on (session_id, captured_at DESC)
    op.create_index(
        'idx_roi_session',
        'roi_records',
        ['session_id', sa.text('captured_at DESC')],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_roi_session', table_name='roi_records')
    op.drop_table('roi_records')
