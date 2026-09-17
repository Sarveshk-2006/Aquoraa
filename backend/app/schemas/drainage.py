"""
Pydantic Schemas for Drainage Network Engine, Nodes, Links, Validation, and Processing Runs.

Enforces strictly typed data contracts for urban drainage infrastructure, data confidence levels,
topology quality flags, directed graph traversals, and catchment associations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DrainageNodeSchema(BaseModel):
    """Schema for an urban drainage node (inlet, manhole, junction, outfall)."""
    model_config = ConfigDict(from_attributes=True)

    node_id: str = Field(..., description="Unique node identifier")
    node_type: str = Field(..., description="Node type: INLET, CATCH_BASIN, MANHOLE, JUNCTION, OUTFALL, STORAGE, PUMP_STATION, OTHER")
    x: float = Field(..., description="X coordinate (Longitude / Easting)")
    y: float = Field(..., description="Y coordinate (Latitude / Northing)")
    elevation_m: float | None = Field(None, description="Top elevation in meters")
    invert_elevation_m: float | None = Field(None, description="Invert elevation in meters")
    ground_elevation_m: float | None = Field(None, description="Ground rim elevation in meters")
    confidence: str = Field("AUTHORITATIVE", description="Data confidence: AUTHORITATIVE, OFFICIAL_OPEN_DATA, VERIFIED_MAPPED, DERIVED, SYNTHETIC, UNKNOWN")
    geojson_geometry: dict[str, Any] = Field(default_factory=dict, description="GeoJSON Point geometry")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Asset provenance lineage")


class DrainageLinkSchema(BaseModel):
    """Schema for an urban drainage conduit / pipe link connecting two nodes."""
    model_config = ConfigDict(from_attributes=True)

    link_id: str = Field(..., description="Unique link identifier")
    from_node_id: str = Field(..., description="Origin node ID")
    to_node_id: str = Field(..., description="Destination node ID")
    link_type: str = Field("PIPE", description="Link type: PIPE, CONDUIT, OPEN_CHANNEL, CULVERT, DITCH, OTHER")
    length_m: float = Field(..., gt=0, description="Metric length in meters")
    diameter_m: float | None = Field(None, description="Pipe diameter in meters")
    width_m: float | None = Field(None, description="Channel width in meters")
    height_m: float | None = Field(None, description="Channel height in meters")
    slope: float | None = Field(None, description="Conduit slope gradient")
    material: str | None = Field(None, description="Conduit material string")
    capacity_m3s: float | None = Field(None, description="Authoritative hydraulic capacity in m3/s. UNKNOWN if None (NOT 0)")
    roughness: float | None = Field(None, description="Manning's roughness coefficient n")
    direction_status: str = Field("KNOWN", description="Direction status: KNOWN or UNKNOWN")
    confidence: str = Field("AUTHORITATIVE", description="Data confidence level")
    geojson_geometry: dict[str, Any] = Field(default_factory=dict, description="GeoJSON LineString geometry")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Asset provenance lineage")


class DrainageValidationSummary(BaseModel):
    """Summary diagnostic report for network topology validation."""
    valid_topology: bool = Field(..., description="True if topology has zero critical errors")
    total_nodes: int = Field(..., ge=0, description="Total node count")
    total_links: int = Field(..., ge=0, description="Total link count")
    duplicate_node_ids: list[str] = Field(default_factory=list, description="Duplicate node IDs")
    duplicate_link_ids: list[str] = Field(default_factory=list, description="Duplicate link IDs")
    orphan_link_ids: list[str] = Field(default_factory=list, description="Link IDs missing endpoint node references")
    self_loop_link_ids: list[str] = Field(default_factory=list, description="Link IDs pointing from a node to itself")
    disconnected_node_ids: list[str] = Field(default_factory=list, description="Isolated nodes with zero link connections")
    unknown_direction_links_count: int = Field(0, description="Count of links with unknown direction")
    unknown_capacity_links_count: int = Field(0, description="Count of links with unknown capacity")
    quality_flags: list[str] = Field(default_factory=list, description="Topology quality flags")


class DrainageCatchmentAssociationSchema(BaseModel):
    """Result of associating Phase 4 catchment polygon with a drainage inlet/node."""
    status: str = Field(..., description="Status: ASSOCIATED, NO_ASSOCIATION, AMBIGUOUS")
    associated_node_id: str | None = Field(None, description="Associated drainage node ID")
    association_method: str = Field(..., description="Method: POLYGON_CONTAINMENT, PROXIMITY_SNAP, NONE")
    distance_m: float | None = Field(None, description="Metric distance to node in meters")
    confidence: str = Field("UNKNOWN", description="Confidence level of association")
    candidates_count: int = Field(0, description="Count of candidate nodes evaluated")


class DrainageNetworkRequest(BaseModel):
    """Schema for initiating drainage network processing run."""
    dataset_id: str = Field("synthetic_simple_chain", description="Target dataset ID or synthetic fixture name")
    provider_type: str = Field("synthetic", description="Provider type: 'synthetic' or 'local'")
    fixture_type: str = Field("simple_chain", description="Synthetic fixture type if provider_type is synthetic")
    snap_tolerance_m: float = Field(5.0, ge=0, description="Spatial snapping tolerance radius in meters")
    analysis_crs: str = Field("EPSG:32633", description="Projected metric Analysis CRS for planar spatial calculations")
    associate_phase4_catchment: bool = Field(False, description="Whether to evaluate Phase 4 catchment association")


class DrainageNetworkResponse(BaseModel):
    """Response schema for compiled drainage network analysis."""
    run_id: str = Field(..., description="Unique processing run UUID")
    network_id: str = Field(..., description="Unique network identifier UUID")
    dataset_id: str = Field(..., description="Source dataset ID")
    status: str = Field("COMPLETED", description="Status string")
    analysis_crs: str = Field(..., description="Projected Analysis CRS used")
    nodes_count: int = Field(..., ge=0, description="Validated node count")
    links_count: int = Field(..., ge=0, description="Validated link count")
    connected_components_count: int = Field(..., ge=0, description="Count of disconnected graph components")
    outfalls_count: int = Field(..., ge=0, description="Count of explicit outfall nodes")
    validation_summary: DrainageValidationSummary = Field(..., description="Topology validation diagnostics")
    catchment_association: DrainageCatchmentAssociationSchema | None = Field(None, description="Catchment association if evaluated")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Audit lineage metadata")


class DrainageProcessingRunResponse(BaseModel):
    """Schema for returning drainage network processing audit run log."""
    model_config = ConfigDict(from_attributes=True)

    run_id: str = Field(..., description="Unique processing run UUID")
    dataset_id: str = Field(..., description="Target dataset ID")
    network_id: str | None = Field(None, description="Generated network ID UUID")
    processing_type: str = Field("DRAINAGE_NETWORK_NORMALIZATION", description="Type of processing performed")
    status: str = Field(..., description="Status: PENDING, RUNNING, COMPLETED, FAILED")
    analysis_crs: str = Field(..., description="Analysis CRS used")
    snap_tolerance_m: float = Field(..., description="Snapping tolerance parameter used")
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
