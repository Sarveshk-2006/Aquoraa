"""Phase 15 Aquora Alerts, Explainability, and Audit Database Tables.

Revision ID: 0013_phase15_alerts
Revises: 0012_phase14_simulator
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0013_phase15_alerts"
down_revision: str | None = "0012_phase14_simulator"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. alerts
    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.String(length=64), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="INFO"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("affected_entity_type", sa.String(length=64), nullable=False, server_default="CITY_REGION"),
        sa.Column("affected_entity_id", sa.String(length=128), nullable=False, server_default="ALL"),
        sa.Column("condition_key", sa.String(length=128), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("source_phase", sa.String(length=32), nullable=False, server_default="Phase9"),
        sa.Column("source_run_id", sa.String(length=64), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("input_completeness", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("model_status", sa.String(length=64), nullable=False, server_default="PROTOTYPE_ONLY"),
        sa.Column("evidence_strength", sa.String(length=64), nullable=False, server_default="UNVERIFIED"),
        sa.Column("uncertainty_status", sa.String(length=64), nullable=False, server_default="MEDIUM"),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("governance_notice", sa.Text(), nullable=False),
        sa.Column("configuration_version", sa.String(length=64), nullable=False, server_default="v1"),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.String(length=128), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=128), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.Column("suppressed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suppressed_by", sa.String(length=128), nullable=True),
        sa.Column("suppression_reason", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("alert_id"),
    )
    op.create_index("idx_alerts_type", "alerts", ["alert_type"])
    op.create_index("idx_alerts_severity", "alerts", ["severity"])
    op.create_index("idx_alerts_status", "alerts", ["status"])
    op.create_index("idx_alerts_fingerprint", "alerts", ["fingerprint"])
    op.create_index("idx_alerts_condition", "alerts", ["condition_key"])
    op.create_index("idx_alerts_source_run", "alerts", ["source_run_id"])

    # 2. alert_evidence
    op.create_table(
        "alert_evidence",
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("alert_id", sa.String(length=64), nullable=False),
        sa.Column("source_phase", sa.String(length=32), nullable=False),
        sa.Column("source_run_id", sa.String(length=64), nullable=False),
        sa.Column("source_artifact_id", sa.String(length=64), nullable=True),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("units", sa.String(length=32), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_strength", sa.String(length=32), nullable=False, server_default="UNVERIFIED"),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.alert_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("evidence_id"),
    )
    op.create_index("idx_evidence_alert", "alert_evidence", ["alert_id"])

    # 3. alert_explainability_steps
    op.create_table(
        "alert_explainability_steps",
        sa.Column("step_id", sa.String(length=64), nullable=False),
        sa.Column("alert_id", sa.String(length=64), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("source_phase", sa.String(length=32), nullable=False),
        sa.Column("source_run_id", sa.String(length=64), nullable=False),
        sa.Column("source_metric", sa.String(length=64), nullable=True),
        sa.Column("source_value", sa.Float(), nullable=True),
        sa.Column("units", sa.String(length=32), nullable=True),
        sa.Column("slice_minutes", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.alert_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("step_id"),
    )
    op.create_index("idx_explain_alert_seq", "alert_explainability_steps", ["alert_id", "sequence"])

    # 4. alert_audit_events
    op.create_table(
        "alert_audit_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("alert_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("previous_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("actor_type", sa.String(length=32), nullable=False, server_default="SYSTEM"),
        sa.Column("actor_reference", sa.String(length=128), nullable=False, server_default="SYSTEM_AUTO"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("source_run_id", sa.String(length=64), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.alert_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("idx_alert_audit_alert", "alert_audit_events", ["alert_id"])

    # 5. alert_configurations
    op.create_table(
        "alert_configurations",
        sa.Column("configuration_id", sa.String(length=64), nullable=False),
        sa.Column("configuration_version", sa.String(length=64), nullable=False),
        sa.Column("thresholds", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("configuration_id"),
    )


def downgrade() -> None:
    op.drop_table("alert_configurations")
    op.drop_table("alert_audit_events")
    op.drop_table("alert_explainability_steps")
    op.drop_table("alert_evidence")
    op.drop_table("alerts")
