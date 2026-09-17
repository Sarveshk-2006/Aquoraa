"""
Vendor-Neutral Spatial Provider Abstract Interfaces.

Defines spatial data provider contracts for terrain (DEM), land cover, and urban vector infrastructure.
Contracts enforce metadata, spatial bounds, CRS specification, resolution, and provenance traceability.

STRICT RULE: No real external network requests or integrations (NASA, USGS, OSM, Copernicus) in Phase 2.
"""

from abc import ABC, abstractmethod

from app.schemas.geospatial import (
    BoundingBox,
    SpatialMetadata,
)


class BaseTerrainProvider(ABC):
    """
    Abstract contract for terrain / DEM spatial data acquisition providers.
    Future implementations may source municipal DEMs, Copernicus, or USGS elevation rasters.
    """

    @abstractmethod
    async def get_metadata(self, dataset_id: str) -> SpatialMetadata:
        """Fetch metadata for a specified terrain dataset."""

    @abstractmethod
    async def check_coverage(self, bbox: BoundingBox, crs: str = "EPSG:4326") -> bool:
        """Check if provider has terrain data available for the given spatial envelope."""


class BaseLandCoverProvider(ABC):
    """
    Abstract contract for land-cover and surface imperviousness providers.
    """

    @abstractmethod
    async def get_metadata(self, dataset_id: str) -> SpatialMetadata:
        """Fetch metadata for a specified land cover dataset."""

    @abstractmethod
    async def check_coverage(self, bbox: BoundingBox, crs: str = "EPSG:4326") -> bool:
        """Check coverage for land cover data."""


class BaseUrbanVectorProvider(ABC):
    """
    Abstract contract for urban vector data (roads, buildings, POIs, municipal infrastructure).
    """

    @abstractmethod
    async def get_metadata(self, dataset_id: str) -> SpatialMetadata:
        """Fetch vector metadata."""

    @abstractmethod
    async def check_coverage(self, bbox: BoundingBox, crs: str = "EPSG:4326") -> bool:
        """Check coverage for urban vector features."""
