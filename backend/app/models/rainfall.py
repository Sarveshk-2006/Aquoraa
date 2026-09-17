import datetime
from typing import Optional, Any

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RainfallObservationGrid(Base):
    """
    Metadata registry for normalized rainfall observation grids (e.g. NASA GPM IMERG V07B).
    Includes envelope bounding polygon in EPSG:4326 with PostGIS GiST index.
    """
    __tablename__ = "rainfall_observation_grids"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    dataset_identifier: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    product_variant: Mapped[str] = mapped_column(String(32), nullable=False)
    product_version: Mapped[str] = mapped_column(String(32), nullable=False)
    observation_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    observation_end: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    geom_bounds: Mapped[Any] = mapped_column(
        Geometry("POLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    resolution_deg_x: Mapped[float] = mapped_column(Float, nullable=False)
    resolution_deg_y: Mapped[float] = mapped_column(Float, nullable=False)
    units: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity_type: Mapped[str] = mapped_column(String(32), nullable=False, default="ACCUMULATION")
    quality_status: Mapped[str] = mapped_column(String(32), nullable=False, default="VALID", index=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    storage_pointer: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class RainfallForecastGrid(Base):
    """
    Metadata registry for short-term precipitation forecast grids (0-3 hour lead times).
    Includes envelope bounding polygon in EPSG:4326 with PostGIS GiST index.
    """
    __tablename__ = "rainfall_forecast_grids"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    dataset_identifier: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False, default="SYNTHETIC_NOWCAST")
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    initialization_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    valid_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    lead_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    geom_bounds: Mapped[Any] = mapped_column(
        Geometry("POLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    resolution_deg_x: Mapped[float] = mapped_column(Float, nullable=False)
    resolution_deg_y: Mapped[float] = mapped_column(Float, nullable=False)
    units: Mapped[str] = mapped_column(String(32), nullable=False)
    quality_status: Mapped[str] = mapped_column(String(32), nullable=False, default="VALID", index=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    storage_pointer: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class IngestionRun(Base):
    """
    Data Pipeline Ingestion Execution Audit Log.
    Records pipeline execution status, provider, record count, and errors.
    """
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    pipeline_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_identifier: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="SUCCESS", index=True)
    records_ingested: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
