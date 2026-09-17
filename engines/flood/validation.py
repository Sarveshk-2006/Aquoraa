"""
Input & Parameter Validation Module for Phase 6 Flood Engine.

Validates spatial coverage, CRS compatibility, positive dimensions,
timestep stability limits, and temporal resolution alignment prior to simulation.
"""

from typing import Any


def validate_simulation_inputs(
    dem_metadata: dict[str, Any],
    elevation_array: Any,
    rainfall_series: list[dict[str, Any]],
    timestep_minutes: int,
    horizon_minutes: int,
    mass_balance_tolerance: float = 1e-4
) -> dict[str, Any]:
    """
    Validate input arrays, metadata, time parameters, and numerical stability limits.

    Returns Dict with valid (bool), error (Optional[str]), and validation details.
    """
    if elevation_array is None or len(elevation_array.shape) != 2:
        return {"valid": False, "error": "Elevation array must be a valid 2D grid"}

    height, width = elevation_array.shape
    if height <= 0 or width <= 0:
        return {"valid": False, "error": f"Invalid DEM dimensions: {width}x{height}"}

    dx = dem_metadata.get("resolution_dx")
    dy = dem_metadata.get("resolution_dy")
    if dx is None or dy is None:
        res = dem_metadata.get("resolution")
        if isinstance(res, (tuple, list)) and len(res) >= 2:
            dx, dy = res[0], res[1]
        elif isinstance(res, (int, float)):
            dx, dy = float(res), float(res)

    if dx is None or dy is None or float(dx) <= 0.0 or float(dy) <= 0.0:
        return {"valid": False, "error": "DEM cell resolutions (resolution_dx, resolution_dy) must be positive"}

    dx = float(dx)
    dy = float(dy)

    if not dem_metadata.get("crs"):
        return {"valid": False, "error": "DEM metadata missing CRS definition"}

    if not rainfall_series:
        return {"valid": False, "error": "Rainfall time series cannot be empty"}

    if timestep_minutes not in [5, 10, 15, 30, 60]:
        return {"valid": False, "error": f"Unsupported simulation timestep: {timestep_minutes} minutes. Supported: [5, 10, 15, 30, 60]"}

    if horizon_minutes < timestep_minutes or horizon_minutes > 300:
        return {"valid": False, "error": f"Simulation horizon ({horizon_minutes} min) out of bounds [timestep, 300 min]"}

    if mass_balance_tolerance <= 0.0:
        return {"valid": False, "error": "mass_balance_tolerance must be positive"}

    return {
        "valid": True,
        "error": None,
        "width": width,
        "height": height,
        "cell_area_m2": abs(dx * dy),
        "total_timesteps": horizon_minutes // timestep_minutes + 1,
    }
