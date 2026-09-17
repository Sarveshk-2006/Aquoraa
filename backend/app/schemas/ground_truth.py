"""Pydantic v2 Schemas for Phase 13 Ground Truth + Photo Verification.

Defines validation schemas, enum taxonomies, request/response payloads for
FloodObservation, ObservationMedia, FloodIncident, ObservationComparison,
GroundTruthRun, and GroundTruthEvidence.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

# --- Taxonomy Enums ---

class WaterDepthClass(str, Enum):
    """Categorical water depth observation classes."""

    DRY = "DRY"
    LESS_THAN_10CM = "LESS_THAN_10CM"
    TEN_TO_TWENTY_CM = "10_TO_20CM"
    TWENTY_TO_FORTY_CM = "20_TO_40CM"
    GREATER_THAN_40CM = "GREATER_THAN_40CM"
    UNKNOWN = "UNKNOWN"


class RoadPassability(str, Enum):
    """Observed road passability status."""

    PASSABLE = "PASSABLE"
    DIFFICULT = "DIFFICULT"
    NOT_PASSABLE = "NOT_PASSABLE"
    UNKNOWN = "UNKNOWN"


class FloodPresence(str, Enum):
    """Observed flood presence indicator."""

    FLOOD_PRESENT = "FLOOD_PRESENT"
    NO_FLOOD_OBSERVED = "NO_FLOOD_OBSERVED"
    UNKNOWN = "UNKNOWN"


class ObserverType(str, Enum):
    """Source classification of the observer."""

    COMMUNITY = "COMMUNITY"
    FIELD_TEAM = "FIELD_TEAM"
    AUTHORITY = "AUTHORITY"
    SENSOR = "SENSOR"
    OTHER = "OTHER"


class ObservationSourceType(str, Enum):
    """Origin taxonomy of observation evidence."""

    AUTHORITY = "AUTHORITY"
    FIELD_TEAM = "FIELD_TEAM"
    COMMUNITY = "COMMUNITY"
    SENSOR = "SENSOR"
    SATELLITE_DERIVED = "SATELLITE_DERIVED"
    OTHER = "OTHER"


class VerificationState(str, Enum):
    """Auditable evidence verification states."""

    UNVERIFIED = "UNVERIFIED"
    CORROBORATED = "CORROBORATED"
    CONFIRMED = "CONFIRMED"


class EvidenceStrength(str, Enum):
    """Qualitative evidence strength metric."""

    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    UNKNOWN = "UNKNOWN"


class ObservationType(str, Enum):
    """Taxonomy of ground truth report types."""

    FLOOD_REPORT = "FLOOD_REPORT"
    ROAD_REPORT = "ROAD_REPORT"
    WATER_LEVEL_REPORT = "WATER_LEVEL_REPORT"
    DRAINAGE_REPORT = "DRAINAGE_REPORT"
    PHOTO_REPORT = "PHOTO_REPORT"
    FIELD_INSPECTION = "FIELD_INSPECTION"
    OTHER_OBSERVATION = "OTHER_OBSERVATION"


class ImageQuality(str, Enum):
    """Image quality assessment state."""

    SUFFICIENT = "SUFFICIENT"
    LIMITED = "LIMITED"
    INSUFFICIENT = "INSUFFICIENT"
    UNKNOWN = "UNKNOWN"


class ModelComparisonStatus(str, Enum):
    """Comparison result between observation and Digital Twin slice."""

    MODEL_SUPPORTS_OBSERVATION = "MODEL_SUPPORTS_OBSERVATION"
    MODEL_PARTIALLY_SUPPORTS = "MODEL_PARTIALLY_SUPPORTS"
    MODEL_CONTRADICTS_OBSERVATION = "MODEL_CONTRADICTS_OBSERVATION"
    MODEL_NO_DATA = "MODEL_NO_DATA"
    OBSERVATION_NO_DATA = "OBSERVATION_NO_DATA"
    TIME_MISMATCH = "TIME_MISMATCH"
    LOCATION_MISMATCH = "LOCATION_MISMATCH"
    UNKNOWN = "UNKNOWN"


# --- Request & Response Schemas ---

class ObservationCreateSchema(BaseModel):
    """Payload schema to submit a new flood observation."""

    latitude: float = Field(ge=-90.0, le=90.0, description="Observation latitude WGS84")
    longitude: float = Field(ge=-180.0, le=180.0, description="Observation longitude WGS84")
    location_source: str = Field(default="MANUAL", description="Location origin (GPS, EXIF, MANUAL, UNKNOWN)")

    observed_at: str | None = Field(default=None, description="ISO8601 observation timestamp if known")
    source: ObservationSourceType = Field(default=ObservationSourceType.COMMUNITY, description="Source origin type")
    source_id: str | None = Field(default=None, description="External reference ID if provided")
    observer_type: ObserverType = Field(default=ObserverType.COMMUNITY, description="Observer type")
    observer_reference: str | None = Field(default=None, description="Pseudonymous internal observer identifier")

    observation_type: ObservationType = Field(default=ObservationType.FLOOD_REPORT, description="Report taxonomy")
    flood_presence: FloodPresence = Field(default=FloodPresence.FLOOD_PRESENT, description="Flood presence state")
    water_depth_class: WaterDepthClass = Field(default=WaterDepthClass.UNKNOWN, description="Categorical water depth class")
    road_passability: RoadPassability = Field(default=RoadPassability.UNKNOWN, description="Observed road passability")

    description: str | None = Field(default=None, max_length=1000, description="Optional text description")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Metadata provenance dictionary")

    @model_validator(mode="after")
    def validate_logical_consistency(self) -> "ObservationCreateSchema":
        """Rejects or normalizes contradictory observation inputs."""
        if self.flood_presence == FloodPresence.NO_FLOOD_OBSERVED and self.water_depth_class in (
            WaterDepthClass.TEN_TO_TWENTY_CM,
            WaterDepthClass.TWENTY_TO_FORTY_CM,
            WaterDepthClass.GREATER_THAN_40CM,
        ):
            raise ValueError("Cannot specify deep water depth when flood_presence is NO_FLOOD_OBSERVED.")
        return self


class MediaUploadResponseSchema(BaseModel):
    """Response payload for uploaded observation media."""

    media_id: str = Field(description="Unique media identifier")
    observation_id: str = Field(description="Associated observation ID")
    media_type: str = Field(description="Media type (PHOTO, VIDEO)")
    file_hash: str = Field(description="SHA256 file hash")
    mime_type: str = Field(description="Validated MIME type")
    file_size: int = Field(description="File size in bytes")

    uploaded_at: str = Field(description="Upload ISO8601 timestamp")
    metadata_status: str = Field(description="Metadata status")
    processing_status: str = Field(description="Processing status")
    image_quality: ImageQuality = Field(description="Image quality state")
    cv_status: str = Field(description="CV status indicator")
    cv_assessment: dict[str, Any] = Field(description="Bounded CV assessment result")
    provenance: dict[str, Any] = Field(description="Media provenance")


class ObservationResponseSchema(BaseModel):
    """Full data payload schema for a flood observation."""

    observation_id: str = Field(description="Observation identifier")
    observation_type: str = Field(description="Report taxonomy")
    latitude: float = Field(description="Latitude WGS84")
    longitude: float = Field(description="Longitude WGS84")
    location_source: str = Field(description="Location source")

    observed_at: str | None = Field(description="Observed timestamp ISO8601")
    received_at: str = Field(description="Received timestamp ISO8601")
    source: str = Field(description="Source origin")
    source_id: str | None = Field(description="Source reference ID")
    observer_type: str = Field(description="Observer type")
    observer_reference: str | None = Field(description="Pseudonymous observer reference")

    flood_presence: str = Field(description="Flood presence state")
    water_depth_class: str = Field(description="Categorical depth class")
    road_passability: str = Field(description="Observed road passability")
    description: str | None = Field(description="Text description")

    media_count: int = Field(description="Total media attachments")
    verification_state: str = Field(description="Verification state (UNVERIFIED, CORROBORATED, CONFIRMED)")
    evidence_strength: str = Field(description="Evidence strength (WEAK, MODERATE, STRONG, UNKNOWN)")
    incident_id: str | None = Field(description="Associated incident cluster ID")
    model_comparison_status: str = Field(description="Comparison status against Digital Twin")

    provenance: dict[str, Any] = Field(description="Provenance payload")
    created_at: str = Field(description="Creation timestamp ISO8601")
    updated_at: str = Field(description="Update timestamp ISO8601")


class IncidentResponseSchema(BaseModel):
    """Clustered incident response schema."""

    incident_id: str = Field(description="Incident cluster identifier")
    latitude: float = Field(description="Cluster centroid latitude")
    longitude: float = Field(description="Cluster centroid longitude")
    first_observed_at: str | None = Field(description="First observation timestamp")
    last_observed_at: str | None = Field(description="Last observation timestamp")

    observation_count: int = Field(description="Total contributing observations")
    unique_source_count: int = Field(description="Unique independent sources")
    verification_state: str = Field(description="Aggregated verification state")
    evidence_strength: str = Field(description="Aggregated evidence strength")
    status: str = Field(description="Incident operational status")

    contributing_observation_ids: list[str] = Field(default_factory=list, description="IDs of contributing observations")
    provenance: dict[str, Any] = Field(description="Incident provenance")


class ComparisonResponseSchema(BaseModel):
    """Model vs observation comparison output schema."""

    comparison_id: str = Field(description="Comparison identifier")
    observation_id: str = Field(description="Observation ID")
    digital_twin_run_id: str = Field(description="Digital Twin run ID")
    model_slice_minutes: int = Field(description="Matched canonical model slice (0, 30, 60, 90, 120, 150, 180)")
    observation_elapsed_minutes: float | None = Field(description="Elapsed minutes from Digital Twin run start")
    observation_time: str | None = Field(description="Observation timestamp")
    time_difference_minutes: float | None = Field(description="Difference between observation time and model slice")
    spatial_distance_m: float = Field(description="Spatial distance to raster cell center in meters")

    observation_state: str = Field(description="Observation state string")
    model_state: str = Field(description="Modeled severity string")
    comparison_status: str = Field(description="Comparison result (MODEL_SUPPORTS_OBSERVATION, MODEL_CONTRADICTS_OBSERVATION, etc.)")
    evidence_strength: str = Field(description="Evidence strength state")
    verification_state: str = Field(description="Verification state")

    explanation: str = Field(description="Human-readable explainable comparison diagnosis")
    warnings: list[str] = Field(default_factory=list, description="Diagnostic warnings")
    provenance: dict[str, Any] = Field(description="Comparison provenance payload")


class GroundTruthRunRequestSchema(BaseModel):
    """Payload to trigger a Ground Truth analysis & comparison run."""

    digital_twin_run_id: str | None = Field(default=None, description="Optional target Digital Twin run ID (defaults to latest)")
    provider_mode: str = Field(default="LOCAL", description="Provider mode (LOCAL, SYNTHETIC)")
    cluster_radius_m: float = Field(default=250.0, ge=50.0, le=2000.0, description="Incident clustering radius in meters")
    cluster_time_minutes: float = Field(default=60.0, ge=10.0, le=360.0, description="Incident clustering window in minutes")
    max_time_diff_minutes: float = Field(default=20.0, ge=5.0, le=120.0, description="Digital Twin slice time matching tolerance in minutes")


class GroundTruthRunResponseSchema(BaseModel):
    """Ground Truth analysis run execution summary."""

    run_id: str = Field(description="Ground Truth run ID")
    digital_twin_run_id: str | None = Field(description="Associated Digital Twin run ID")
    status: str = Field(description="Run execution status")
    started_at: str = Field(description="Start timestamp ISO8601")
    completed_at: str | None = Field(description="Completion timestamp ISO8601")

    observation_count: int = Field(description="Total observations processed")
    incident_count: int = Field(description="Total incidents clustered")
    comparison_count: int = Field(description="Total model comparisons evaluated")
    provider_mode: str = Field(description="Provider mode used")

    warnings: list[str] = Field(default_factory=list, description="Diagnostic warnings")
    provenance: dict[str, Any] = Field(description="Run provenance payload")


class EvidenceResponseSchema(BaseModel):
    """Corroborating evidence record response schema."""

    evidence_id: str = Field(description="Evidence identifier")
    observation_id: str = Field(description="Associated observation ID")
    evidence_type: str = Field(description="Type of evidence (PHOTO, FIELD_REPORT, SATELLITE)")
    source: str = Field(description="Source origin")
    source_id: str | None = Field(description="Source reference ID")
    evidence_strength: str = Field(description="Evidence strength")
    provenance: dict[str, Any] = Field(description="Evidence provenance")
