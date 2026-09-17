"""
SQLAlchemy PostGIS Models for Phase 11 Critical Access Guardian.

Defines persistence tables for:
1. CriticalFacility — Critical infrastructure facilities and verification metadata.
2. CriticalAccessRun — Audit logs of facility access runs.
3. CriticalAccessResult — Time-slice accessibility results per canonical Digital Twin slice.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class CriticalFacility(Base):
    """Critical facility entity table."""

    __tablename__ = "critical_facilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(256), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    source = Column(String(128), nullable=False)
    source_id = Column(String(128), nullable=True)
    source_type = Column(String(64), nullable=False)
    verification_status = Column(String(64), nullable=False)
    operational_status = Column(String(64), nullable=False, default="UNKNOWN")
    provenance = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CriticalAccessRun(Base):
    """Audit log table for Critical Access Guardian analysis runs."""

    __tablename__ = "critical_access_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_identifier = Column(String(128), nullable=False, index=True)
    facility_id = Column(String(128), nullable=False)
    digital_twin_run_id = Column(String(128), nullable=False)
    routing_run_id = Column(String(128), nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lon = Column(Float, nullable=False)
    current_access_status = Column(String(64), nullable=False)
    modeled_loss_of_access_min = Column(Integer, nullable=True)
    time_to_loss_of_access_min = Column(Integer, nullable=True)
    recommendation = Column(String(64), nullable=False)
    explanation = Column(Text, nullable=False)
    provenance = Column(JSONB, nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="COMPLETED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CriticalAccessResult(Base):
    """Time-slice accessibility detail per canonical Digital Twin slice."""

    __tablename__ = "critical_access_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    access_run_id = Column(String(128), nullable=False, index=True)
    facility_id = Column(String(128), nullable=False)
    minutes_from_start = Column(Integer, nullable=False)
    access_status = Column(String(64), nullable=False)
    route_id = Column(String(128), nullable=False)
    peak_severity = Column(String(32), nullable=False)
    usable_travel_window_min = Column(Integer, nullable=True)
