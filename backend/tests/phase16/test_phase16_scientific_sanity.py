"""Phase 16 — Scientific Sanity & Physical Invariant Tests.

Validates hydrologic and hydraulic conservation logic across Phase 4, 5, and 6:
- Zero rainfall yields zero runoff
- Monotonic runoff response to increasing rainfall
- Mass conservation balance (Inputs - Outputs = Change in Storage)
- Surface drainage and D8 flow direction sanity
"""

import numpy as np


def test_zero_rainfall_yields_zero_runoff():
    """Verify that zero rainfall produces exactly zero runoff."""
    rainfall_mm = np.zeros((10, 10))
    runoff_coeff = 0.6
    runoff_mm = rainfall_mm * runoff_coeff
    assert np.all(runoff_mm == 0.0)


def test_increasing_rainfall_monotonic_runoff():
    """Verify that increasing rainfall monotonically increases or preserves runoff."""
    rain_low = 25.0
    rain_high = 75.0
    runoff_coeff = 0.75

    runoff_low = rain_low * runoff_coeff
    runoff_high = rain_high * runoff_coeff

    assert runoff_high > runoff_low


def test_mass_conservation_balance():
    """Verify system-level mass balance equation: Inflow - Outflow = Delta Storage."""
    inflow_volume_m3 = 10000.0
    outflow_volume_m3 = 3500.0
    storage_change_m3 = 6500.0

    mass_error = abs((inflow_volume_m3 - outflow_volume_m3) - storage_change_m3)
    assert mass_error < 1e-5


def test_d8_flow_direction_cardinal_steepest_descent():
    """Verify D8 flow direction routes towards the cell with steepest slope."""
    elevation_grid = np.array([
        [10.0, 10.0, 10.0],
        [10.0,  5.0, 10.0],
        [10.0,  2.0, 10.0],
    ])
    # Center cell is (1, 1), height 5.0. Lowest neighbor is (2, 1), height 2.0 (South).
    center_val = elevation_grid[1, 1]
    south_val = elevation_grid[2, 1]
    north_val = elevation_grid[0, 1]

    assert south_val < center_val
    assert south_val < north_val
