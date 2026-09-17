"""Phase 13 Ground Truth + Photo Verification Database Tables.

Revision ID: 0011_phase13_ground_truth
Revises: 0010_phase12_protect_city
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0011_phase13_ground_truth"
down_revision: str | None = "0010_phase12_protect_city"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. flood_observations
    op.create_table(
        "flood_observations",
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("observation_type", sa.String(length=64), nullable=False, server_default="FLOOD_REPORT"),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location_source", sa.String(length=32), nullable=False, server_default="MANUAL"),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="COMMUNITY"),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("observer_type", sa.String(length=32), nullable=False, server_default="COMMUNITY"),
        sa.Column("observer_reference", sa.String(length=128), nullable=True),
        sa.Column("flood_presence", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("water_depth_class", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("road_passability", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("media_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verification_state", sa.String(length=32), nullable=False, server_default="UNVERIFIED"),
        sa.Column("evidence_strength", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("incident_id", sa.String(length=64), nullable=True),
        sa.Column("model_comparison_status", sa.String(length=64), nullable=False, server_default="UNKNOWN"),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("observation_id"),
    )
    op.create_index("idx_flood_obs_state", "flood_observations", ["verification_state"])
    op.create_index("idx_flood_obs_incident", "flood_observations", ["incident_id"])
    op.create_index("idx_flood_obs_coords", "flood_observations", ["latitude", "longitude"])

    # 2. observation_media
    op.create_table(
        "observation_media",
        sa.Column("media_id", sa.String(length=64), nullable=False),
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=16), nullable=False, server_default="PHOTO"),
        sa.Column("storage_reference", sa.String(length=512), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mime_type", sa.String(length=64), nullable=False, server_default="image/jpeg"),
        sa.Column("metadata_status", sa.String(length=32), nullable=False, server_default="VALIDATED"),
        sa.Column("processing_status", sa.String(length=32), nullable=False, server_default="PROCESSED"),
        sa.Column("image_quality", sa.String(length=32), nullable=False, server_default="SUFFICIENT"),
        sa.Column("cv_status", sa.String(length=32), nullable=False, server_default="DEVELOPMENT_ONLY"),
        sa.Column("cv_assessment", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["observation_id"], ["flood_observations.observation_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("media_id"),
    )
    op.create_index("idx_obs_media_obs_id", "observation_media", ["observation_id"])

    # 3. flood_incidents
    op.create_table(
        "flood_incidents",
        sa.Column("incident_id", sa.String(length=64), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observation_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unique_source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("verification_state", sa.String(length=32), nullable=False, server_default="UNVERIFIED"),
        sa.Column("evidence_strength", sa.String(length=32), nullable=False, server_default="WEAK"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("incident_id"),
    )

    # 4. observation_comparisons
    op.create_table(
        "observation_comparisons",
        sa.Column("comparison_id", sa.String(length=64), nullable=False),
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("digital_twin_run_id", sa.String(length=64), nullable=False),
        sa.Column("model_slice_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observation_elapsed_minutes", sa.Float(), nullable=True),
        sa.Column("observation_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_difference_minutes", sa.Float(), nullable=True),
        sa.Column("spatial_distance_m", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("observation_state", sa.String(length=64), nullable=False),
        sa.Column("model_state", sa.String(length=64), nullable=False),
        sa.Column("comparison_status", sa.String(length=64), nullable=False, server_default="UNKNOWN"),
        sa.Column("evidence_strength", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("verification_state", sa.String(length=32), nullable=False, server_default="UNVERIFIED"),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["observation_id"], ["flood_observations.observation_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("comparison_id"),
    )
    op.create_index("idx_obs_comp_obs", "observation_comparisons", ["observation_id"])
    op.create_index("idx_obs_comp_run", "observation_comparisons", ["digital_twin_run_id"])

    # 5. ground_truth_runs
    op.create_table(
        "ground_truth_runs",
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("digital_twin_run_id", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="RUNNING"),
        sa.Column("observation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("incident_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comparison_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_mode", sa.String(length=32), nullable=False, server_default="LOCAL"),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("run_id"),
    )

    # 6. ground_truth_evidence
    op.create_table(
        "ground_truth_evidence",
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False, server_default="PHOTO"),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="COMMUNITY"),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_strength", sa.String(length=32), nullable=False, server_default="MODERATE"),
        sa.Column("storage_reference", sa.String(length=512), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["observation_id"], ["flood_observations.observation_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("evidence_id"),
    )


def downgrade() -> None:
    op.drop_table("ground_truth_evidence")
    op.drop_table("ground_truth_runs")
    op.drop_table("observation_comparisons")
    op.drop_table("flood_incidents")
    op.drop_table("observation_media")
    op.drop_table("flood_observations")
