"""
Diagnostics, Mass Conservation, & Uncertainty Module for Phase 6 Flood Engine.

Calculates exact mass balance accounting for every simulation timestep,
computes input data completeness indicators (NOT ML confidence),
and surfaces physical/data uncertainty warnings.
"""

from typing import Any

from engines.flood.models import (
    DataCompletenessLevel,
    MassBalanceDiagnostic,
    UncertaintyCategory,
)


def compute_timestep_mass_balance(
    timestep_index: int,
    timestamp_iso: str,
    previous_storage_m3: float,
    gross_rainfall_input_m3: float,
    runoff_generated_m3: float,
    surface_inflow_m3: float,
    surface_outflow_m3: float,
    drainage_inflow_m3: float,
    drainage_outflow_m3: float,
    infiltration_losses_m3: float,
    current_storage_m3: float,
    tolerance: float = 1e-4
) -> MassBalanceDiagnostic:
    """
    Perform exact mass conservation verification for a single simulation timestep.

    Conservation Equation:
        Storage(t) = Storage(t-1) + Rainfall_Input - Infiltration_Losses - Drainage_Outflow

    Returns MassBalanceDiagnostic record with error calculation and validity status.
    """
    expected_storage = previous_storage_m3 + gross_rainfall_input_m3 - infiltration_losses_m3 - drainage_outflow_m3
    mass_balance_error = float(abs(current_storage_m3 - expected_storage))

    is_valid = bool(mass_balance_error <= tolerance)
    warnings: list[str] = []

    if not is_valid:
        warnings.append(
            f"Mass balance discrepancy ({mass_balance_error:.6f} m3) exceeded tolerance ({tolerance:.6f} m3) at timestep {timestep_index}"
        )

    return MassBalanceDiagnostic(
        timestep_index=timestep_index,
        timestamp_iso=timestamp_iso,
        previous_storage_m3=previous_storage_m3,
        rainfall_input_m3=gross_rainfall_input_m3,
        runoff_generated_m3=runoff_generated_m3,
        surface_inflow_m3=surface_inflow_m3,
        surface_outflow_m3=surface_outflow_m3,
        drainage_inflow_m3=drainage_inflow_m3,
        drainage_outflow_m3=drainage_outflow_m3,
        infiltration_losses_m3=infiltration_losses_m3,
        current_storage_m3=current_storage_m3,
        mass_balance_error_m3=mass_balance_error,
        is_valid=is_valid,
        warnings=warnings,
    )


def compute_input_completeness(
    rainfall_available: bool,
    forecast_available: bool,
    dem_available: bool,
    drainage_available: bool,
    known_capacity_ratio: float = 1.0,
    known_direction_ratio: float = 1.0,
    catchment_assoc_ratio: float = 1.0
) -> dict[str, Any]:
    """
    Compute input data completeness indicators (NOT ML confidence).

    Returns data quality score (0.0 to 1.0) and DataCompletenessLevel enum.
    """
    score = 0.0
    weights = {
        "dem": 0.25,
        "rainfall": 0.25,
        "drainage_topology": 0.20,
        "drainage_capacity": 0.15,
        "drainage_direction": 0.10,
        "catchment_assoc": 0.05,
    }

    if dem_available:
        score += weights["dem"]
    if rainfall_available or forecast_available:
        score += weights["rainfall"]
    if drainage_available:
        score += weights["drainage_topology"]

    score += weights["drainage_capacity"] * max(0.0, min(1.0, known_capacity_ratio))
    score += weights["drainage_direction"] * max(0.0, min(1.0, known_direction_ratio))
    score += weights["catchment_assoc"] * max(0.0, min(1.0, catchment_assoc_ratio))

    if score >= 0.8:
        level = DataCompletenessLevel.HIGH
    elif score >= 0.5:
        level = DataCompletenessLevel.MEDIUM
    else:
        level = DataCompletenessLevel.LOW

    return {
        "completeness_score": round(score, 4),
        "completeness_level": level.value,
        "dem_available": dem_available,
        "rainfall_available": rainfall_available,
        "drainage_available": drainage_available,
        "known_capacity_ratio": round(known_capacity_ratio, 4),
        "known_direction_ratio": round(known_direction_ratio, 4),
        "catchment_assoc_ratio": round(catchment_assoc_ratio, 4),
    }


def collect_uncertainty_warnings(
    rainfall_source_type: str,
    is_synthetic_forecast: bool,
    known_capacity_ratio: float,
    known_direction_ratio: float,
    catchment_assoc_ratio: float
) -> list[dict[str, str]]:
    """Surface structured simulation uncertainty warnings with explicit categories."""
    warnings: list[dict[str, str]] = []

    if "IMERG" in rainfall_source_type.upper():
        warnings.append({
            "category": UncertaintyCategory.DATA_UNCERTAINTY.value,
            "code": "COARSE_RAINFALL_RESOLUTION",
            "message": "IMERG rainfall observation has coarse resolution (~0.1° / 10km) spatially distributed across higher-resolution DEM cells."
        })

    if is_synthetic_forecast:
        warnings.append({
            "category": UncertaintyCategory.DATA_UNCERTAINTY.value,
            "code": "SYNTHETIC_FORECAST_USED",
            "message": "Simulation executed with SyntheticForecastProvider test fixture, not real meteorological forecast."
        })

    if known_capacity_ratio < 1.0:
        warnings.append({
            "category": UncertaintyCategory.PARAMETER_UNCERTAINTY.value,
            "code": "INCOMPLETE_DRAINAGE_CAPACITY",
            "message": f"{(1.0 - known_capacity_ratio)*100:.1f}% of drainage links have UNKNOWN capacity and rely on configured simulation policy."
        })

    if known_direction_ratio < 1.0:
        warnings.append({
            "category": UncertaintyCategory.STRUCTURAL_UNCERTAINTY.value,
            "code": "INCOMPLETE_DRAINAGE_DIRECTION",
            "message": f"{(1.0 - known_direction_ratio)*100:.1f}% of drainage links have UNKNOWN flow direction and are excluded from directed hydraulic routing."
        })

    if catchment_assoc_ratio < 1.0:
        warnings.append({
            "category": UncertaintyCategory.STRUCTURAL_UNCERTAINTY.value,
            "code": "UNASSOCIATED_CATCHMENTS",
            "message": f"{(1.0 - catchment_assoc_ratio)*100:.1f}% of catchments lack defensible drainage inlet associations."
        })

    return warnings
