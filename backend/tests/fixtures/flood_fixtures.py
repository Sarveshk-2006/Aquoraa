"""
Deterministic Test Fixtures for Phase 6 Flood Simulation Engine.

LOCKED HARD INVARIANT:
Synthetic flood test datasets are explicitly labeled 'TEST FIXTURE ONLY — Synthetic Test Fixture'.
They MUST NEVER be used as or presented as real-world municipal flood measurements.
"""

from typing import Any

import numpy as np
import pytest

FIXTURE_LABEL = "TEST FIXTURE ONLY — Synthetic Test Fixture"


@pytest.fixture
def rain_only_fixture() -> dict[str, Any]:
    """Fixture A: Rain only on flat terrain with no drainage."""
    dem_meta = {
        "crs": "EPSG:32633",
        "resolution_dx": 10.0,
        "resolution_dy": 10.0,
    }
    elevation = np.full((5, 5), 10.0, dtype=np.float64)
    flow_dir = np.zeros((5, 5), dtype=np.int32)
    rainfall_series = [{"offset_minutes": 0, "rainfall_intensity_mm_hr": 30.0}]
    drainage_graph = {"nodes": {}, "links": {}, "adj": {}, "rev_adj": {}, "outfalls": set()}

    return {
        "label": FIXTURE_LABEL,
        "dem_metadata": dem_meta,
        "elevation": elevation,
        "flow_dir": flow_dir,
        "rainfall_series": rainfall_series,
        "drainage_graph": drainage_graph,
        "cell_inlet_assoc": {},
    }


@pytest.fixture
def sloped_terrain_fixture() -> dict[str, Any]:
    """Fixture B: Sloped terrain with downslope flow routing."""
    dem_meta = {
        "crs": "EPSG:32633",
        "resolution_dx": 10.0,
        "resolution_dy": 10.0,
    }
    elevation = np.array([
        [50.0, 50.0, 50.0],
        [40.0, 40.0, 40.0],
        [30.0, 30.0, 30.0],
    ], dtype=np.float64)

    # South-descending D8 code = 4
    flow_dir = np.array([
        [4, 4, 4],
        [4, 4, 4],
        [0, 0, 0],
    ], dtype=np.int32)

    rainfall_series = [{"offset_minutes": 0, "rainfall_intensity_mm_hr": 20.0}]
    drainage_graph = {"nodes": {}, "links": {}, "adj": {}, "rev_adj": {}, "outfalls": set()}

    return {
        "label": FIXTURE_LABEL,
        "dem_metadata": dem_meta,
        "elevation": elevation,
        "flow_dir": flow_dir,
        "rainfall_series": rainfall_series,
        "drainage_graph": drainage_graph,
        "cell_inlet_assoc": {},
    }


@pytest.fixture
def drainage_removal_fixture() -> dict[str, Any]:
    """Fixture C: Surface cell connected to valid drainage inlet with known capacity and outfall."""
    dem_meta = {
        "crs": "EPSG:32633",
        "resolution_dx": 10.0,
        "resolution_dy": 10.0,
    }
    elevation = np.full((3, 3), 10.0, dtype=np.float64)
    flow_dir = np.zeros((3, 3), dtype=np.int32)
    rainfall_series = [{"offset_minutes": 0, "rainfall_intensity_mm_hr": 60.0}]

    inlet_node = {"id": "N1", "node_type": "INLET"}
    outfall_node = {"id": "N2", "node_type": "OUTFALL"}
    pipe_link = {"id": "L1", "from_node_id": "N1", "to_node_id": "N2", "capacity_m3s": 10.0, "direction_status": "KNOWN"}

    drainage_graph = {
        "nodes": {"N1": inlet_node, "N2": outfall_node},
        "links": {"L1": pipe_link},
        "adj": {"N1": ["N2"], "N2": []},
        "rev_adj": {"N1": [], "N2": ["N1"]},
        "outfalls": {"N2"},
    }

    cell_inlet_assoc = {(0, 0): [inlet_node]}

    return {
        "label": FIXTURE_LABEL,
        "dem_metadata": dem_meta,
        "elevation": elevation,
        "flow_dir": flow_dir,
        "rainfall_series": rainfall_series,
        "drainage_graph": drainage_graph,
        "cell_inlet_assoc": cell_inlet_assoc,
    }
