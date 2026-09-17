"""
Geospatial Flood Simulation Wrapper Module for Backend App Integration.

Delegates core deterministic simulation logic to engines/flood while providing
lightweight re-exports and adapter utilities for FastAPI services.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path for importing engines.flood
_project_root = str(Path(__file__).resolve().parents[3])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from engines.flood import (
    DataCompletenessLevel,
    DrainageCouplingPolicy,
    FloodSeverity,
    MassBalanceDiagnostic,
    RainfallResamplingMethod,
    RainfallSourceType,
    RunoffModel,
    RunoffParameters,
    UncertaintyCategory,
    run_flood_simulation_loop,
    validate_simulation_inputs,
)

__all__ = [
    "DataCompletenessLevel",
    "DrainageCouplingPolicy",
    "FloodSeverity",
    "MassBalanceDiagnostic",
    "RainfallResamplingMethod",
    "RainfallSourceType",
    "RunoffModel",
    "RunoffParameters",
    "UncertaintyCategory",
    "run_flood_simulation_loop",
    "validate_simulation_inputs",
]
