"""0007_phase9_digital_twin

Revision ID: 0007_phase9_digital_twin
Revises: 0006_phase6_flood_simulation
Create Date: 2026-09-13 00:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0007_phase9_digital_twin'
down_revision: Union[str, None] = '0006_phase6_flood_simulation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create digital_twin_runs table
    op.create_table(
        'digital_twin_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_identifier', sa.String(length=128), nullable=False),
        sa.Column('study_area_id', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('simulation_start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('horizon_minutes', sa.Integer(), nullable=False, server_default='180'),
        sa.Column('timestep_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('total_timesteps', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('rainfall_source', sa.String(length=128), nullable=True),
        sa.Column('forecast_source', sa.String(length=128), nullable=True),
        sa.Column('terrain_dataset_id', sa.String(length=128), nullable=True),
        sa.Column('drainage_dataset_id', sa.String(length=128), nullable=True),
        sa.Column('physical_engine_version', sa.String(length=32), nullable=False, server_default='Phase6_Deterministic_D8'),
        sa.Column('ml_calibration_version', sa.String(length=64), nullable=True, server_default='Phase8_XGBoost_Prototype_V1'),
        sa.Column('input_completeness', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('output_directory', sa.Text(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_digital_twin_runs_run_identifier', 'digital_twin_runs', ['run_identifier'], unique=True)
    op.create_index('ix_digital_twin_runs_study_area_id', 'digital_twin_runs', ['study_area_id'], unique=False)
    op.create_index('ix_digital_twin_runs_status', 'digital_twin_runs', ['status'], unique=False)

    # 2. Create digital_twin_artifacts table
    op.create_table(
        'digital_twin_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', sa.String(length=128), nullable=False),
        sa.Column('artifact_type', sa.String(length=64), nullable=False),
        sa.Column('minutes_from_start', sa.Integer(), nullable=True),
        sa.Column('relative_path', sa.Text(), nullable=False),
        sa.Column('format', sa.String(length=32), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_digital_twin_artifacts_run_id', 'digital_twin_artifacts', ['run_id'], unique=False)
    op.create_index('ix_digital_twin_artifacts_artifact_type', 'digital_twin_artifacts', ['artifact_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_digital_twin_artifacts_artifact_type', table_name='digital_twin_artifacts')
    op.drop_index('ix_digital_twin_artifacts_run_id', table_name='digital_twin_artifacts')
    op.drop_table('digital_twin_artifacts')

    op.drop_index('ix_digital_twin_runs_status', table_name='digital_twin_runs')
    op.drop_index('ix_digital_twin_runs_study_area_id', table_name='digital_twin_runs')
    op.drop_index('ix_digital_twin_runs_run_identifier', table_name='digital_twin_runs')
    op.drop_table('digital_twin_runs')
