"""
Rainfall-to-Runoff Transformation Module for Phase 6 Flood Engine.

Computes rainfall excess and runoff volume for grid cells based on configurable
hydrologic parameters (initial abstraction, infiltration, runoff coefficient).
Deterministic and mass-conserving.
"""

from engines.flood.models import RunoffModel, RunoffParameters


def calculate_rainfall_excess(
    rainfall_intensity_mm_hr: float,
    timestep_minutes: int,
    parameters: RunoffParameters,
    cell_area_m2: float
) -> dict[str, float]:
    """
    Calculate gross rainfall depth, rainfall excess, infiltration loss, and runoff volume
    for a given cell over a single timestep.

    Args:
        rainfall_intensity_mm_hr: Rainfall rate in mm/hr for the cell.
        timestep_minutes: Duration of simulation timestep in minutes.
        parameters: Hydrologic runoff configuration parameters.
        cell_area_m2: Grid cell area in m2.

    Returns:
        Dict containing:
            gross_rainfall_depth_mm
            rainfall_excess_mm
            runoff_depth_mm
            gross_rainfall_volume_m3
            runoff_volume_m3
            infiltration_loss_volume_m3
    """
    rainfall_intensity_mm_hr = max(rainfall_intensity_mm_hr, 0.0)
    if timestep_minutes <= 0:
        raise ValueError("timestep_minutes must be positive")
    if cell_area_m2 <= 0.0:
        raise ValueError("cell_area_m2 must be positive")

    dt_hours = timestep_minutes / 60.0
    gross_depth_mm = rainfall_intensity_mm_hr * dt_hours
    gross_volume_m3 = (gross_depth_mm / 1000.0) * cell_area_m2

    if parameters.model == RunoffModel.RATIONAL_COEFFICIENT:
        runoff_depth_mm = gross_depth_mm * max(0.0, min(1.0, parameters.runoff_coefficient))
        excess_depth_mm = runoff_depth_mm
    else:  # IMPERVIOUS_LOSS or INITIAL_DEPRESSION_LOSS
        infil_depth_mm = parameters.infiltration_rate_mm_hr * dt_hours
        net_excess_mm = max(0.0, gross_depth_mm - parameters.initial_loss_mm - infil_depth_mm)
        runoff_depth_mm = net_excess_mm * max(0.0, min(1.0, parameters.runoff_coefficient))
        excess_depth_mm = net_excess_mm

    runoff_volume_m3 = (runoff_depth_mm / 1000.0) * cell_area_m2
    loss_volume_m3 = max(0.0, gross_volume_m3 - runoff_volume_m3)

    return {
        "gross_rainfall_depth_mm": gross_depth_mm,
        "rainfall_excess_mm": excess_depth_mm,
        "runoff_depth_mm": runoff_depth_mm,
        "gross_rainfall_volume_m3": gross_volume_m3,
        "runoff_volume_m3": runoff_volume_m3,
        "infiltration_loss_volume_m3": loss_volume_m3,
    }
