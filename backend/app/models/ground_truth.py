"""SQLAlchemy ORM Data Models for Phase 13 Ground Truth + Photo Verification.

Defines PostGIS-backed models for FloodObservation, ObservationMedia,
FloodIncident, ObservationComparison, GroundTruthRun, and GroundTruthEvidence.
"""

from datetime import datetime
from typing import Optional, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.audit import Base


class FloodObservation(Base):
    """Core observation entity recorded by community, field teams, sensors, or authorities."""

    __tablename__ = "flood_observations"

    observation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    observation_type: Mapped[str] = mapped_column(String(64), nullable=False, default="FLOOD_REPORT")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location_source: Mapped[str] = mapped_column(String(32), nullable=False, default="MANUAL")

    observed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    source: Mapped[str] = mapped_column(String(64), nullable=False, default="COMMUNITY")
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    observer_type: Mapped[str] = mapped_column(String(32), nullable=False, default="COMMUNITY")
    observer_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    flood_presence: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    water_depth_class: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    road_passability: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    media_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verification_state: Mapped[str] = mapped_column(String(32), nullable=False, default="UNVERIFIED")
    evidence_strength: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    incident_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model_comparison_status: Mapped[str] = mapped_column(String(64), nullable=False, default="UNKNOWN")

    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    media_items: Mapped[list["ObservationMedia"]] = relationship("ObservationMedia", back_populates="observation", cascade="all, delete-orphan")
    comparisons: Mapped[list["ObservationComparison"]] = relationship("ObservationComparison", back_populates="observation", cascade="all, delete-orphan")
    evidences: Mapped[list["GroundTruthEvidence"]] = relationship("GroundTruthEvidence", back_populates="observation", cascade="all, delete-orphan")


class ObservationMedia(Base):
    """Media evidence (photo/video) attached to a flood observation."""

    __tablename__ = "observation_media"

    media_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    observation_id: Mapped[str] = mapped_column(String(64), ForeignKey("flood_observations.observation_id", ondelete="CASCADE"), nullable=False)

    media_type: Mapped[str] = mapped_column(String(16), nullable=False, default="PHOTO")
    storage_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False, default="image/jpeg")

    metadata_status: Mapped[str] = mapped_column(String(32), nullable=False, default="VALIDATED")
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROCESSED")
    image_quality: Mapped[str] = mapped_column(String(32), nullable=False, default="SUFFICIENT")
    cv_status: Mapped[str] = mapped_column(String(32), nullable=False, default="DEVELOPMENT_ONLY")
    cv_assessment: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    observation: Mapped["FloodObservation"] = relationship("FloodObservation", back_populates="media_items")


class FloodIncident(Base):
    """Clustered real-world incident entity grouping related observations."""

    __tablename__ = "flood_incidents"

    incident_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    first_observed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_observed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unique_source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    verification_state: Mapped[str] = mapped_column(String(32), nullable=False, default="UNVERIFIED")
    evidence_strength: Mapped[str] = mapped_column(String(32), nullable=False, default="WEAK")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ObservationComparison(Base):
    """Auditable record matching an observation against a canonical Digital Twin slice."""

    __tablename__ = "observation_comparisons"

    comparison_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    observation_id: Mapped[str] = mapped_column(String(64), ForeignKey("flood_observations.observation_id", ondelete="CASCADE"), nullable=False)
    digital_twin_run_id: Mapped[str] = mapped_column(String(64), nullable=False)

    model_slice_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    observation_elapsed_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    observation_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_difference_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spatial_distance_m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    observation_state: Mapped[str] = mapped_column(String(64), nullable=False)
    model_state: Mapped[str] = mapped_column(String(64), nullable=False)
    comparison_status: Mapped[str] = mapped_column(String(64), nullable=False, default="UNKNOWN")

    evidence_strength: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    verification_state: Mapped[str] = mapped_column(String(32), nullable=False, default="UNVERIFIED")
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    warnings: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    observation: Mapped["FloodObservation"] = relationship("FloodObservation", back_populates="comparisons")


class GroundTruthRun(Base):
    """Audit run record for Ground Truth observation processing and Digital Twin comparison."""

    __tablename__ = "ground_truth_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    digital_twin_run_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RUNNING")

    observation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    incident_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comparison_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="LOCAL")

    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    warnings: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class GroundTruthEvidence(Base):
    """Corroborating evidence link (photo, field report, SAR metadata) for an observation."""

    __tablename__ = "ground_truth_evidence"

    evidence_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    observation_id: Mapped[str] = mapped_column(String(64), ForeignKey("flood_observations.observation_id", ondelete="CASCADE"), nullable=False)

    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False, default="PHOTO")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="COMMUNITY")
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    evidence_strength: Mapped[str] = mapped_column(String(32), nullable=False, default="MODERATE")
    storage_reference: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    observation: Mapped["FloodObservation"] = relationship("FloodObservation", back_populates="evidences")
