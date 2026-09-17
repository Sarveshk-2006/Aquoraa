"""
External Provider Abstract Interfaces

Defines contracts for future external data source connectors.
NO network calls to external APIs are made in Phase 0.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseRainfallProvider(ABC):
    """Obtains real-time rainfall observations/data."""
    @abstractmethod
    async def fetch_observations(self, location_id: str) -> dict[str, Any]:
        pass

class BaseForecastProvider(ABC):
    """Obtains short-term precipitation forecasts."""
    @abstractmethod
    async def fetch_forecast(self, location_id: str, horizon_hours: int = 3) -> dict[str, Any]:
        pass

class BaseTerrainProvider(ABC):
    """Provides digital elevation model (DEM) and terrain data."""
    @abstractmethod
    async def fetch_dem(self, bbox: dict[str, float]) -> dict[str, Any]:
        pass

class BaseLandCoverProvider(ABC):
    """Provides land cover, soil, and impervious surface data."""
    @abstractmethod
    async def fetch_land_cover(self, bbox: dict[str, float]) -> dict[str, Any]:
        pass

class BaseRoadNetworkProvider(ABC):
    """Provides OpenStreetMap (OSM) road network data."""
    @abstractmethod
    async def fetch_road_network(self, bbox: dict[str, float]) -> dict[str, Any]:
        pass

class BaseSatelliteProvider(ABC):
    """Provides satellite observations (e.g., Sentinel-1 SAR)."""
    @abstractmethod
    async def fetch_satellite_granule(self, granule_id: str) -> dict[str, Any]:
        pass

class BaseRoutingProvider(ABC):
    """Provides routing graph calculation interface."""
    @abstractmethod
    async def compute_base_route(self, origin: dict[str, float], destination: dict[str, float]) -> dict[str, Any]:
        pass
