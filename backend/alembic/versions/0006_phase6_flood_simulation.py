"""0006_phase6_flood_simulation

Revision ID: 0006_phase6_flood_simulation
Revises: 0005_phase5_drainage
Create Date: 2026-09-12 01:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0006_phase6_flood_simulation'
down_revision: Union[str, None] = '0005_phase5_drainage'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create flood_simulation_runs table
    op.create_table(
        'flood_simulation_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('simulation_identifier', sa.String(length=128), nullable=False),
        sa.Column('study_area_id', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('horizon_minutes', sa.Integer(), nullable=False, server_default='180'),
        sa.Column('timestep_minutes', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('total_timesteps', sa.Integer(), nullable=False, server_default='19'),
        sa.Column('rainfall_source_id', sa.String(length=128), nullable=True),
        sa.Column('forecast_source_id', sa.String(length=128), nullable=True),
        sa.Column('terrain_dataset_id', sa.String(length=128), nullable=True),
        sa.Column('drainage_dataset_id', sa.String(length=128), nullable=True),
        sa.Column('configuration_hash', sa.String(length=64), nullable=False),
        sa.Column('engine_version', sa.String(length=32), nullable=False, server_default='0.6.0-phase6'),
        sa.Column('analysis_crs', sa.String(length=64), nullable=False, server_default='EPSG:32633'),
        sa.Column('input_completeness', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('mass_balance_totals', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('overall_mass_balance_error_m3', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_mass_balance_valid', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('output_manifest_path', sa.Text(), nullable=False),
        sa.Column('warnings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_flood_simulation_runs_simulation_identifier', 'flood_simulation_runs', ['simulation_identifier'], unique=True)
    op.create_index('ix_flood_simulation_runs_study_area_id', 'flood_simulation_runs', ['study_area_id'], unique=False)
    op.create_index('ix_flood_simulation_runs_status', 'flood_simulation_runs', ['status'], unique=False)
    op.create_index('ix_flood_simulation_runs_configuration_hash', 'flood_simulation_runs', ['configuration_hash'], unique=False)

    # 2. Create flood_simulation_artifacts table
    op.create_table(
        'flood_simulation_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('simulation_id', sa.String(length=128), nullable=False),
        sa.Column('artifact_type', sa.String(length=64), nullable=False),
        sa.Column('relative_path', sa.Text(), nullable=False),
        sa.Column('format', sa.String(length=32), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_flood_simulation_artifacts_simulation_id', 'flood_simulation_artifacts', ['simulation_id'], unique=False)
    op.create_index('ix_flood_simulation_artifacts_artifact_type', 'flood_simulation_artifacts', ['artifact_type'], unique=False)

    # 3. Create flood_simulation_diagnostics table
    op.create_table(
        'flood_simulation_diagnostics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('simulation_id', sa.String(length=128), nullable=False),
        sa.Column('timestep_index', sa.Integer(), nullable=False),
        sa.Column('timestamp_iso', sa.String(length=64), nullable=False),
        sa.Column('previous_storage_m3', sa.Float(), nullable=False),
        sa.Column('rainfall_input_m3', sa.Float(), nullable=False),
        sa.Column('runoff_generated_m3', sa.Float(), nullable=False),
        sa.Column('surface_inflow_m3', sa.Float(), nullable=False),
        sa.Column('surface_outflow_m3', sa.Float(), nullable=False),
        sa.Column('drainage_inflow_m3', sa.Float(), nullable=False),
        sa.Column('drainage_outflow_m3', sa.Float(), nullable=False),
        sa.Column('infiltration_losses_m3', sa.Float(), nullable=False),
        sa.Column('current_storage_m3', sa.Float(), nullable=False),
        sa.Column('mass_balance_error_m3', sa.Float(), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_flood_simulation_diagnostics_simulation_id', 'flood_simulation_diagnostics', ['simulation_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_flood_simulation_diagnostics_simulation_id', table_name='flood_simulation_diagnostics')
    op.drop_table('flood_simulation_diagnostics')

    op.drop_index('ix_flood_simulation_artifacts_artifact_type', table_name='flood_simulation_artifacts')
    op.drop_index('ix_flood_simulation_artifacts_simulation_id', table_name='flood_simulation_artifacts')
    op.drop_table('flood_simulation_artifacts')

    op.drop_index('ix_flood_simulation_runs_configuration_hash', table_name='flood_simulation_runs')
    op.drop_index('ix_flood_simulation_runs_status', table_name='flood_simulation_runs')
    op.drop_index('ix_flood_simulation_runs_study_area_id', table_name='flood_simulation_runs')
    op.drop_index('ix_flood_simulation_runs_simulation_identifier', table_name='flood_simulation_runs')
    op.drop_table('flood_simulation_runs')
