"""add_actual_data_columns

Revision ID: 582e8dd9639e
Revises: eaae31218d4c
Create Date: 2025-06-05 00:31:10.584324

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '582e8dd9639e'
down_revision = 'eaae31218d4c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns for actual data collection to indicators table
    op.add_column('indicators', sa.Column('actual_value', sa.Float(), nullable=True))
    op.add_column('indicators', sa.Column('actual_collected_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('indicators', sa.Column('actual_sentiment', sa.Integer(), nullable=True))
    op.add_column('indicators', sa.Column('is_actual_available', sa.Boolean(), default=False, nullable=True))
    
    # Add index on is_actual_available for efficient queries
    op.create_index(op.f('ix_indicators_is_actual_available'), 'indicators', ['is_actual_available'], unique=False)
    
    # Add composite index on (event_id, is_actual_available) for efficient actual data queries
    op.create_index('ix_indicators_event_id_actual_available', 'indicators', ['event_id', 'is_actual_available'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_indicators_event_id_actual_available', table_name='indicators')
    op.drop_index(op.f('ix_indicators_is_actual_available'), table_name='indicators')
    
    # Drop columns
    op.drop_column('indicators', 'is_actual_available')
    op.drop_column('indicators', 'actual_sentiment')
    op.drop_column('indicators', 'actual_collected_at')
    op.drop_column('indicators', 'actual_value') 