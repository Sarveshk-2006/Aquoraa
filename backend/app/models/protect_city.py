"""
SQLAlchemy PostGIS Models for Phase 12 Protect the City.

Defines persistence tables for:
1. InterventionCandidate — Intervention opportunity assets and candidate metadata.
2. ProtectCityRun — Execution audit log for Protect the City analysis runs.
3. ProtectCityRecommendation — Prioritized recommendation records per intervention candidate.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class InterventionCandidate(Base):
    """Intervention opportunity asset entity table."""

    __tablename__ = "intervention_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(256), nullable=False)
    candidate_type = Column(String(64), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    source = Column(String(128), nullable=False)
    source_id = Column(String(128), nullable=True)
    source_type = Column(String(64), nullable=False, default="SYNTHETIC")
    verification_status = Column(String(64), nullable=False, default="UNVERIFIED")
    provider_mode = Column(String(64), nullable=False, default="SYNTHETIC")
    environment = Column(String(64), nullable=False, default="DEVELOPMENT_ONLY")
    affected_asset_type = Column(String(128), nullable=True)
    affected_asset_id = Column(String(128), nullable=True)
    provenance = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ProtectCityRun(Base):
    """Persistent audit log of a Protect the City analysis execution."""

    __tablename__ = "protect_city_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_identifier = Column(String(128), unique=True, nullable=False, index=True)
    digital_twin_run_id = Column(String(128), nullable=False)
    routing_run_id = Column(String(128), nullable=True)
    critical_access_run_id = Column(String(128), nullable=True)
    minimum_priority = Column(String(32), nullable=False, default="HIGH")
    total_candidates = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="COMPLETED")
    provenance = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ProtectCityRecommendation(Base):
    """Prioritized recommendation per candidate for a Protect the City run."""

    __tablename__ = "protect_city_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_identifier = Column(String(128), nullable=False, index=True)
    candidate_id = Column(String(128), nullable=False, index=True)
    priority = Column(String(32), nullable=False)
    priority_score = Column(Float, nullable=False, default=0.0)
    intervention_type = Column(String(64), nullable=False)
    first_threat_minutes = Column(Integer, nullable=True)
    first_high_severity_minutes = Column(Integer, nullable=True)
    peak_severity = Column(String(32), nullable=False, default="DRY")
    peak_severity_minutes = Column(Integer, nullable=True)
    expected_benefit = Column(String(32), nullable=False, default="UNKNOWN")
    feasibility_status = Column(String(32), nullable=False, default="UNKNOWN")
    uncertainty_status = Column(String(32), nullable=False, default="MEDIUM")
    affected_route_count = Column(Integer, nullable=False, default=0)
    affected_critical_facility_count = Column(Integer, nullable=False, default=0)
    priority_component_breakdown_json = Column(JSONB, nullable=True)
    explanation = Column(Text, nullable=False)
    warnings_json = Column(JSONB, nullable=True)
    provenance = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
