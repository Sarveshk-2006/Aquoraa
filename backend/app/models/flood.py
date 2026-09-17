"""
SQLAlchemy PostGIS Models for Phase 6 Flood Simulation Engine.

Tracks simulation run execution parameters, configuration hashes, input completeness,
mass balance errors, output file artifact manifests, and per-timestep diagnostics.
"""

import datetime
import uuid
from typing import Optional, Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FloodSimulationRun(Base):
    """
    Persistent record of a flood simulation execution run.
    """
    __tablename__ = "flood_simulation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    simulation_identifier: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
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
    start_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    horizon_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=180)
    timestep_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    total_timesteps: Mapped[int] = mapped_column(Integer, nullable=False, default=19)

    rainfall_source_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    forecast_source_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    terrain_dataset_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    drainage_dataset_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    configuration_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False, default="0.6.0-phase6")
    analysis_crs: Mapped[str] = mapped_column(String(64), nullable=False, default="EPSG:32633")

    input_completeness: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    mass_balance_totals: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    overall_mass_balance_error_m3: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_mass_balance_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    output_manifest_path: Mapped[str] = mapped_column(Text, nullable=False)
    warnings: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class FloodSimulationArtifact(Base):
    """
    Reference table for file-backed raster/JSON outputs produced by a flood simulation run.
    """
    __tablename__ = "flood_simulation_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    simulation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class FloodSimulationDiagnostic(Base):
    """
    Per-timestep mass balance accounting log for fine-grained simulation auditability.
    """
    __tablename__ = "flood_simulation_diagnostics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    simulation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    timestep_index: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_iso: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_storage_m3: Mapped[float] = mapped_column(Float, nullable=False)
    rainfall_input_m3: Mapped[float] = mapped_column(Float, nullable=False)
    runoff_generated_m3: Mapped[float] = mapped_column(Float, nullable=False)
    surface_inflow_m3: Mapped[float] = mapped_column(Float, nullable=False)
    surface_outflow_m3: Mapped[float] = mapped_column(Float, nullable=False)
    drainage_inflow_m3: Mapped[float] = mapped_column(Float, nullable=False)
    drainage_outflow_m3: Mapped[float] = mapped_column(Float, nullable=False)
    infiltration_losses_m3: Mapped[float] = mapped_column(Float, nullable=False)
    current_storage_m3: Mapped[float] = mapped_column(Float, nullable=False)
    mass_balance_error_m3: Mapped[float] = mapped_column(Float, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
