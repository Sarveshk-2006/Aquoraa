"""
Pydantic Schemas for Terrain Engine, Catchment Delineation, and Processing Runs.

Enforces typed data contracts for DEM validation, derivative rasters, catchment geometries,
and terrain processing runs.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DEMMetadataSchema(BaseModel):
    """Schema for Digital Elevation Model metadata."""
    dataset_id: str = Field(..., description="Unique terrain dataset identifier")
    source: str = Field(..., description="Provider or source file label")
    crs: str = Field(..., description="Dataset Spatial Reference System")
    bounds: tuple[float, float, float, float] = Field(..., description="(left, bottom, right, top)")
    resolution: tuple[float, float] = Field(..., description="(dx, dy) cell dimensions")
    width: int = Field(..., gt=0, description="Raster width in pixels")
    height: int = Field(..., gt=0, description="Raster height in pixels")
    vertical_units: str = Field("meters", description="Vertical elevation unit")
    nodata: float | None = Field(-9999.0, description="Nodata sentinel value")
    is_test_fixture: bool = Field(False, description="Flag indicating if dataset is a test fixture")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Dataset audit lineage")


class TerrainAnalysisRequest(BaseModel):
    """Schema for initiating terrain derivative & flow analysis."""
    dataset_id: str = Field("synthetic_inclined_plane", description="Target dataset ID or fixture name")
    provider_type: str = Field("synthetic", description="Provider type: 'synthetic' or 'local'")
    fixture_type: str = Field("inclined_plane", description="Synthetic fixture type if provider_type is synthetic")
    analysis_crs: str = Field("EPSG:32633", description="Projected metric Analysis CRS")
    calculate_aspect: bool = Field(True, description="Whether to calculate aspect raster")
    surface_drainage_threshold_m2: float = Field(10000.0, gt=0, description="Surface drainage proxy threshold area in m2")
    pour_point_xy: tuple[float, float] | None = Field(None, description="Optional (x, y) pour point coordinate for catchment delineation")
    snap_tolerance_m: float = Field(100.0, ge=0, description="Pour-point snapping distance tolerance in meters")


class PourPointSchema(BaseModel):
    """Coordinates of a pour point."""
    x: float = Field(..., description="X coordinate (Easting or Longitude)")
    y: float = Field(..., description="Y coordinate (Northing or Latitude)")


class CatchmentResponse(BaseModel):
    """Schema for terrain catchment delineation response."""
    model_config = ConfigDict(from_attributes=True)

    catchment_id: str = Field(..., description="Unique catchment identifier UUID")
    dataset_id: str = Field(..., description="Parent DEM dataset ID")
    original_pour_point: PourPointSchema = Field(..., description="Original requested pour point")
    snapped_pour_point: PourPointSchema = Field(..., description="Snapped pour point coordinate")
    snapped: bool = Field(..., description="True if pour point was snapped")
    snap_distance_m: float = Field(0.0, description="Snapping distance in meters")
    contributing_cells_count: int = Field(..., gt=0, description="Number of contributing DEM cells")
    area_m2: float = Field(..., gt=0, description="Metric catchment area in square meters")
    area_km2: float = Field(..., gt=0, description="Catchment area in square kilometers")
    crs: str = Field(..., description="Analysis CRS of geometry")
    geojson_geometry: dict[str, Any] = Field(..., description="GeoJSON polygon geometry of catchment")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Processing provenance")


class TerrainDerivativeSummary(BaseModel):
    """Summary metadata for a calculated terrain derivative raster artifact."""
    derivative_type: str = Field(..., description="Derivative type: slope, aspect, flow_direction, flow_accumulation, surface_drainage_proxy")
    crs: str = Field(..., description="Raster CRS")
    resolution: tuple[float, float] = Field(..., description="Pixel resolution")
    units: str = Field(..., description="Measurement units")
    storage_pointer: str | None = Field(None, description="Path or reference to stored raster artifact")


class TerrainAnalysisResponse(BaseModel):
    """Response schema for completed terrain analysis run."""
    run_id: str = Field(..., description="Unique processing run UUID")
    dataset_id: str = Field(..., description="Processed DEM dataset ID")
    status: str = Field("COMPLETED", description="Run status")
    analysis_crs: str = Field(..., description="Projected metric Analysis CRS used")
    dem_metadata: DEMMetadataSchema = Field(..., description="Input DEM metadata")
    derivatives: list[TerrainDerivativeSummary] = Field(default_factory=list, description="Generated terrain derivative summaries")
    catchment: CatchmentResponse | None = Field(None, description="Delineated catchment if pour point was supplied")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Audit lineage metadata")


class TerrainProcessingRunResponse(BaseModel):
    """Schema for returning terrain processing run record."""
    model_config = ConfigDict(from_attributes=True)

    run_id: str = Field(..., description="Unique processing run UUID")
    dataset_id: str = Field(..., description="Target dataset ID")
    processing_type: str = Field("TERRAIN_DERIVATIVES", description="Type of processing performed")
    status: str = Field(..., description="Status: PENDING, RUNNING, COMPLETED, FAILED")
    analysis_crs: str = Field(..., description="Analysis CRS used")
    surface_drainage_threshold_m2: float = Field(..., description="Threshold area parameter used")
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
