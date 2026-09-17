"""
SQLAlchemy PostGIS Models for Phase 9 Flood Digital Twin.

Tracks Digital Twin run execution metadata, provenance, 0-180 min horizon timesteps,
input completeness, prototype ML score references, and file-backed map artifacts.
"""

import datetime
import uuid
from typing import Optional, Any

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DigitalTwinRun(Base):
    """
    Persistent record of a Flood Digital Twin execution run.
    """
    __tablename__ = "digital_twin_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    run_identifier: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    study_area_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)

    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    simulation_start_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    horizon_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=180)
    timestep_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    total_timesteps: Mapped[int] = mapped_column(Integer, nullable=False, default=7)

    rainfall_source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    forecast_source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    terrain_dataset_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    drainage_dataset_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    physical_engine_version: Mapped[str] = mapped_column(String(32), nullable=False, default="Phase6_Deterministic_D8")
    ml_calibration_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default="Phase8_XGBoost_Prototype_V1")

    input_completeness: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    output_directory: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DigitalTwinArtifact(Base):
    """
    Reference table for file-backed raster/JSON outputs produced by a Digital Twin run.
    """
    __tablename__ = "digital_twin_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    run_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    minutes_from_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
