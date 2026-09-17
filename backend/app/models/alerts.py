"""
Phase 15 Alerts, Explainability, and Audit SQLAlchemy ORM Models.
"""

from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="INFO", index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE", index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    affected_entity_type: Mapped[str] = mapped_column(String(64), nullable=False, default="CITY_REGION")
    affected_entity_id: Mapped[str] = mapped_column(String(128), nullable=False, default="ALL")
    condition_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_phase: Mapped[str] = mapped_column(String(32), nullable=False, default="Phase9")
    source_run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sources: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    input_completeness: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    model_status: Mapped[str] = mapped_column(String(64), nullable=False, default="PROTOTYPE_ONLY")
    evidence_strength: Mapped[str] = mapped_column(String(64), nullable=False, default="UNVERIFIED")
    uncertainty_status: Mapped[str] = mapped_column(String(64), nullable=False, default="MEDIUM")
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    governance_notice: Mapped[str] = mapped_column(Text, nullable=False)
    configuration_version: Mapped[str] = mapped_column(String(64), nullable=False, default="v1")
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    resolution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suppressed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    suppressed_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    suppression_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    evidences: Mapped[list["AlertEvidence"]] = relationship(
        "AlertEvidence", back_populates="alert", cascade="all, delete-orphan"
    )
    explainability_steps: Mapped[list["ExplainabilityStep"]] = relationship(
        "ExplainabilityStep", back_populates="alert", cascade="all, delete-orphan", order_by="ExplainabilityStep.sequence"
    )
    audit_events: Mapped[list["AlertAuditEvent"]] = relationship(
        "AlertAuditEvent", back_populates="alert", cascade="all, delete-orphan", order_by="AlertAuditEvent.timestamp"
    )


class AlertEvidence(Base):
    __tablename__ = "alert_evidence"

    evidence_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(64), ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False)
    source_phase: Mapped[str] = mapped_column(String(32), nullable=False)
    source_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_artifact_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    units: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_strength: Mapped[str] = mapped_column(String(32), nullable=False, default="UNVERIFIED")
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="evidences")


class ExplainabilityStep(Base):
    __tablename__ = "alert_explainability_steps"

    step_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(64), ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # WHAT, WHY, WHEN, WHERE, HOW_CERTAIN, WHAT_SHOULD_I_DO, EVIDENCE
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    source_phase: Mapped[str] = mapped_column(String(32), nullable=False)
    source_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_metric: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    units: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    slice_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="explainability_steps")


class AlertAuditEvent(Base):
    __tablename__ = "alert_audit_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(64), ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False, default="SYSTEM")
    actor_reference: Mapped[str] = mapped_column(String(128), nullable=False, default="SYSTEM_AUTO")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_run_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="audit_events")


class AlertConfiguration(Base):
    __tablename__ = "alert_configurations"

    configuration_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    configuration_version: Mapped[str] = mapped_column(String(64), nullable=False)
    thresholds: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
