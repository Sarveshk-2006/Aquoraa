"""
SQLAlchemy Models for Terrain Datasets, Catchments, and Processing Runs.

Maintains spatial database metadata, catchment geometries with GiST spatial indexes,
and processing run execution history.
"""

import datetime
import uuid
from typing import Optional, Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TerrainDataset(Base):
    """
    Metadata record for Digital Elevation Models (DEM) stored in the filesystem or raster store.
    """
    __tablename__ = "terrain_datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dataset_identifier: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    crs: Mapped[str] = mapped_column(String(64), nullable=False)
    geom_bounds: Mapped[Any] = mapped_column(
        Geometry("POLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    resolution_x: Mapped[float] = mapped_column(Float, nullable=False)
    resolution_y: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    vertical_units: Mapped[str] = mapped_column(String(32), nullable=False, default="meters")
    nodata: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_test_fixture: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    storage_pointer: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class Catchment(Base):
    """
    Delineated terrain catchment polygon entity with area metrics and pour-point snapping history.
    """
    __tablename__ = "catchments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dataset_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    original_pour_point_x: Mapped[float] = mapped_column(Float, nullable=False)
    original_pour_point_y: Mapped[float] = mapped_column(Float, nullable=False)
    snapped_pour_point_x: Mapped[float] = mapped_column(Float, nullable=False)
    snapped_pour_point_y: Mapped[float] = mapped_column(Float, nullable=False)
    snapped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    snap_distance_m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    contributing_cells_count: Mapped[int] = mapped_column(Integer, nullable=False)
    area_m2: Mapped[float] = mapped_column(Float, nullable=False)
    area_km2: Mapped[float] = mapped_column(Float, nullable=False)
    srid: Mapped[int] = mapped_column(Integer, default=4326, nullable=False)
    geom: Mapped[Any] = mapped_column(
        Geometry("GEOMETRY", srid=4326, spatial_index=True),
        nullable=False
    )
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class TerrainProcessingRun(Base):
    """
    Audit log table tracking terrain engine execution runs, parameters, status, and error states.
    """
    __tablename__ = "terrain_processing_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dataset_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    processing_type: Mapped[str] = mapped_column(String(64), nullable=False, default="TERRAIN_DERIVATIVES")
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="PENDING")
    analysis_crs: Mapped[str] = mapped_column(String(64), nullable=False)
    surface_drainage_threshold_m2: Mapped[float] = mapped_column(Float, nullable=False)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
