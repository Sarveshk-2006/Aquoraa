"""
Surface Flow Engine Interface Specification

Responsibility:
Simulate 2D shallow water hydrodynamic overland surface flow (diffusive wave / kinematic wave).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSurfaceFlowEngine(ABC):
    """Abstract Base Class for Surface Flow Engine implementations (Phase 4/6)."""

    @abstractmethod
    async def compute_surface_water_movement(self, surface_inflow: Dict[str, Any]) -> Dict[str, Any]:
        """Compute overland 2D surface water depth grids and flow velocity vectors."""
        pass
