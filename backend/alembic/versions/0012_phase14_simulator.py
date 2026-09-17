"""Phase 14 Aquora Simulator Database Tables.

Revision ID: 0012_phase14_simulator
Revises: 0011_phase13_ground_truth
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0012_phase14_simulator"
down_revision: str | None = "0011_phase13_ground_truth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. simulator_scenarios
    op.create_table(
        "simulator_scenarios",
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("baseline_run_id", sa.String(length=64), nullable=False),
        sa.Column("scenario_type", sa.String(length=64), nullable=False, server_default="RAINFALL_MULTIPLIER"),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("assumptions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("scenario_id"),
    )
    op.create_index("idx_sim_scen_status", "simulator_scenarios", ["status"])
    op.create_index("idx_sim_scen_baseline", "simulator_scenarios", ["baseline_run_id"])

    # 2. simulator_runs
    op.create_table(
        "simulator_runs",
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("baseline_run_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="RUNNING"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("engine_version", sa.String(length=64), nullable=False, server_default="Phase6_FloodEngine_v1"),
        sa.Column("config_version", sa.String(length=64), nullable=False, server_default="Phase14_SimulatorConfig_v1"),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["scenario_id"], ["simulator_scenarios.scenario_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index("idx_sim_run_scen", "simulator_runs", ["scenario_id"])

    # 3. simulator_artifacts
    op.create_table(
        "simulator_artifacts",
        sa.Column("artifact_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False, server_default="RASTER_SLICE"),
        sa.Column("storage_reference", sa.String(length=512), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("crs", sa.String(length=32), nullable=False, server_default="EPSG:32643"),
        sa.Column("transform", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("width", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("nodata", sa.Float(), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["run_id"], ["simulator_runs.run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("artifact_id"),
    )

    # 4. simulator_comparisons
    op.create_table(
        "simulator_comparisons",
        sa.Column("comparison_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("slice_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("baseline_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scenario_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("deltas", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("outcome", sa.String(length=32), nullable=False, server_default="NO_SIGNIFICANT_CHANGE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["run_id"], ["simulator_runs.run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("comparison_id"),
    )

    # 5. simulator_diagnostics
    op.create_table(
        "simulator_diagnostics",
        sa.Column("diagnostic_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="VALID"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["run_id"], ["simulator_runs.run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("diagnostic_id"),
    )


def downgrade() -> None:
    op.drop_table("simulator_diagnostics")
    op.drop_table("simulator_comparisons")
    op.drop_table("simulator_artifacts")
    op.drop_table("simulator_runs")
    op.drop_table("simulator_scenarios")
