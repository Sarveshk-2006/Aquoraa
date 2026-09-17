"""
Runoff Engine Interface Specification

Responsibility:
Transform rainfall precipitation into net surface runoff volumes using soil infiltration
models (SCS Curve Number / Green-Ampt).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseRunoffEngine(ABC):
    """Abstract Base Class for Runoff Engine implementations (Phase 4)."""

    @abstractmethod
    async def compute_runoff(self, rainfall_data: Dict[str, Any], soil_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate effective surface runoff depth and volume across catchments."""
        pass
