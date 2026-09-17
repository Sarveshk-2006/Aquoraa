"""0004_phase4_terrain

Revision ID: 0004_phase4_terrain
Revises: 0003_phase3_rainfall
Create Date: 2026-09-12 01:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

revision: str = '0004_phase4_terrain'
down_revision: Union[str, None] = '0003_phase3_rainfall'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create terrain_datasets table
    op.create_table(
        'terrain_datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_identifier', sa.String(length=128), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False),
        sa.Column('crs', sa.String(length=64), nullable=False),
        sa.Column('geom_bounds', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=False),
        sa.Column('resolution_x', sa.Float(), nullable=False),
        sa.Column('resolution_y', sa.Float(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('vertical_units', sa.String(length=32), nullable=False, server_default='meters'),
        sa.Column('nodata', sa.Float(), nullable=True),
        sa.Column('is_test_fixture', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('storage_pointer', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terrain_datasets_dataset_identifier'), 'terrain_datasets', ['dataset_identifier'], unique=True)
    op.create_index(op.f('ix_terrain_datasets_source'), 'terrain_datasets', ['source'], unique=False)

    # 2. Create catchments table
    op.create_table(
        'catchments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', sa.String(length=128), nullable=False),
        sa.Column('original_pour_point_x', sa.Float(), nullable=False),
        sa.Column('original_pour_point_y', sa.Float(), nullable=False),
        sa.Column('snapped_pour_point_x', sa.Float(), nullable=False),
        sa.Column('snapped_pour_point_y', sa.Float(), nullable=False),
        sa.Column('snapped', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('snap_distance_m', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('contributing_cells_count', sa.Integer(), nullable=False),
        sa.Column('area_m2', sa.Float(), nullable=False),
        sa.Column('area_km2', sa.Float(), nullable=False),
        sa.Column('srid', sa.Integer(), nullable=False, server_default='4326'),
        sa.Column('geom', Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=True), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_catchments_dataset_id'), 'catchments', ['dataset_id'], unique=False)

    # 3. Create terrain_processing_runs table
    op.create_table(
        'terrain_processing_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', sa.String(length=128), nullable=False),
        sa.Column('processing_type', sa.String(length=64), nullable=False, server_default='TERRAIN_DERIVATIVES'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('analysis_crs', sa.String(length=64), nullable=False),
        sa.Column('surface_drainage_threshold_m2', sa.Float(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terrain_processing_runs_dataset_id'), 'terrain_processing_runs', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_terrain_processing_runs_status'), 'terrain_processing_runs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_terrain_processing_runs_status'), table_name='terrain_processing_runs')
    op.drop_index(op.f('ix_terrain_processing_runs_dataset_id'), table_name='terrain_processing_runs')
    op.drop_table('terrain_processing_runs')

    op.drop_index(op.f('ix_catchments_dataset_id'), table_name='catchments')
    op.drop_table('catchments')

    op.drop_index(op.f('ix_terrain_datasets_source'), table_name='terrain_datasets')
    op.drop_index(op.f('ix_terrain_datasets_dataset_identifier'), table_name='terrain_datasets')
    op.drop_table('terrain_datasets')
