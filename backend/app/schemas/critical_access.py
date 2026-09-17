"""
Pydantic v2 Schemas for Phase 11 Critical Access Guardian API.

Defines strict input request and output response schemas for:
- CriticalFacilitySchema
- ResponderOriginSchema
- CriticalAccessRequestSchema
- SliceAccessibilitySchema
- AlternateRouteSummarySchema
- CriticalAccessResponseSchema
"""

import math
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.routing import RouteCandidateSchema, RouteLocationSchema

FACILITY_CATEGORIES = [
    "HOSPITAL",
    "CLINIC",
    "FIRE_STATION",
    "POLICE_STATION",
    "AMBULANCE_BASE",
    "EMERGENCY_CONTROL",
    "EMERGENCY_CONTROL_CENTER",
    "SHELTER",
    "OTHER_CRITICAL",
]


class CriticalFacilitySchema(BaseModel):
    """Critical facility schema representation."""

    facility_id: str = Field(description="Unique facility identifier")
    name: str = Field(description="Facility name")
    category: str = Field(description="Facility category taxonomy (HOSPITAL, FIRE_STATION, etc.)")
    latitude: float = Field(description="Facility latitude in EPSG:4326")
    longitude: float = Field(description="Facility longitude in EPSG:4326")
    source: str = Field(description="Data source name")
    source_id: str | None = Field(default=None, description="Source-specific record ID")
    source_type: str = Field(default="SYNTHETIC", description="Source type (AUTHORITATIVE, INSTITUTIONAL, OPEN_GOVERNMENT, OSM, SYNTHETIC)")
    verification_status: str = Field(default="UNVERIFIED", description="Verification status")
    operational_status: str = Field(default="UNKNOWN", description="Facility operational status (UNKNOWN, OPEN, CLOSED)")
    provider_mode: str = Field(default="SYNTHETIC", description="Provider mode (SYNTHETIC, LOCAL_VERIFIED)")
    environment: str = Field(default="DEVELOPMENT_ONLY", description="Environment mode ('DEVELOPMENT_ONLY', 'TEST_ONLY', 'PRODUCTION')")
    summary: str = Field(default="", description="Short facility description")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Full source provenance metadata")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if v is None or math.isnan(v) or math.isinf(v) or not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude must be finite value between -90 and +90, got {v}")
        return float(v)

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if v is None or math.isnan(v) or math.isinf(v) or not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude must be finite value between -180 and +180, got {v}")
        return float(v)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        cat_upper = v.upper()
        if cat_upper not in FACILITY_CATEGORIES:
            raise ValueError(f"Facility category '{v}' not recognized in taxonomy. Expected one of {FACILITY_CATEGORIES}")
        return cat_upper

    def to_route_location(self) -> RouteLocationSchema:
        """Convert facility coordinates to Phase 10 RouteLocationSchema."""
        return RouteLocationSchema(
            latitude=self.latitude,
            longitude=self.longitude,
            label=f"{self.name} ({self.category})",
        )


class ResponderOriginSchema(BaseModel):
    """Responder / emergency vehicle starting origin location."""

    latitude: float = Field(description="Origin latitude in EPSG:4326 (-90 to +90)")
    longitude: float = Field(description="Origin longitude in EPSG:4326 (-180 to +180)")
    label: str | None = Field(default="Responder Origin", description="Optional label for origin location")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if v is None or math.isnan(v) or math.isinf(v) or not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude must be finite value between -90 and +90, got {v}")
        return float(v)

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if v is None or math.isnan(v) or math.isinf(v) or not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude must be finite value between -180 and +180, got {v}")
        return float(v)

    def to_route_location(self) -> RouteLocationSchema:
        """Convert responder origin to Phase 10 RouteLocationSchema."""
        return RouteLocationSchema(
            latitude=self.latitude,
            longitude=self.longitude,
            label=self.label or "Responder Origin",
        )


