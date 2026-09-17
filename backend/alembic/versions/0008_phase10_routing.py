"""0008_phase10_routing

Revision ID: 0008_phase10_routing
Revises: 0007_phase9_digital_twin
Create Date: 2026-09-13 01:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0008_phase10_routing'
down_revision: Union[str, None] = '0007_phase9_digital_twin'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create routing_runs table
    op.create_table(
        'routing_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_identifier', sa.String(length=128), nullable=False),
        sa.Column('digital_twin_run_id', sa.String(length=128), nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('provider_mode', sa.String(length=64), nullable=False),
        sa.Column('origin_lat', sa.Float(), nullable=False),
        sa.Column('origin_lon', sa.Float(), nullable=False),
        sa.Column('dest_lat', sa.Float(), nullable=False),
        sa.Column('dest_lon', sa.Float(), nullable=False),
        sa.Column('recommendation', sa.String(length=64), nullable=False),
        sa.Column('usable_travel_window_min', sa.Integer(), nullable=True),
        sa.Column('route_flood_onset_min', sa.Integer(), nullable=True),
        sa.Column('estimated_travel_time_min', sa.Float(), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='COMPLETED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_routing_runs_run_identifier', 'routing_runs', ['run_identifier'], unique=True)
    op.create_index('ix_routing_runs_digital_twin_run_id', 'routing_runs', ['digital_twin_run_id'], unique=False)

    # 2. Create route_candidates table
    op.create_table(
        'route_candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('routing_run_id', sa.String(length=128), nullable=False),
        sa.Column('route_id', sa.String(length=128), nullable=False),
        sa.Column('summary', sa.String(length=256), nullable=True),
        sa.Column('distance_m', sa.Float(), nullable=False),
        sa.Column('estimated_duration_s', sa.Float(), nullable=False),
        sa.Column('recommendation', sa.String(length=64), nullable=False),
        sa.Column('usable_travel_window_min', sa.Integer(), nullable=True),
        sa.Column('route_flood_onset_min', sa.Integer(), nullable=True),
        sa.Column('peak_severity', sa.String(length=32), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('geometry_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_route_candidates_routing_run_id', 'route_candidates', ['routing_run_id'], unique=False)
    op.create_index('ix_route_candidates_route_id', 'route_candidates', ['route_id'], unique=False)

    # 3. Create route_exposures table
    op.create_table(
        'route_exposures',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('routing_run_id', sa.String(length=128), nullable=False),
        sa.Column('route_id', sa.String(length=128), nullable=False),
        sa.Column('minutes_from_start', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('affected_distance_m', sa.Float(), nullable=False),
        sa.Column('affected_percentage', sa.Float(), nullable=False),
        sa.Column('peak_severity', sa.String(length=32), nullable=False),
        sa.Column('peak_water_depth_m', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_route_exposures_routing_run_id', 'route_exposures', ['routing_run_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_route_exposures_routing_run_id', table_name='route_exposures')
    op.drop_table('route_exposures')

    op.drop_index('ix_route_candidates_route_id', table_name='route_candidates')
    op.drop_index('ix_route_candidates_routing_run_id', table_name='route_candidates')
    op.drop_table('route_candidates')

    op.drop_index('ix_routing_runs_digital_twin_run_id', table_name='routing_runs')
    op.drop_index('ix_routing_runs_run_identifier', table_name='routing_runs')
    op.drop_table('routing_runs')
