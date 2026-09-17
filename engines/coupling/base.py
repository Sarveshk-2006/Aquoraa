"""
Coupling Engine Interface Specification

Responsibility:
Coupling 1D sewer network hydraulic models with 2D overland surface water flow models.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseCouplingEngine(ABC):
    """Abstract Base Class for Coupled Hydraulics Engine implementations (Phase 6)."""

    @abstractmethod
    async def couple_1d_2d_hydraulic_state(self, surface_state: Dict[str, Any], drainage_state: Dict[str, Any]) -> Dict[str, Any]:
        """Bi-directionally couple 1D underground pipe flow with 2D surface water depth."""
        pass
