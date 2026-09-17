"""
Rainfall Engine Interface Specification

Responsibility:
Normalize and transform radar/NWP rainfall forcing into spatial-temporal grids
suitable for hydrological surface-flow and runoff calculation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseRainfallEngine(ABC):
    """Abstract Base Class for Rainfall Engine implementations (Phase 3/4)."""

    @abstractmethod
    async def process_rainfall_grid(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw rainfall data into spatial-temporal intensity grids."""
        pass
