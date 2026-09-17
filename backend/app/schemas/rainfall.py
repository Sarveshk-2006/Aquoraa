"""
Pydantic Schemas for Rainfall Observation and Forecast Data Contracts.

Defines strict schemas for rainfall observations, precipitation forecasts,
quality status enums, and data ingestion execution audit records.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QualityStatus(str, Enum):
    """
    Explicit Quality Status Flags.
    
    CRITICAL DISTINCTION:
    - VALID: Valid measurement (including measured 0.0 zero rainfall).
    - MISSING: Sensor/file missing.
    - INVALID: Failed validation (e.g. negative rainfall value).
    - SUSPECT: Out of expected physical bounds.
    - NODATA: Nodata sentinel pixel.
    """
    VALID = "VALID"
    MISSING = "MISSING"
    INVALID = "INVALID"
    SUSPECT = "SUSPECT"
    NODATA = "NODATA"


class RainfallQuantityType(str, Enum):
    """Rainfall quantity interpretation (accumulation vs rate)."""
    ACCUMULATION = "ACCUMULATION"  # mm over interval
    INTENSITY = "INTENSITY"        # mm/h rate


class RainfallObservationSchema(BaseModel):
    """Schema for a normalized rainfall observation grid metadata record."""
    model_config = ConfigDict(from_attributes=True)

    dataset_identifier: str = Field(..., description="Unique dataset/file identifier string")
    provider: str = Field(..., description="Provider tag (e.g. NASA_GPM_IMERG)")
    product_variant: str = Field("Final", description="IMERG product variant: Final, Late, Early")
    product_version: str = Field("V07B", description="Product version string")
    observation_start: datetime = Field(..., description="UTC start timestamp of accumulation interval")
    observation_end: datetime = Field(..., description="UTC end timestamp of accumulation interval")
    duration_minutes: float = Field(30.0, description="Interval duration in minutes")
    resolution_deg: tuple[float, float] = Field((0.1, 0.1), description="Spatial resolution in degrees (x_res, y_res)")
    units: str = Field("mm", description="Measurement units (mm or mm/h)")
    quantity_type: RainfallQuantityType = Field(RainfallQuantityType.ACCUMULATION, description="Quantity type")
    quality_status: QualityStatus = Field(QualityStatus.VALID, description="Overall grid quality status")
    bounds: tuple[float, float, float, float] = Field(..., description="(minx, miny, maxx, maxy) envelope")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Audit lineage metadata")
    storage_pointer: str | None = Field(None, description="Path or URI to stored array payload")

    @model_validator(mode="after")
    def validate_timestamps(self) -> "RainfallObservationSchema":
        if self.observation_start >= self.observation_end:
            raise ValueError(f"observation_start ({self.observation_start}) must precede observation_end ({self.observation_end})")
        return self


class RainfallForecastSchema(BaseModel):
    """Schema for a normalized rainfall forecast grid metadata record."""
    model_config = ConfigDict(from_attributes=True)

    dataset_identifier: str = Field(..., description="Unique forecast dataset identifier")
    provider: str = Field(..., description="Forecast provider tag")
    model_name: str = Field("SYNTHETIC_NOWCAST", description="Forecast model name")
    model_version: str = Field("1.0", description="Forecast model/version identifier")
    initialization_time: datetime = Field(..., description="UTC initialization time T0")
    valid_time: datetime = Field(..., description="UTC valid forecast time T_valid")
    lead_time_minutes: int = Field(..., ge=0, le=180, description="Forecast lead time in minutes (0-180)")
    temporal_resolution_minutes: float = Field(30.0, description="Temporal step resolution in minutes")
    resolution_deg: tuple[float, float] = Field((0.1, 0.1), description="Spatial resolution in degrees")
    units: str = Field("mm", description="Units (mm accumulation or mm/h rate)")
    quantity_type: RainfallQuantityType = Field(RainfallQuantityType.ACCUMULATION, description="Precipitation quantity type")
    quality_status: QualityStatus = Field(QualityStatus.VALID, description="Quality status")
    bounds: tuple[float, float, float, float] = Field(..., description="(minx, miny, maxx, maxy) envelope")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Forecast provenance lineage")
    storage_pointer: str | None = Field(None, description="Storage pointer to forecast grid payload")

    @model_validator(mode="after")
    def validate_forecast_times(self) -> "RainfallForecastSchema":
        if self.valid_time < self.initialization_time:
            raise ValueError(f"valid_time ({self.valid_time}) cannot precede initialization_time ({self.initialization_time})")
        return self


class IngestionRunSchema(BaseModel):
    """Schema for recording a data ingestion execution run."""
    model_config = ConfigDict(from_attributes=True)

    pipeline_type: str = Field(..., description="RAINFALL or FORECAST")
    provider: str = Field(..., description="Provider identifier")
    source_identifier: str = Field(..., description="Source dataset/file identifier")
    status: str = Field("SUCCESS", description="SUCCESS, FAILED, or PARTIAL")
    records_ingested: int = Field(1, ge=0, description="Count of records/grids ingested")
    error_message: str | None = Field(None, description="Error log message if failed")
    started_at: datetime
    completed_at: datetime
    provenance: dict[str, Any] = Field(default_factory=dict)
