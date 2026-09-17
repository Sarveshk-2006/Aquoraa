"""
Flood Engine Interface Specification

Responsibility:
Synthesize physical hydrodynamic simulations and ML-calibrated residual maps to output
final 0–3h flood extent, depth grids, and risk categorization.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseFloodEngine(ABC):
    """Abstract Base Class for Flood Engine implementations (Phase 6/8)."""

    @abstractmethod
    async def generate_flood_state(self, simulation_payload: dict[str, Any]) -> dict[str, Any]:
        """Produce unified flood inundation depth grid and hazard index."""
