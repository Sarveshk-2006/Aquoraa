"""0009_phase11_critical_access

Revision ID: 0009_phase11_critical_access
Revises: 0008_phase10_routing
Create Date: 2026-09-13 01:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0009_phase11_critical_access'
down_revision: Union[str, None] = '0008_phase10_routing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create critical_facilities table
    op.create_table(
        'critical_facilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('facility_id', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False),
        sa.Column('source_id', sa.String(length=128), nullable=True),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('verification_status', sa.String(length=64), nullable=False),
        sa.Column('operational_status', sa.String(length=64), nullable=False, server_default='UNKNOWN'),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('facility_id')
    )
    op.create_index('ix_critical_facilities_facility_id', 'critical_facilities', ['facility_id'])
    op.create_index('ix_critical_facilities_category', 'critical_facilities', ['category'])

    # 2. Create critical_access_runs table
    op.create_table(
        'critical_access_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_identifier', sa.String(length=128), nullable=False),
        sa.Column('facility_id', sa.String(length=128), nullable=False),
        sa.Column('digital_twin_run_id', sa.String(length=128), nullable=False),
        sa.Column('routing_run_id', sa.String(length=128), nullable=False),
        sa.Column('origin_lat', sa.Float(), nullable=False),
        sa.Column('origin_lon', sa.Float(), nullable=False),
        sa.Column('current_access_status', sa.String(length=64), nullable=False),
        sa.Column('modeled_loss_of_access_min', sa.Integer(), nullable=True),
        sa.Column('time_to_loss_of_access_min', sa.Integer(), nullable=True),
        sa.Column('recommendation', sa.String(length=64), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='COMPLETED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_critical_access_runs_run_identifier', 'critical_access_runs', ['run_identifier'])

    # 3. Create critical_access_results table
    op.create_table(
        'critical_access_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('access_run_id', sa.String(length=128), nullable=False),
        sa.Column('facility_id', sa.String(length=128), nullable=False),
        sa.Column('minutes_from_start', sa.Integer(), nullable=False),
        sa.Column('access_status', sa.String(length=64), nullable=False),
        sa.Column('route_id', sa.String(length=128), nullable=False),
        sa.Column('peak_severity', sa.String(length=32), nullable=False),
        sa.Column('usable_travel_window_min', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_critical_access_results_run_id', 'critical_access_results', ['access_run_id'])


def downgrade() -> None:
    op.drop_index('ix_critical_access_results_run_id', table_name='critical_access_results')
    op.drop_table('critical_access_results')
    op.drop_index('ix_critical_access_runs_run_identifier', table_name='critical_access_runs')
    op.drop_table('critical_access_runs')
    op.drop_index('ix_critical_facilities_category', table_name='critical_facilities')
    op.drop_index('ix_critical_facilities_facility_id', table_name='critical_facilities')
    op.drop_table('critical_facilities')
