"""0002_phase2_geospatial

Revision ID: 0002_phase2_geospatial
Revises: 0001_phase0_initial
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

revision: str = '0002_phase2_geospatial'
down_revision: Union[str, None] = '0001_phase0_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create study_areas table
    op.create_table(
        'study_areas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('geom', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=False), nullable=False),
        sa.Column('srid', sa.Integer(), nullable=False, server_default='4326'),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index(op.f('ix_study_areas_name'), 'study_areas', ['name'], unique=False)
    op.create_index('idx_study_areas_geom', 'study_areas', ['geom'], postgresql_using='gist')

    # 2. Create raster_metadata table
    op.create_table(
        'raster_metadata',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('dataset_identifier', sa.String(length=128), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False),
        sa.Column('acquisition_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ingestion_time', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('crs', sa.String(length=64), nullable=False),
        sa.Column('geom_bounds', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=False), nullable=False),
        sa.Column('resolution_x', sa.Float(), nullable=False),
        sa.Column('resolution_y', sa.Float(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('nodata', sa.Float(), nullable=True),
        sa.Column('units', sa.String(length=32), nullable=True),
        sa.Column('version', sa.String(length=32), nullable=False, server_default='1.0'),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('storage_pointer', sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raster_metadata_id'), 'raster_metadata', ['id'], unique=False)
    op.create_index(op.f('ix_raster_metadata_dataset_identifier'), 'raster_metadata', ['dataset_identifier'], unique=True)
    op.create_index(op.f('ix_raster_metadata_source'), 'raster_metadata', ['source'], unique=False)
    op.create_index('idx_raster_metadata_geom_bounds', 'raster_metadata', ['geom_bounds'], postgresql_using='gist')

    # 3. Create vector_features table
    op.create_table(
        'vector_features',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('geom', Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=False), nullable=False),
        sa.Column('srid', sa.Integer(), nullable=False, server_default='4326'),
        sa.Column('feature_properties', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vector_features_id'), 'vector_features', ['id'], unique=False)
    op.create_index(op.f('ix_vector_features_category'), 'vector_features', ['category'], unique=False)
    op.create_index('idx_vector_features_geom', 'vector_features', ['geom'], postgresql_using='gist')


def downgrade() -> None:
    op.drop_index('idx_vector_features_geom', table_name='vector_features', postgresql_using='gist')
    op.drop_index(op.f('ix_vector_features_category'), table_name='vector_features')
    op.drop_index(op.f('ix_vector_features_id'), table_name='vector_features')
    op.drop_table('vector_features')

    op.drop_index('idx_raster_metadata_geom_bounds', table_name='raster_metadata', postgresql_using='gist')
    op.drop_index(op.f('ix_raster_metadata_source'), table_name='raster_metadata')
    op.drop_index(op.f('ix_raster_metadata_dataset_identifier'), table_name='raster_metadata')
    op.drop_index(op.f('ix_raster_metadata_id'), table_name='raster_metadata')
    op.drop_table('raster_metadata')

    op.drop_index('idx_study_areas_geom', table_name='study_areas', postgresql_using='gist')
    op.drop_index(op.f('ix_study_areas_name'), table_name='study_areas')
    op.drop_table('study_areas')
