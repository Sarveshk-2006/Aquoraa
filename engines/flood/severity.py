"""
Severity Classification & Temporal Peak Tracking Module for Phase 6 Flood Engine.

Classifies cell-level flood severity levels and tracks flood onset timestamps,
peak water depths, peak timestamps, and flood durations over time.
"""

import numpy as np
from engines.flood.models import FloodSeverity


def classify_depth_severity(water_depth_m: float) -> FloodSeverity:
    """
    Classify inundation severity based on cell water depth in meters.

    Thresholds:
    - DRY: < 0.05 m
    - LOW: 0.05 m to 0.15 m
    - MODERATE: 0.15 m to 0.30 m
    - HIGH: 0.30 m to 0.60 m
    - SEVERE: >= 0.60 m
    """
    if water_depth_m < 0.05:
        return FloodSeverity.DRY
    elif water_depth_m < 0.15:
        return FloodSeverity.LOW
    elif water_depth_m < 0.30:
        return FloodSeverity.MODERATE
    elif water_depth_m < 0.60:
        return FloodSeverity.HIGH
    else:
        return FloodSeverity.SEVERE


def classify_depth_grid(depth_grid_m: np.ndarray) -> np.ndarray:
    """Map 2D water depth array to 2D string array of FloodSeverity enum values."""
    rows, cols = depth_grid_m.shape
    severity_grid = np.full((rows, cols), FloodSeverity.DRY.value, dtype=object)

    for r in range(rows):
        for c in range(cols):
            severity_grid[r, c] = classify_depth_severity(depth_grid_m[r, c]).value

    return severity_grid


def update_onset_and_peak_trackers(
    current_depth_grid_m: np.ndarray,
    timestep_iso: str,
    dt_minutes: int,
    onset_grid: np.ndarray,
    peak_depth_grid: np.ndarray,
    peak_time_grid: np.ndarray,
    duration_grid_min: np.ndarray
) -> None:
    """
    In-place update of onset timestamps, peak water depths, peak timestamps,
    and cumulative flood duration for all cells.

    Onset threshold: depth >= 0.05 m (5 cm).
    """
    rows, cols = current_depth_grid_m.shape

    for r in range(rows):
        for c in range(cols):
            d = current_depth_grid_m[r, c]
            if d >= 0.05:
                # 1. Onset timestamp
                if onset_grid[r, c] is None or onset_grid[r, c] == "":
                    onset_grid[r, c] = timestep_iso

                # 2. Cumulative duration
                duration_grid_min[r, c] += dt_minutes

                # 3. Peak depth & peak timestamp
                if d > peak_depth_grid[r, c]:
                    peak_depth_grid[r, c] = d
                    peak_time_grid[r, c] = timestep_iso
