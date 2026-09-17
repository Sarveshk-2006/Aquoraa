"""
Domain Models and Enums for Phase 6 Flood Simulation Engine.

Enforces deterministic type contracts, physical severity thresholds,
data completeness classifications, and mass balance data structures.
"""

from dataclasses import dataclass, field
from enum import Enum


class RunoffModel(str, Enum):
    """Supported rainfall-excess runoff generation model formulations."""

    IMPERVIOUS_LOSS = "IMPERVIOUS_LOSS"
    RATIONAL_COEFFICIENT = "RATIONAL_COEFFICIENT"
    INITIAL_DEPRESSION_LOSS = "INITIAL_DEPRESSION_LOSS"


class FloodSeverity(str, Enum):
    """
    Deterministic inundation severity classification levels based on water depth or relative storage.
    Thresholds:
    - DRY: depth < 0.05m (5 cm)
    - LOW: 0.05m <= depth < 0.15m (5-15 cm)
    - MODERATE: 0.15m <= depth < 0.30m (15-30 cm)
    - HIGH: 0.30m <= depth < 0.60m (30-60 cm)
    - SEVERE: depth >= 0.60m (60+ cm)
    """

    DRY = "DRY"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class UncertaintyCategory(str, Enum):
    """Categorization of simulation uncertainties."""

    DATA_UNCERTAINTY = "DATA_UNCERTAINTY"
    PARAMETER_UNCERTAINTY = "PARAMETER_UNCERTAINTY"
    STRUCTURAL_UNCERTAINTY = "STRUCTURAL_UNCERTAINTY"


class DataCompletenessLevel(str, Enum):
    """Input data completeness indicator (NOT ML confidence)."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RainfallResamplingMethod(str, Enum):
    """Resampling method for mapping coarse rainfall resolution to simulation timesteps."""

    HOLD = "HOLD"
    LINEAR_INTERPOLATION = "LINEAR_INTERPOLATION"


class RainfallSourceType(str, Enum):
    """Rainfall input provenance type."""

    OBSERVATION = "OBSERVATION"
    FORECAST = "FORECAST"
    SYNTHETIC_TEST = "SYNTHETIC_TEST"


@dataclass
class RunoffParameters:
    """Configurable parameters for rainfall-runoff transformation."""

    model: RunoffModel = RunoffModel.IMPERVIOUS_LOSS
    runoff_coefficient: float = 0.7
    infiltration_rate_mm_hr: float = 5.0
    initial_loss_mm: float = 2.0
    depression_storage_m3_per_m2: float = 0.05


@dataclass
class DrainageCouplingPolicy:
    """Policy for handling incomplete or ambiguous drainage infrastructure data."""

    unknown_capacity_policy: str = "EXCLUDE"  # 'EXCLUDE', 'CONSERVATIVE_ASSUMPTION', 'SCENARIO'
    unknown_direction_policy: str = "EXCLUDE"  # 'EXCLUDE', 'SCENARIO'
    unknown_association_policy: str = "EXCLUDE"  # 'EXCLUDE', 'NEAREST_VALID'
    max_association_distance_m: float = 200.0


@dataclass
class MassBalanceDiagnostic:
    """Mass balance accounting container for a single simulation timestep."""

    timestep_index: int
    timestamp_iso: str
    previous_storage_m3: float
    rainfall_input_m3: float
    runoff_generated_m3: float
    surface_inflow_m3: float
    surface_outflow_m3: float
    drainage_inflow_m3: float
    drainage_outflow_m3: float
    infiltration_losses_m3: float
    current_storage_m3: float
    mass_balance_error_m3: float
    is_valid: bool
    warnings: list[str] = field(default_factory=list)


@dataclass
class CellFloodState:
    """Grid cell flood status at a specific point in time."""

    cell_id: str
    row: int
    col: int
    elevation_m: float
    cell_area_m2: float
    rainfall_mm_hr: float
    runoff_m3: float
    surface_storage_m3: float
    water_depth_m: float
    water_surface_elevation_m: float
    severity: FloodSeverity
    first_flood_timestamp: str | None = None
    peak_water_depth_m: float = 0.0
    peak_timestamp: str | None = None
