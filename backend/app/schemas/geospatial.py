"""
Pydantic Schemas for Geospatial Metadata and Provenance.

Provides strictly typed data contracts for spatial datasets, rasters, vector features, and study areas.
Ensures full auditability, CRS validation, and provenance tracking across all geospatial models.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BoundingBox(BaseModel):
    """Spatial bounding box representation [minx, miny, maxx, maxy]."""
    minx: float = Field(..., description="Minimum X coordinate (Longitude/Easting)")
    miny: float = Field(..., description="Minimum Y coordinate (Latitude/Northing)")
    maxx: float = Field(..., description="Maximum X coordinate (Longitude/Easting)")
    maxy: float = Field(..., description="Maximum Y coordinate (Latitude/Northing)")

    @model_validator(mode="after")
    def validate_bounds(self) -> "BoundingBox":
        if self.minx > self.maxx:
            raise ValueError(f"minx ({self.minx}) cannot be greater than maxx ({self.maxx})")
        if self.miny > self.maxy:
            raise ValueError(f"miny ({self.miny}) cannot be greater than maxy ({self.maxy})")
        return self


class SpatialMetadata(BaseModel):
    """Full geospatial dataset metadata and provenance model."""
    source: str = Field(..., description="Origin provider or dataset source identifier")
    acquisition_time: datetime | None = Field(None, description="Timestamp when data was originally observed/captured")
    ingestion_time: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when data was ingested into Aquora")
    crs: str = Field("EPSG:4326", description="Spatial reference system identifier (e.g. EPSG:4326)")
    resolution: tuple[float, float] | None = Field(None, description="Spatial resolution (x_res, y_res)")
    bounding_box: BoundingBox | None = Field(None, description="Dataset spatial envelope")
    units: str | None = Field(None, description="Physical units of data values (e.g., meters, degrees)")
    nodata: float | None = Field(None, description="Nodata sentinel value")
    version: str = Field("1.0", description="Dataset version tag")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Audit trail metadata (processing steps, parameters)")


class StudyAreaBase(BaseModel):
    """Base schema for StudyArea."""
    name: str = Field(..., description="Human-readable study area name")
    description: str | None = Field(None, description="Detailed study area description")
    srid: int = Field(4326, description="Spatial Reference ID (SRID)")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Provenance metadata dictionary")


class StudyAreaCreate(StudyAreaBase):
    """Schema for creating a new StudyArea."""
    geojson_geometry: dict[str, Any] = Field(..., description="GeoJSON geometry object")


class StudyAreaResponse(StudyAreaBase):
    """Schema for returning StudyArea details."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique UUID identifier for the study area")
    created_at: datetime
    updated_at: datetime


class RasterMetadataBase(BaseModel):
    """Base schema for Raster dataset metadata."""
    dataset_identifier: str = Field(..., description="Unique dataset identifier string")
    source: str = Field(..., description="Data source provider identifier")
    crs: str = Field(..., description="Dataset CRS string (e.g. EPSG:4326)")
    bounds: tuple[float, float, float, float] = Field(..., description="(left, bottom, right, top)")
    resolution: tuple[float, float] = Field(..., description="(x_res, y_res)")
    width: int = Field(..., gt=0, description="Raster width in pixels")
    height: int = Field(..., gt=0, description="Raster height in pixels")
    nodata: float | None = Field(None, description="Nodata sentinel value")
    units: str | None = Field(None, description="Value units")
    version: str = Field("1.0", description="Dataset version tag")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Audit and processing lineage")
    storage_pointer: str | None = Field(None, description="URI or path to stored raster asset")


class VectorFeatureBase(BaseModel):
    """Base schema for generic urban vector features."""
    category: str = Field(..., description="Feature category: road, building, waterway, poi, future_domain_feature")
    feature_properties: dict[str, Any] = Field(default_factory=dict, description="Generic attribute key-value pairs")
    srid: int = Field(4326, description="Geometry SRID")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Provenance lineage")


RasterMetadataSchema = RasterMetadataBase
VectorFeatureSchema = VectorFeatureBase
