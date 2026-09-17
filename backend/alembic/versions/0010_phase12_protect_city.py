"""0010_phase12_protect_city

Revision ID: 0010_phase12_protect_city
Revises: 0009_phase11_critical_access
Create Date: 2026-09-13 01:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0010_phase12_protect_city'
down_revision: Union[str, None] = '0009_phase11_critical_access'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create intervention_candidates table
    op.create_table(
        'intervention_candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_id', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('candidate_type', sa.String(length=64), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False),
        sa.Column('source_id', sa.String(length=128), nullable=True),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('verification_status', sa.String(length=64), nullable=False),
        sa.Column('provider_mode', sa.String(length=64), nullable=False),
        sa.Column('environment', sa.String(length=64), nullable=False),
        sa.Column('affected_asset_type', sa.String(length=128), nullable=True),
        sa.Column('affected_asset_id', sa.String(length=128), nullable=True),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intervention_candidates_candidate_id'), 'intervention_candidates', ['candidate_id'], unique=True)

    # 2. Create protect_city_runs table
    op.create_table(
        'protect_city_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_identifier', sa.String(length=128), nullable=False),
        sa.Column('digital_twin_run_id', sa.String(length=128), nullable=False),
        sa.Column('routing_run_id', sa.String(length=128), nullable=True),
        sa.Column('critical_access_run_id', sa.String(length=128), nullable=True),
        sa.Column('minimum_priority', sa.String(length=32), nullable=False),
        sa.Column('total_candidates', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_protect_city_runs_run_identifier'), 'protect_city_runs', ['run_identifier'], unique=True)

    # 3. Create protect_city_recommendations table
    op.create_table(
        'protect_city_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_identifier', sa.String(length=128), nullable=False),
        sa.Column('candidate_id', sa.String(length=128), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('intervention_type', sa.String(length=64), nullable=False),
        sa.Column('first_threat_minutes', sa.Integer(), nullable=True),
        sa.Column('first_high_severity_minutes', sa.Integer(), nullable=True),
        sa.Column('peak_severity', sa.String(length=32), nullable=False),
        sa.Column('peak_severity_minutes', sa.Integer(), nullable=True),
        sa.Column('expected_benefit', sa.String(length=32), nullable=False),
        sa.Column('feasibility_status', sa.String(length=32), nullable=False),
        sa.Column('uncertainty_status', sa.String(length=32), nullable=False),
        sa.Column('affected_route_count', sa.Integer(), nullable=False),
        sa.Column('affected_critical_facility_count', sa.Integer(), nullable=False),
        sa.Column('priority_component_breakdown_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('warnings_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_protect_city_recommendations_run_identifier'), 'protect_city_recommendations', ['run_identifier'], unique=False)
    op.create_index(op.f('ix_protect_city_recommendations_candidate_id'), 'protect_city_recommendations', ['candidate_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_protect_city_recommendations_candidate_id'), table_name='protect_city_recommendations')
    op.drop_index(op.f('ix_protect_city_recommendations_run_identifier'), table_name='protect_city_recommendations')
    op.drop_table('protect_city_recommendations')
    op.drop_index(op.f('ix_protect_city_runs_run_identifier'), table_name='protect_city_runs')
    op.drop_table('protect_city_runs')
    op.drop_index(op.f('ix_intervention_candidates_candidate_id'), table_name='intervention_candidates')
    op.drop_table('intervention_candidates')
