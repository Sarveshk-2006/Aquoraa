"""0005_phase5_drainage

Revision ID: 0005_phase5_drainage
Revises: 0004_phase4_terrain
Create Date: 2026-09-12 01:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

revision: str = '0005_phase5_drainage'
down_revision: Union[str, None] = '0004_phase4_terrain'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create drainage_datasets table
    op.create_table(
        'drainage_datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_identifier', sa.String(length=128), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False),
        sa.Column('crs', sa.String(length=64), nullable=False),
        sa.Column('geom_bounds', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=False),
        sa.Column('feature_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('node_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('link_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence', sa.String(length=32), nullable=False, server_default='AUTHORITATIVE'),
        sa.Column('is_test_fixture', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('storage_pointer', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drainage_datasets_dataset_identifier'), 'drainage_datasets', ['dataset_identifier'], unique=True)
    op.create_index(op.f('ix_drainage_datasets_source'), 'drainage_datasets', ['source'], unique=False)

    # 2. Create drainage_nodes table
    op.create_table(
        'drainage_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', sa.String(length=128), nullable=False),
        sa.Column('node_id', sa.String(length=128), nullable=False),
        sa.Column('node_type', sa.String(length=32), nullable=False, server_default='INLET'),
        sa.Column('elevation_m', sa.Float(), nullable=True),
        sa.Column('invert_elevation_m', sa.Float(), nullable=True),
        sa.Column('ground_elevation_m', sa.Float(), nullable=True),
        sa.Column('confidence', sa.String(length=32), nullable=False, server_default='AUTHORITATIVE'),
        sa.Column('srid', sa.Integer(), nullable=False, server_default='4326'),
        sa.Column('geom', Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drainage_nodes_dataset_id'), 'drainage_nodes', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_drainage_nodes_node_id'), 'drainage_nodes', ['node_id'], unique=False)
    op.create_index(op.f('ix_drainage_nodes_node_type'), 'drainage_nodes', ['node_type'], unique=False)

    # 3. Create drainage_links table
    op.create_table(
        'drainage_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', sa.String(length=128), nullable=False),
        sa.Column('link_id', sa.String(length=128), nullable=False),
        sa.Column('from_node_id', sa.String(length=128), nullable=False),
        sa.Column('to_node_id', sa.String(length=128), nullable=False),
        sa.Column('link_type', sa.String(length=32), nullable=False, server_default='PIPE'),
        sa.Column('length_m', sa.Float(), nullable=False),
        sa.Column('diameter_m', sa.Float(), nullable=True),
        sa.Column('width_m', sa.Float(), nullable=True),
        sa.Column('height_m', sa.Float(), nullable=True),
        sa.Column('slope', sa.Float(), nullable=True),
        sa.Column('material', sa.String(length=64), nullable=True),
        sa.Column('capacity_m3s', sa.Float(), nullable=True),
        sa.Column('roughness', sa.Float(), nullable=True),
        sa.Column('direction_status', sa.String(length=32), nullable=False, server_default='KNOWN'),
        sa.Column('confidence', sa.String(length=32), nullable=False, server_default='AUTHORITATIVE'),
        sa.Column('srid', sa.Integer(), nullable=False, server_default='4326'),
        sa.Column('geom', Geometry(geometry_type='LINESTRING', srid=4326, spatial_index=True), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drainage_links_dataset_id'), 'drainage_links', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_drainage_links_link_id'), 'drainage_links', ['link_id'], unique=False)
    op.create_index(op.f('ix_drainage_links_from_node_id'), 'drainage_links', ['from_node_id'], unique=False)
    op.create_index(op.f('ix_drainage_links_to_node_id'), 'drainage_links', ['to_node_id'], unique=False)

    # 4. Create drainage_networks table
    op.create_table(
        'drainage_networks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', sa.String(length=128), nullable=False),
        sa.Column('analysis_crs', sa.String(length=64), nullable=False),
        sa.Column('nodes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('links_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('connected_components_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('outfalls_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('validation_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drainage_networks_dataset_id'), 'drainage_networks', ['dataset_id'], unique=False)

    # 5. Create drainage_processing_runs table
    op.create_table(
        'drainage_processing_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', sa.String(length=128), nullable=False),
        sa.Column('network_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('processing_type', sa.String(length=64), nullable=False, server_default='DRAINAGE_NETWORK_NORMALIZATION'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('analysis_crs', sa.String(length=64), nullable=False),
        sa.Column('snap_tolerance_m', sa.Float(), nullable=False, server_default='5.0'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drainage_processing_runs_dataset_id'), 'drainage_processing_runs', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_drainage_processing_runs_network_id'), 'drainage_processing_runs', ['network_id'], unique=False)
    op.create_index(op.f('ix_drainage_processing_runs_status'), 'drainage_processing_runs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_drainage_processing_runs_status'), table_name='drainage_processing_runs')
    op.drop_index(op.f('ix_drainage_processing_runs_network_id'), table_name='drainage_processing_runs')
    op.drop_index(op.f('ix_drainage_processing_runs_dataset_id'), table_name='drainage_processing_runs')
    op.drop_table('drainage_processing_runs')

    op.drop_index(op.f('ix_drainage_networks_dataset_id'), table_name='drainage_networks')
    op.drop_table('drainage_networks')

    op.drop_index(op.f('ix_drainage_links_to_node_id'), table_name='drainage_links')
    op.drop_index(op.f('ix_drainage_links_from_node_id'), table_name='drainage_links')
    op.drop_index(op.f('ix_drainage_links_link_id'), table_name='drainage_links')
    op.drop_index(op.f('ix_drainage_links_dataset_id'), table_name='drainage_links')
    op.drop_table('drainage_links')

    op.drop_index(op.f('ix_drainage_nodes_node_type'), table_name='drainage_nodes')
    op.drop_index(op.f('ix_drainage_nodes_node_id'), table_name='drainage_nodes')
    op.drop_index(op.f('ix_drainage_nodes_dataset_id'), table_name='drainage_nodes')
    op.drop_table('drainage_nodes')

    op.drop_index(op.f('ix_drainage_datasets_source'), table_name='drainage_datasets')
    op.drop_index(op.f('ix_drainage_datasets_dataset_identifier'), table_name='drainage_datasets')
    op.drop_table('drainage_datasets')
