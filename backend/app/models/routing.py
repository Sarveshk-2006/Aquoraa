"""
SQLAlchemy PostGIS Models for Phase 10 Flood-Aware Routing & Travel Window.

Stores routing run metadata, candidate route geometries, risk metrics,
modeled onset timing, travel windows, and recommendation audit logs.
"""

import datetime
import uuid
from typing import Optional, Any

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RoutingRun(Base):
    """
    Persistent record of a Flood-Aware Routing analysis run.
    """
    __tablename__ = "routing_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    run_identifier: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    digital_twin_run_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_mode: Mapped[str] = mapped_column(String(64), nullable=False)

    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lon: Mapped[float] = mapped_column(Float, nullable=False)
    dest_lat: Mapped[float] = mapped_column(Float, nullable=False)
    dest_lon: Mapped[float] = mapped_column(Float, nullable=False)

    recommendation: Mapped[str] = mapped_column(String(64), nullable=False)
    usable_travel_window_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    route_flood_onset_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_travel_time_min: Mapped[float] = mapped_column(Float, nullable=False)

    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPLETED")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class RouteCandidate(Base):
    """
    Candidate route geometry and travel window metrics for a routing run.
    """
    __tablename__ = "route_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    routing_run_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    route_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_duration_s: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(64), nullable=False)
    usable_travel_window_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    route_flood_onset_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    peak_severity: Mapped[str] = mapped_column(String(32), nullable=False)

    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    geometry_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class RouteExposure(Base):
    """
    Time-slice spatial exposure record along a candidate route for each canonical Digital Twin slice.
    """
    __tablename__ = "route_exposures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    routing_run_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    route_id: Mapped[str] = mapped_column(String(128), nullable=False)
    minutes_from_start: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(String(64), nullable=False)
    affected_distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    affected_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    peak_severity: Mapped[str] = mapped_column(String(32), nullable=False)
    peak_water_depth_m: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
