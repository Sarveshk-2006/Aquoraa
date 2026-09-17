"""
SQLAlchemy PostGIS Models for Drainage Datasets, Networks, Nodes, Links, and Processing Runs.

Maintains spatial database metadata, node Point and link LineString PostGIS geometries with GiST spatial indexes,
relational foreign keys/indexes, and processing audit run execution history.
"""

import datetime
import uuid
from typing import Optional, Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DrainageDataset(Base):
    """
    Metadata record for drainage vector datasets (municipal GIS, open data, synthetic test fixtures).
    """
    __tablename__ = "drainage_datasets"

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
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    link_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[str] = mapped_column(String(32), nullable=False, default="AUTHORITATIVE")
    is_test_fixture: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    storage_pointer: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class DrainageNode(Base):
    """
    Urban drainage node entity (inlet, catch basin, manhole, junction, outfall, pump station).
    Uses GeoAlchemy2 Geometry Point column in EPSG:4326 with GiST spatial index.
    """
    __tablename__ = "drainage_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dataset_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    node_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    node_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="INLET")
    elevation_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    invert_elevation_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ground_elevation_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[str] = mapped_column(String(32), nullable=False, default="AUTHORITATIVE")
    srid: Mapped[int] = mapped_column(Integer, default=4326, nullable=False)
    geom: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326, spatial_index=True),
        nullable=False
    )
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class DrainageLink(Base):
    """
    Urban drainage conduit / pipe link connecting from_node to to_node.
    Uses GeoAlchemy2 Geometry LineString column in EPSG:4326 with GiST spatial index.
    """
    __tablename__ = "drainage_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dataset_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    link_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    from_node_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    to_node_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    link_type: Mapped[str] = mapped_column(String(32), nullable=False, default="PIPE")
    length_m: Mapped[float] = mapped_column(Float, nullable=False)
    diameter_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    slope: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    capacity_m3s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Null if unknown, NEVER zero
    roughness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    direction_status: Mapped[str] = mapped_column(String(32), nullable=False, default="KNOWN")
    confidence: Mapped[str] = mapped_column(String(32), nullable=False, default="AUTHORITATIVE")
    srid: Mapped[int] = mapped_column(Integer, default=4326, nullable=False)
    geom: Mapped[Any] = mapped_column(
        Geometry("LINESTRING", srid=4326, spatial_index=True),
        nullable=False
    )
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class DrainageNetwork(Base):
    """
    Compiled drainage network summary entity storing network topology statistics and graph diagnostics.
    """
    __tablename__ = "drainage_networks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dataset_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    analysis_crs: Mapped[str] = mapped_column(String(64), nullable=False)
    nodes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    links_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    connected_components_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outfalls_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class DrainageProcessingRun(Base):
    """
    Audit log table tracking drainage network ingestion & normalization processing runs.
    """
    __tablename__ = "drainage_processing_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dataset_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    network_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    processing_type: Mapped[str] = mapped_column(String(64), nullable=False, default="DRAINAGE_NETWORK_NORMALIZATION")
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="PENDING")
    analysis_crs: Mapped[str] = mapped_column(String(64), nullable=False)
    snap_tolerance_m: Mapped[float] = mapped_column(Float, nullable=False)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
