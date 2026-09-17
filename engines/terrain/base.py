"""
Terrain Engine Interface Specification

Responsibility:
Derive terrain-based hydrological and geospatial structures from DEM rasters
(slope, aspect, flow direction D8, D-Infinity, and sub-catchment delineation).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTerrainEngine(ABC):
    """Abstract Base Class for Terrain Engine implementations (Phase 4)."""

    @abstractmethod
    async def process_dem(self, dem_path: str) -> Dict[str, Any]:
        """Derive hydro-delineated catchments, slopes, and flow directions."""
        pass
