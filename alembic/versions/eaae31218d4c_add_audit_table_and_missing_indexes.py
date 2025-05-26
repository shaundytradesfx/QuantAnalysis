"""add_audit_table_and_missing_indexes

Revision ID: eaae31218d4c
Revises: initial_migration
Create Date: 2025-05-25 20:35:38.079030

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = 'eaae31218d4c'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit table for failed parsing attempts
    op.create_table(
        'audit_failures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('html_snippet', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=True),
        sa.Column('resolved', sa.Boolean(), default=False, nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_failures_timestamp'), 'audit_failures', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_failures_error_type'), 'audit_failures', ['error_type'], unique=False)
    op.create_index(op.f('ix_audit_failures_resolved'), 'audit_failures', ['resolved'], unique=False)

    # Add composite index on (currency, scheduled_datetime) for events table as specified in PRD
    op.create_index('ix_events_currency_scheduled_datetime', 'events', ['currency', 'scheduled_datetime'], unique=False)
    
    # Add proper index on (event_id, timestamp_collected DESC) for indicators table as specified in PRD
    op.create_index('ix_indicators_event_id_timestamp_desc', 'indicators', ['event_id', sa.text('timestamp_collected DESC')], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_indicators_event_id_timestamp_desc', table_name='indicators')
    op.drop_index('ix_events_currency_scheduled_datetime', table_name='events')
    
    # Drop audit table
    op.drop_index(op.f('ix_audit_failures_resolved'), table_name='audit_failures')
    op.drop_index(op.f('ix_audit_failures_error_type'), table_name='audit_failures')
    op.drop_index(op.f('ix_audit_failures_timestamp'), table_name='audit_failures')
    op.drop_table('audit_failures') 