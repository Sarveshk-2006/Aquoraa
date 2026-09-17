"""0003_phase3_rainfall

Revision ID: 0003_phase3_rainfall
Revises: 0002_phase2_geospatial
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

revision: str = '0003_phase3_rainfall'
down_revision: Union[str, None] = '0002_phase2_geospatial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create rainfall_observation_grids table
    op.create_table(
        'rainfall_observation_grids',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('dataset_identifier', sa.String(length=128), nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('product_variant', sa.String(length=32), nullable=False),
        sa.Column('product_version', sa.String(length=32), nullable=False),
        sa.Column('observation_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('observation_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Float(), nullable=False),
        sa.Column('geom_bounds', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=False), nullable=False),
        sa.Column('resolution_deg_x', sa.Float(), nullable=False),
        sa.Column('resolution_deg_y', sa.Float(), nullable=False),
        sa.Column('units', sa.String(length=32), nullable=False),
        sa.Column('quantity_type', sa.String(length=32), nullable=False, server_default='ACCUMULATION'),
        sa.Column('quality_status', sa.String(length=32), nullable=False, server_default='VALID'),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('storage_pointer', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rainfall_observation_grids_id'), 'rainfall_observation_grids', ['id'], unique=False)
    op.create_index(op.f('ix_rainfall_observation_grids_dataset_identifier'), 'rainfall_observation_grids', ['dataset_identifier'], unique=True)
    op.create_index(op.f('ix_rainfall_observation_grids_provider'), 'rainfall_observation_grids', ['provider'], unique=False)
    op.create_index(op.f('ix_rainfall_observation_grids_observation_start'), 'rainfall_observation_grids', ['observation_start'], unique=False)
    op.create_index(op.f('ix_rainfall_observation_grids_observation_end'), 'rainfall_observation_grids', ['observation_end'], unique=False)
    op.create_index(op.f('ix_rainfall_observation_grids_quality_status'), 'rainfall_observation_grids', ['quality_status'], unique=False)
    op.create_index('idx_rainfall_observation_grids_geom_bounds', 'rainfall_observation_grids', ['geom_bounds'], postgresql_using='gist')

    # 2. Create rainfall_forecast_grids table
    op.create_table(
        'rainfall_forecast_grids',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('dataset_identifier', sa.String(length=128), nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('model_name', sa.String(length=64), nullable=False, server_default='SYNTHETIC_NOWCAST'),
        sa.Column('model_version', sa.String(length=32), nullable=False),
        sa.Column('initialization_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('lead_time_minutes', sa.Integer(), nullable=False),
        sa.Column('geom_bounds', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=False), nullable=False),
        sa.Column('resolution_deg_x', sa.Float(), nullable=False),
        sa.Column('resolution_deg_y', sa.Float(), nullable=False),
        sa.Column('units', sa.String(length=32), nullable=False),
        sa.Column('quality_status', sa.String(length=32), nullable=False, server_default='VALID'),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('storage_pointer', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rainfall_forecast_grids_id'), 'rainfall_forecast_grids', ['id'], unique=False)
    op.create_index(op.f('ix_rainfall_forecast_grids_dataset_identifier'), 'rainfall_forecast_grids', ['dataset_identifier'], unique=True)
    op.create_index(op.f('ix_rainfall_forecast_grids_provider'), 'rainfall_forecast_grids', ['provider'], unique=False)
    op.create_index(op.f('ix_rainfall_forecast_grids_initialization_time'), 'rainfall_forecast_grids', ['initialization_time'], unique=False)
    op.create_index(op.f('ix_rainfall_forecast_grids_valid_time'), 'rainfall_forecast_grids', ['valid_time'], unique=False)
    op.create_index(op.f('ix_rainfall_forecast_grids_lead_time_minutes'), 'rainfall_forecast_grids', ['lead_time_minutes'], unique=False)
    op.create_index(op.f('ix_rainfall_forecast_grids_quality_status'), 'rainfall_forecast_grids', ['quality_status'], unique=False)
    op.create_index('idx_rainfall_forecast_grids_geom_bounds', 'rainfall_forecast_grids', ['geom_bounds'], postgresql_using='gist')

    # 3. Create ingestion_runs table
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pipeline_type', sa.String(length=32), nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('source_identifier', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='SUCCESS'),
        sa.Column('records_ingested', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ingestion_runs_id'), 'ingestion_runs', ['id'], unique=False)
    op.create_index(op.f('ix_ingestion_runs_pipeline_type'), 'ingestion_runs', ['pipeline_type'], unique=False)
    op.create_index(op.f('ix_ingestion_runs_provider'), 'ingestion_runs', ['provider'], unique=False)
    op.create_index(op.f('ix_ingestion_runs_source_identifier'), 'ingestion_runs', ['source_identifier'], unique=False)
    op.create_index(op.f('ix_ingestion_runs_status'), 'ingestion_runs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ingestion_runs_status'), table_name='ingestion_runs')
    op.drop_index(op.f('ix_ingestion_runs_source_identifier'), table_name='ingestion_runs')
    op.drop_index(op.f('ix_ingestion_runs_provider'), table_name='ingestion_runs')
    op.drop_index(op.f('ix_ingestion_runs_pipeline_type'), table_name='ingestion_runs')
    op.drop_index(op.f('ix_ingestion_runs_id'), table_name='ingestion_runs')
    op.drop_table('ingestion_runs')

    op.drop_index('idx_rainfall_forecast_grids_geom_bounds', table_name='rainfall_forecast_grids', postgresql_using='gist')
    op.drop_index(op.f('ix_rainfall_forecast_grids_quality_status'), table_name='rainfall_forecast_grids')
    op.drop_index(op.f('ix_rainfall_forecast_grids_lead_time_minutes'), table_name='rainfall_forecast_grids')
    op.drop_index(op.f('ix_rainfall_forecast_grids_valid_time'), table_name='rainfall_forecast_grids')
    op.drop_index(op.f('ix_rainfall_forecast_grids_initialization_time'), table_name='rainfall_forecast_grids')
    op.drop_index(op.f('ix_rainfall_forecast_grids_provider'), table_name='rainfall_forecast_grids')
    op.drop_index(op.f('ix_rainfall_forecast_grids_dataset_identifier'), table_name='rainfall_forecast_grids')
    op.drop_index(op.f('ix_rainfall_forecast_grids_id'), table_name='rainfall_forecast_grids')
    op.drop_table('rainfall_forecast_grids')

    op.drop_index('idx_rainfall_observation_grids_geom_bounds', table_name='rainfall_observation_grids', postgresql_using='gist')
    op.drop_index(op.f('ix_rainfall_observation_grids_quality_status'), table_name='rainfall_observation_grids')
    op.drop_index(op.f('ix_rainfall_observation_grids_observation_end'), table_name='rainfall_observation_grids')
    op.drop_index(op.f('ix_rainfall_observation_grids_observation_start'), table_name='rainfall_observation_grids')
    op.drop_index(op.f('ix_rainfall_observation_grids_provider'), table_name='rainfall_observation_grids')
    op.drop_index(op.f('ix_rainfall_observation_grids_dataset_identifier'), table_name='rainfall_observation_grids')
    op.drop_index(op.f('ix_rainfall_observation_grids_id'), table_name='rainfall_observation_grids')
    op.drop_table('rainfall_observation_grids')
