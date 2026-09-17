"""
Core Deterministic Timestep Solver for Phase 6 Flood Engine.

Couples rainfall-runoff generation, surface storage, D8 terrain surface routing,
and municipal drainage network removal into a mass-conserving temporal simulation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from engines.flood.diagnostics import (
    collect_uncertainty_warnings,
    compute_input_completeness,
    compute_timestep_mass_balance,
)
from engines.flood.drainage_coupling import apply_drainage_coupling
from engines.flood.models import (
    DrainageCouplingPolicy,
    FloodSeverity,
    MassBalanceDiagnostic,
    RunoffParameters,
)
from engines.flood.runoff import calculate_rainfall_excess
from engines.flood.severity import (
    classify_depth_severity,
    update_onset_and_peak_trackers,
)
from engines.flood.surface_routing import route_surface_water_step
from engines.flood.validation import validate_simulation_inputs


def run_flood_simulation_loop(
    dem_metadata: dict[str, Any],
    elevation_array: np.ndarray,
    flow_dir_array: np.ndarray,
    rainfall_series: list[dict[str, Any]],
    drainage_network: dict[str, Any],
    cell_inlet_associations: dict[tuple[int, int], list[dict[str, Any]]],
    runoff_params: RunoffParameters,
    coupling_policy: DrainageCouplingPolicy,
    timestep_minutes: int = 10,
    horizon_minutes: int = 180,
    start_time_iso: str | None = None,
    resampling_method: str = "HOLD",
    mass_balance_tolerance: float = 1e-4
) -> dict[str, Any]:
    """
    Execute full deterministic temporal simulation loop from t=0 to t=horizon_minutes.

    Returns comprehensive simulation payload with per-timestep states, peak state maps,
    onset timelines, mass balance diagnostics, and data completeness metrics.
    """
    val = validate_simulation_inputs(
        dem_metadata, elevation_array, rainfall_series, timestep_minutes, horizon_minutes, mass_balance_tolerance
    )
    if not val["valid"]:
        raise ValueError(f"Simulation input validation failed: {val['error']}")

    rows, cols = elevation_array.shape
    dx = dem_metadata.get("resolution_dx")
    dy = dem_metadata.get("resolution_dy")
    if dx is None or dy is None:
        res = dem_metadata.get("resolution", (10.0, 10.0))
        if isinstance(res, (tuple, list)) and len(res) >= 2:
            dx, dy = res[0], res[1]
        else:
            dx, dy = float(res), float(res)

    dx = float(dx)
    dy = float(dy)
    cell_area_m2 = abs(dx * dy)

    # Initialize simulation clock
    if start_time_iso:
        try:
            start_dt = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
        except ValueError:
            start_dt = datetime.now(timezone.utc)
    else:
        start_dt = datetime.now(timezone.utc)

    num_steps = horizon_minutes // timestep_minutes + 1

    # Initialize 2D state grids
    storage_grid_m3 = np.zeros((rows, cols), dtype=np.float64)
    depression_capacity_grid_m3 = np.full((rows, cols), runoff_params.depression_storage_m3_per_m2 * cell_area_m2, dtype=np.float64)
    
    onset_grid = np.full((rows, cols), "", dtype=object)
    peak_depth_grid = np.zeros((rows, cols), dtype=np.float64)
    peak_time_grid = np.full((rows, cols), "", dtype=object)
    duration_grid_min = np.zeros((rows, cols), dtype=np.float64)

    timestep_diagnostics: list[MassBalanceDiagnostic] = []
    timestep_summaries: list[dict[str, Any]] = []
    timestep_depth_grids: list[np.ndarray] = []

    total_gross_rain_m3 = 0.0
    total_runoff_gen_m3 = 0.0
    total_infil_loss_m3 = 0.0
    total_drainage_removed_m3 = 0.0
    total_surface_transferred_m3 = 0.0

    # Calculate input completeness indicators
    nodes = drainage_network.get("nodes", {})
    links = drainage_network.get("links", {})
    known_cap_count = sum(1 for l in links.values() if l.get("capacity_m3s") is not None)
    known_dir_count = sum(1 for l in links.values() if str(l.get("direction_status", "")).upper() == "KNOWN")
    known_cap_ratio = (known_cap_count / len(links)) if links else 1.0
    known_dir_ratio = (known_dir_count / len(links)) if links else 1.0

    completeness_info = compute_input_completeness(
        rainfall_available=True,
        forecast_available=False,
        dem_available=True,
        drainage_available=bool(nodes),
        known_capacity_ratio=known_cap_ratio,
        known_direction_ratio=known_dir_ratio,
        catchment_assoc_ratio=1.0 if cell_inlet_associations else 0.0
    )

    rainfall_source_type = str(rainfall_series[0].get("source_type", "OBSERVATION")) if rainfall_series else "OBSERVATION"
    uncertainty_warnings = collect_uncertainty_warnings(
        rainfall_source_type=rainfall_source_type,
        is_synthetic_forecast="SYNTHETIC" in rainfall_source_type.upper(),
        known_capacity_ratio=known_cap_ratio,
        known_direction_ratio=known_dir_ratio,
        catchment_assoc_ratio=1.0 if cell_inlet_associations else 0.0
    )

    # ----------------------------------------------------
    # TEMPORAL SIMULATION LOOP
    # ----------------------------------------------------
    for step_idx in range(num_steps):
        elapsed_min = step_idx * timestep_minutes
        curr_dt = start_dt + timedelta(minutes=elapsed_min)
        curr_iso = curr_dt.isoformat()

        # 1. Resolve rainfall intensity for current timestep
        rain_intensity_mm_hr = _resolve_rainfall_for_step(
            rainfall_series, elapsed_min, resampling_method
        )

        prev_storage_m3 = float(np.sum(storage_grid_m3))

        # 2. Rainfall-Runoff Generation
        runoff_res = calculate_rainfall_excess(
            rain_intensity_mm_hr, timestep_minutes, runoff_params, cell_area_m2
        )
        gross_rain_step_m3 = runoff_res["gross_rainfall_volume_m3"] * rows * cols
        runoff_step_m3 = runoff_res["runoff_volume_m3"] * rows * cols
        infil_loss_step_m3 = runoff_res["infiltration_loss_volume_m3"] * rows * cols

        total_gross_rain_m3 += gross_rain_step_m3
        total_runoff_gen_m3 += runoff_step_m3
        total_infil_loss_m3 += infil_loss_step_m3

        # 3. Add runoff to surface storage
        storage_grid_m3 += runoff_res["runoff_volume_m3"]

        # 4. D8 Surface Routing
        routing_res = route_surface_water_step(
            storage_grid_m3, flow_dir_array, depression_capacity_grid_m3, max_transfer_ratio=0.5
        )
        storage_grid_m3 = routing_res["updated_storage_grid_m3"]
        surf_inflow_step_m3 = float(np.sum(routing_res["surface_inflow_grid_m3"]))
        surf_outflow_step_m3 = float(np.sum(routing_res["surface_outflow_grid_m3"]))
        total_surface_transferred_m3 += routing_res["total_surface_transferred_m3"]

        # 5. Drainage Coupling
        drainage_res = apply_drainage_coupling(
            storage_grid_m3, cell_inlet_associations, drainage_network, timestep_minutes, coupling_policy
        )
        storage_grid_m3 = drainage_res["updated_storage_grid_m3"]
        drainage_outflow_step_m3 = drainage_res["total_drainage_removed_m3"]
        total_drainage_removed_m3 += drainage_outflow_step_m3

        curr_storage_m3 = float(np.sum(storage_grid_m3))

        # 6. Mass Balance Diagnostics & Accounting
        diag = compute_timestep_mass_balance(
            timestep_index=step_idx,
            timestamp_iso=curr_iso,
            previous_storage_m3=prev_storage_m3,
            gross_rainfall_input_m3=gross_rain_step_m3,
            runoff_generated_m3=runoff_step_m3,
            surface_inflow_m3=surf_inflow_step_m3,
            surface_outflow_m3=surf_outflow_step_m3,
            drainage_inflow_m3=0.0,
            drainage_outflow_m3=drainage_outflow_step_m3,
            infiltration_losses_m3=infil_loss_step_m3,
            current_storage_m3=curr_storage_m3,
            tolerance=mass_balance_tolerance
        )
        timestep_diagnostics.append(diag)

        # 7. Water Depth & Onset / Peak State Tracking
        water_depth_grid_m = storage_grid_m3 / cell_area_m2
        timestep_depth_grids.append(water_depth_grid_m.copy())
        update_onset_and_peak_trackers(
            water_depth_grid_m, curr_iso, timestep_minutes,
            onset_grid, peak_depth_grid, peak_time_grid, duration_grid_min
        )

        # Record step summary
        timestep_summaries.append({
            "step_index": int(step_idx),
            "elapsed_minutes": int(elapsed_min),
            "timestamp_iso": curr_iso,
            "rainfall_intensity_mm_hr": float(rain_intensity_mm_hr),
            "gross_rain_volume_m3": float(gross_rain_step_m3),
            "runoff_volume_m3": float(runoff_step_m3),
            "surface_storage_m3": float(curr_storage_m3),
            "drainage_removed_m3": float(drainage_outflow_step_m3),
            "max_depth_m": float(np.max(water_depth_grid_m)),
            "flooded_cells_count": int(np.sum(water_depth_grid_m >= 0.05)),
            "mass_balance_error_m3": float(diag.mass_balance_error_m3),
            "is_valid": bool(diag.is_valid),
        })

    # Final summary calculations
    final_depth_grid_m = storage_grid_m3 / cell_area_m2
    peak_severity_grid = np.full((rows, cols), FloodSeverity.DRY.value, dtype=object)
    for r in range(rows):
        for c in range(cols):
            peak_severity_grid[r, c] = classify_depth_severity(peak_depth_grid[r, c]).value

    overall_mass_balance_error = float(abs(
        curr_storage_m3 - (total_gross_rain_m3 - total_infil_loss_m3 - total_drainage_removed_m3)
    ))

    return {
        "start_time_iso": start_dt.isoformat(),
        "horizon_minutes": int(horizon_minutes),
        "timestep_minutes": int(timestep_minutes),
        "total_timesteps": int(num_steps),
        "rows": int(rows),
        "cols": int(cols),
        "cell_area_m2": float(cell_area_m2),
        "totals": {
            "total_gross_rain_m3": float(total_gross_rain_m3),
            "total_runoff_gen_m3": float(total_runoff_gen_m3),
            "total_infil_loss_m3": float(total_infil_loss_m3),
            "total_drainage_removed_m3": float(total_drainage_removed_m3),
            "total_surface_transferred_m3": float(total_surface_transferred_m3),
            "final_surface_storage_m3": float(curr_storage_m3),
            "overall_mass_balance_error_m3": float(overall_mass_balance_error),
        },
        "input_completeness": completeness_info,
        "warnings": uncertainty_warnings,
        "timestep_summaries": timestep_summaries,
        "diagnostics": [d.__dict__ for d in timestep_diagnostics],
        "timestep_depth_grids": timestep_depth_grids,
        "final_storage_grid_m3": storage_grid_m3,
        "final_depth_grid_m": final_depth_grid_m,
        "peak_depth_grid_m": peak_depth_grid,
        "peak_severity_grid": peak_severity_grid,
        "onset_grid_iso": onset_grid,
        "peak_time_grid_iso": peak_time_grid,
        "duration_grid_min": duration_grid_min,
    }


def _resolve_rainfall_for_step(
    rainfall_series: list[dict[str, Any]],
    elapsed_minutes: int,
    resampling_method: str
) -> float:
    """Resolve rainfall intensity in mm/hr for the given elapsed simulation time."""
    if not rainfall_series:
        return 0.0

    if len(rainfall_series) == 1:
        return float(rainfall_series[0].get("rainfall_intensity_mm_hr", 0.0))

    # Match time series offset
    step_idx = min(elapsed_minutes // 30, len(rainfall_series) - 1)
    val = float(rainfall_series[step_idx].get("rainfall_intensity_mm_hr", 0.0))
    return max(0.0, val)
