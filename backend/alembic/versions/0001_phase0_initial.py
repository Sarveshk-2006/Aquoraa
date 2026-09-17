"""0001_phase0_initial

Revision ID: 0001_phase0_initial
Revises: 
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_phase0_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 2. Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('actor', sa.String(length=128), nullable=False),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('entity_type', sa.String(length=128), nullable=False),
        sa.Column('entity_id', sa.String(length=128), nullable=False),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('model_version', sa.String(length=64), nullable=True),
        sa.Column('data_version', sa.String(length=64), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_id'), 'audit_events', ['id'], unique=False)
    op.create_index(op.f('ix_audit_events_timestamp'), 'audit_events', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_events_actor'), 'audit_events', ['actor'], unique=False)
    op.create_index(op.f('ix_audit_events_action'), 'audit_events', ['action'], unique=False)

    # 3. Create model_runs table
    op.create_table(
        'model_runs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('model_version', sa.String(length=64), nullable=False),
        sa.Column('dataset_version', sa.String(length=64), nullable=False),
        sa.Column('feature_version', sa.String(length=64), nullable=False),
        sa.Column('input_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('forecast_horizon', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('metrics_reference', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_runs_id'), 'model_runs', ['id'], unique=False)
    op.create_index(op.f('ix_model_runs_model_version'), 'model_runs', ['model_version'], unique=False)
    op.create_index(op.f('ix_model_runs_status'), 'model_runs', ['status'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_model_runs_status'), table_name='model_runs')
    op.drop_index(op.f('ix_model_runs_model_version'), table_name='model_runs')
    op.drop_index(op.f('ix_model_runs_id'), table_name='model_runs')
    op.drop_table('model_runs')

    op.drop_index(op.f('ix_audit_events_action'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_actor'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_timestamp'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_id'), table_name='audit_events')
    op.drop_table('audit_events')
