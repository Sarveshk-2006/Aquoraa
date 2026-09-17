"""
Ground Truth Engine Interface Specification

Responsibility:
Process, aggregate, and validate community ground-truth reports and geotagged imagery.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseGroundTruthEngine(ABC):
    """Abstract Base Class for Ground Truth Engine implementations (Phase 13)."""

    @abstractmethod
    async def process_report(self, report_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate citizen flood observation report and geotagged photo metadata."""
        pass
