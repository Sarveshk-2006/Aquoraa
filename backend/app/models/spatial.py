import datetime
import uuid
from typing import Optional, Any

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudyArea(Base):
    """
    StudyArea model representing spatial extent for cities, pilot zones, or catchments.
    Uses GeoAlchemy2 Geometry column in EPSG:4326 with GiST index.
    """
    __tablename__ = "study_areas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    geom: Mapped[Any] = mapped_column(
        Geometry("POLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    srid: Mapped[int] = mapped_column(Integer, default=4326, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class RasterMetadata(Base):
    """
    Metadata registry table for raster datasets (DEMs, land-cover, satellite grids).
    Includes envelope bounding polygon in EPSG:4326 with GiST index for fast coverage queries.
    """
    __tablename__ = "raster_metadata"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    dataset_identifier: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    acquisition_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ingestion_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    crs: Mapped[str] = mapped_column(String(64), nullable=False)
    geom_bounds: Mapped[Any] = mapped_column(
        Geometry("POLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    resolution_x: Mapped[float] = mapped_column(Float, nullable=False)
    resolution_y: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    nodata: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    units: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    storage_pointer: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)


class VectorFeature(Base):
    """
    Generic PostGIS spatial entity store for urban vector infrastructure (roads, buildings, POIs).
    Uses generic Geometry type in EPSG:4326 with GiST index.
    """
    __tablename__ = "vector_features"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    geom: Mapped[Any] = mapped_column(
        Geometry("GEOMETRY", srid=4326, spatial_index=True),
        nullable=False
    )
    srid: Mapped[int] = mapped_column(Integer, default=4326, nullable=False)
    feature_properties: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