class CriticalAccessRequestSchema(BaseModel):
    """Input request schema for critical facility accessibility analysis."""

    facility_id: str = Field(description="ID of target critical facility to analyze")
    responder_origin: ResponderOriginSchema = Field(description="Responder / vehicle starting origin location")
    digital_twin_run_id: str | None = Field(default=None, description="Optional Digital Twin run ID (defaults to latest completed run)")
    departure_time: str | None = Field(default=None, description="Optional ISO8601 reference departure time")
    critical_access_severity: str | None = Field(default=None, description="Optional access policy threshold ('MODERATE', 'HIGH', 'SEVERE')")
    access_mode: str = Field(default="EMERGENCY_VEHICLE", description="Primary access mode ('EMERGENCY_VEHICLE')")


class SliceAccessibilitySchema(BaseModel):
    """Facility accessibility state for a single canonical Digital Twin time slice."""

    minutes_from_start: int = Field(description="Minutes from simulation start (0, 30, 60, 90, 120, 150, 180)")
    accessibility_status: str = Field(description="Accessibility status (ACCESSIBLE, LIMITED, AT_RISK, COMPROMISED, UNKNOWN)")
    primary_route_state: str = Field(description="Primary route evaluation state at this time slice")
    primary_route_peak_severity: str = Field(description="Peak flood severity along primary route at this time slice")
    acceptable_alternate_available: bool = Field(description="Flag indicating if an acceptable alternate route is available at this slice")
    evaluation_notes: str = Field(description="Causal explanation notes for this time slice")


class AlternateRouteSummarySchema(BaseModel):
    """Summary schema for an alternate candidate access route."""

    route_id: str = Field(description="Unique route ID")
    summary: str = Field(description="Route corridor summary name")
    distance_m: float = Field(description="Total route distance in meters")
    estimated_duration_s: float = Field(description="Estimated travel duration in seconds")
    status: str = Field(description="Alternate route status ('AVAILABLE', 'ALTERNATE_UNAVAILABLE')")
    usable_travel_window_min: int = Field(description="Usable travel window in minutes")
    route_flood_onset_min: int | None = Field(default=None, description="Modeled flood onset in minutes")
    recommendation_note: str = Field(description="Recommendation status note")
    geometry_geojson: dict[str, Any] | None = Field(default=None, description="LineString GeoJSON geometry of alternate route")


class CriticalAccessResponseSchema(BaseModel):
    """Top-level response schema for Phase 11 Critical Access Guardian API."""

    access_run_id: str = Field(description="Unique critical access run identifier")
    facility: CriticalFacilitySchema = Field(description="Target critical facility metadata")
    origin: ResponderOriginSchema = Field(description="Responder starting location")
    digital_twin_run_id: str = Field(description="Selected Phase 9 Digital Twin run ID")
    routing_run_id: str = Field(description="Reused Phase 10 routing run ID")
    current_access_status: str = Field(description="Access status at 0-min time slice (ACCESSIBLE, LIMITED, AT_RISK, COMPROMISED, UNKNOWN)")
    modeled_loss_of_access_min: int | None = Field(default=None, description="Earliest canonical slice (min) when NO acceptable route remains")
    modeled_loss_of_access_label: str | None = Field(default=None, description="Human-readable loss of access label e.g. '+120 min'")
    time_to_loss_of_access_min: int | None = Field(default=None, description="Minutes remaining until modeled loss of access")
    accessibility_timeline: list[SliceAccessibilitySchema] = Field(default_factory=list, description="7-slice accessibility timeline")
    selected_route: RouteCandidateSchema = Field(description="Primary selected access candidate route")
    alternate_route: AlternateRouteSummarySchema | None = Field(default=None, description="Best alternate access candidate route summary")
    recommendation: str = Field(description="Access recommendation (MAINTAIN_ACCESS, USE_ALTERNATE, ACCESS_AT_RISK, ACCESS_COMPROMISED, UNKNOWN)")
    explanation: str = Field(description="Human-readable explainable causal rationale")
    warnings: list[str] = Field(default_factory=list, description="Data quality, synthetic facility, and uncertainty warnings")
    provenance: dict[str, Any] = Field(description="Full provenance and verification metadata")
    facility_operational_status: str = Field(description="Preserved facility operational status (UNKNOWN, OPEN, CLOSED)")
    facility_verification_status: str = Field(description="Preserved facility verification status")
