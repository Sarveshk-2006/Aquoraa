"""
Surface Routing Module for Phase 6 Flood Engine.

Routes surface water across terrain cells using Phase 4 D8 flow directions,
respecting cell geometry, elevation constraints, and numerical stability limits.
Deterministic and mass-conserving.
"""

from typing import Any

import numpy as np

# Phase 4 D8 Flow Direction Mapping: (delta_row, delta_col)
D8_OFFSET_MAP: dict[int, tuple[int, int]] = {
    1: (0, 1),     # East
    2: (1, 1),     # Southeast
    4: (1, 0),     # South
    8: (1, -1),    # Southwest
    16: (0, -1),   # West
    32: (-1, -1),  # Northwest
    64: (-1, 0),   # North
    128: (-1, 1),  # Northeast
}


def route_surface_water_step(
    storage_grid_m3: np.ndarray,
    flow_direction_grid: np.ndarray,
    depression_capacity_m3_grid: np.ndarray,
    max_transfer_ratio: float = 0.5
) -> dict[str, Any]:
    """
    Execute one surface routing step across all grid cells using D8 flow directions.

    Args:
        storage_grid_m3: 2D numpy array of current surface water storage in m3.
        flow_direction_grid: 2D numpy array of Phase 4 D8 flow direction codes.
        depression_capacity_m3_grid: 2D numpy array of cell depression storage capacities in m3.
        max_transfer_ratio: Numerical stability Courant limit (<= 0.5).

    Returns:
        Dict containing:
            updated_storage_grid_m3
            surface_inflow_grid_m3
            surface_outflow_grid_m3
            total_surface_transferred_m3
    """
    rows, cols = storage_grid_m3.shape
    updated_storage = storage_grid_m3.copy()
    inflow_grid = np.zeros_like(storage_grid_m3, dtype=np.float64)
    outflow_grid = np.zeros_like(storage_grid_m3, dtype=np.float64)

    # Constrain Courant limiter to prevent numerical oscillation or negative storage
    transfer_limit = max(0.0, min(0.5, max_transfer_ratio))
    total_transferred = 0.0

    # Process transfer for all cells
    for r in range(rows):
        for c in range(cols):
            curr_storage = updated_storage[r, c]
            if curr_storage <= 0.0:
                continue

            depr_cap = depression_capacity_m3_grid[r, c]
            available_mobile = max(0.0, curr_storage - depr_cap)
            if available_mobile <= 0.0:
                continue

            d8_code = int(flow_direction_grid[r, c])
            if d8_code not in D8_OFFSET_MAP:
                # Sink (0), NoData (-1), or invalid code: retain water in cell
                continue

            dr, dc = D8_OFFSET_MAP[d8_code]
            nr, nc = r + dr, c + dc

            # Check bounds
            if 0 <= nr < rows and 0 <= nc < cols:
                # Flow downstream
                transfer_vol = available_mobile * transfer_limit
                if transfer_vol > 0.0:
                    outflow_grid[r, c] += transfer_vol
                    inflow_grid[nr, nc] += transfer_vol
                    total_transferred += transfer_vol

    # Apply net transfers deterministically
    updated_storage = updated_storage - outflow_grid + inflow_grid
    # Protect against floating point precision errors underflow below 0.0
    updated_storage = np.maximum(0.0, updated_storage)

    return {
        "updated_storage_grid_m3": updated_storage,
        "surface_inflow_grid_m3": inflow_grid,
        "surface_outflow_grid_m3": outflow_grid,
        "total_surface_transferred_m3": total_transferred,
    }
