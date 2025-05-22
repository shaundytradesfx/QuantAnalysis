"""initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2024-07-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('event_name', sa.Text(), nullable=True),
        sa.Column('scheduled_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('impact_level', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_currency'), 'events', ['currency'], unique=False)
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_index(op.f('ix_events_scheduled_datetime'), 'events', ['scheduled_datetime'], unique=False)

    # Create indicators table
    op.create_table(
        'indicators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('previous_value', sa.Float(), nullable=True),
        sa.Column('forecast_value', sa.Float(), nullable=True),
        sa.Column('timestamp_collected', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_indicators_event_id'), 'indicators', ['event_id'], unique=False)
    op.create_index(op.f('ix_indicators_id'), 'indicators', ['id'], unique=False)
    op.create_index(op.f('ix_indicators_timestamp_collected'), 'indicators', ['timestamp_collected'], unique=False)

    # Create sentiments table
    op.create_table(
        'sentiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('week_start', sa.Date(), nullable=True),
        sa.Column('week_end', sa.Date(), nullable=True),
        sa.Column('final_sentiment', sa.String(length=50), nullable=True),
        sa.Column('details_json', JSON(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentiments_currency'), 'sentiments', ['currency'], unique=False)
    op.create_index(op.f('ix_sentiments_id'), 'sentiments', ['id'], unique=False)
    op.create_index(op.f('ix_sentiments_week_start'), 'sentiments', ['week_start'], unique=False)

    # Create config table
    op.create_table(
        'config',
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('key')
    )


def downgrade() -> None:
    op.drop_table('config')
    op.drop_table('sentiments')
    op.drop_table('indicators')
    op.drop_table('events') 