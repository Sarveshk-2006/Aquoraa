"""
Routing Engine Interface Specification

Responsibility:
Compute flood-aware safe vehicle/emergency routing over OpenStreetMap road networks
considering temporal water depth inundation thresholds.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseRoutingEngine(ABC):
    """Abstract Base Class for Routing Engine implementations (Phase 10)."""

    @abstractmethod
    async def compute_safe_route(self, origin: Dict[str, float], destination: Dict[str, float], departure_time: str) -> Dict[str, Any]:
        """Compute safe travel route avoiding flooded road segments."""
        pass
