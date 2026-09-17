"""
Rainfall Observation Data Provider Contracts and NASA GPM IMERG Adapter.

Provides vendor-neutral interface for rainfall observations/estimates (BaseRainfallProvider)
and NASA GPM IMERG V07B specific provider adapter (IMERGRainfallProvider).

IMPORTANT SCIENTIFIC PRINCIPLE:
IMERG is a precipitation observation/estimation product, NOT a weather forecast.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import structlog

from app.core.config import settings
from app.schemas.geospatial import BoundingBox, SpatialMetadata
from app.schemas.rainfall import (
    QualityStatus,
    RainfallObservationSchema,
    RainfallQuantityType,
)

logger = structlog.get_logger("aquora.providers.rainfall")


class BaseRainfallProvider(ABC):
    """
    Abstract Vendor-Neutral Contract for Rainfall Observation & Precipitation Estimation Providers.
    """

    @abstractmethod
    async def get_dataset_metadata(self, dataset_id: str) -> SpatialMetadata:
        """Fetch metadata for a specific rainfall observation dataset."""

    @abstractmethod
    async def fetch_observation(
        self,
        bbox: BoundingBox,
        start_time: datetime,
        end_time: datetime,
        product_variant: str = "Final"
    ) -> RainfallObservationSchema:
        """Fetch normalized rainfall observation record for spatial envelope and time interval."""

    @abstractmethod
    async def check_availability(self, bbox: BoundingBox, timestamp: datetime) -> bool:
        """Check if rainfall observation is available for given spatial envelope and timestamp."""


class IMERGRainfallProvider(BaseRainfallProvider):
    """
    NASA GPM IMERG V07B Rainfall Observation Provider Adapter.
    
    Supports product variants:
    - Final: Research quality (latencies ~3.5 months).
    - Late: Operational monitoring (latencies ~14 hours).
    - Early: Near real-time monitoring (latencies ~4 hours).
    
    Spatial resolution: ~0.1° (~10km)
    Temporal resolution: 30 minutes
    """

    def __init__(self, username: str | None = None, password: str | None = None):
        self.username = username or settings.NASA_EARTHDATA_USERNAME
        self.password = password or settings.NASA_EARTHDATA_PASSWORD
        self.provider_id = "NASA_GPM_IMERG"
        self.version = "V07B"

    def has_credentials(self) -> bool:
        """Check if NASA Earthdata Login credentials are provided."""
        return bool(self.username and self.password)

    async def get_dataset_metadata(self, dataset_id: str) -> SpatialMetadata:
        """Inspect IMERG dataset metadata."""
        return SpatialMetadata(
            source=self.provider_id,
            crs="EPSG:4326",
            resolution=(0.1, 0.1),
            units="mm",
            version=self.version,
            provenance={
                "provider": self.provider_id,
                "version": self.version,
                "variant_options": ["Final", "Late", "Early"],
                "credentials_configured": self.has_credentials(),
            }
        )

    async def check_availability(self, bbox: BoundingBox, timestamp: datetime) -> bool:
        """Check availability for IMERG product."""
        # IMERG global coverage between 60N and 60S
        if bbox.miny < -60.0 or bbox.maxy > 60.0:
            logger.warning("Bounding box outside GPM IMERG latitude extent (-60 to 60)", bbox=bbox)
            return False
        return True

    async def fetch_observation(
        self,
        bbox: BoundingBox,
        start_time: datetime,
        end_time: datetime,
        product_variant: str = "Final"
    ) -> RainfallObservationSchema:
        """
        Fetch normalized IMERG observation metadata record.
        
        If Earthdata credentials are missing, reports authentication unconfigured
        and returns structured metadata contract for verification.
        """
        valid_variants = ["Final", "Late", "Early"]
        if product_variant not in valid_variants:
            raise ValueError(f"Invalid IMERG product variant: '{product_variant}'. Expected one of {valid_variants}")

        duration_minutes = (end_time - start_time).total_seconds() / 60.0

        dataset_id = f"GPM_3IMERG_{start_time.strftime('%Y%m%d_%H%M')}_{product_variant.upper()}"

        logger.info(
            "IMERG observation requested",
            dataset_id=dataset_id,
            variant=product_variant,
            credentials_configured=self.has_credentials()
        )

        return RainfallObservationSchema(
            dataset_identifier=dataset_id,
            provider=self.provider_id,
            product_variant=product_variant,
            product_version=self.version,
            observation_start=start_time,
            observation_end=end_time,
            duration_minutes=duration_minutes,
            resolution_deg=(0.1, 0.1),
            units="mm",
            quantity_type=RainfallQuantityType.ACCUMULATION,
            quality_status=QualityStatus.VALID,
            bounds=(bbox.minx, bbox.miny, bbox.maxx, bbox.maxy),
            provenance={
                "provider": self.provider_id,
                "product_variant": product_variant,
                "product_version": self.version,
                "spatial_resolution_deg": 0.1,
                "temporal_resolution_min": 30,
                "credentials_configured": self.has_credentials(),
            }
        )

    def load_event_rainfall_raster(
        self,
        event_id: str = "E05",
        custom_path: str | None = None
    ) -> tuple[Any, dict]:
        """
        Load real processed NASA IMERG event rainfall raster (GeoTIFF) for Phase 6 flood engine.
        
        Default event: E05 (data/processed/phase7/rainfall/E05_rainfall_30m.tif).
        """
        import os
        import numpy as np
        import rasterio

        file_path = custom_path
        if not file_path or not os.path.exists(file_path):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            file_path = os.path.join(project_root, "data", "processed", "phase7", "rainfall", f"{event_id}_rainfall_30m.tif")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"REAL IMERG rainfall raster for event '{event_id}' not found at {file_path}")

        with rasterio.open(file_path) as ds:
            rain_array = ds.read(1).astype(np.float32)
            transform = ds.transform
            meta = {
                "event_id": event_id,
                "source_file": file_path,
                "crs": str(ds.crs) if ds.crs else "EPSG:32643",
                "width": ds.width,
                "height": ds.height,
                "resolution": (abs(transform.a), abs(transform.e)),
                "units": "mm/hr",
                "mean_intensity_mm_hr": float(np.mean(rain_array)),
                "max_intensity_mm_hr": float(np.max(rain_array)),
                "is_synthetic": False,
                "provenance": {
                    "provider": self.provider_id,
                    "event_id": event_id,
                    "file_path": file_path,
                }
            }
            return rain_array, meta

