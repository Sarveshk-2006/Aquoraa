"""
Unit tests for Phase 7C Master Dataset Final Consistency Gate.

Verifies detection of the 1,911-cell stale dataset defect, Phase 7D inheritance,
and zero network/data mutations.
"""

import json
import os

import pytest


@pytest.fixture
def gate_json():
    json_path = os.path.join(
        "data", "processed", "phase7", "qa", "PHASE_7C_MASTER_DATASET_FINAL_CONSISTENCY_AUDIT.json"
    )
    assert os.path.exists(json_path), f"Gate JSON not found: {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_gate_json_verdict(gate_json):
    assert gate_json["phase"] == "PHASE_7C_MASTER_DATASET_FINAL_CONSISTENCY_AUDIT"
    assert gate_json["defect_status"] == "MASTER_DATASET_STALE_OR_DEFECTIVE"
    assert gate_json["phase7d_consistency_status"] == "PHASE 7D DATASET ALSO REQUIRES REGENERATION"
    assert gate_json["final_verdict"] == "PHASE 7C MASTER GATE — BLOCKED — MASTER REGENERATION REQUIRED"
    assert gate_json["network_calls"] == 0
    assert gate_json["files_modified"] == 0
    assert gate_json["raw_data_status"] == "UNCHANGED"


def test_dataset_dimensions_audit(gate_json):
    dims = gate_json["dataset_dimensions"]
    assert dims["total_rows"] == 13377
    assert dims["unique_cells"] == 1911
    assert dims["event_count"] == 7
    assert dims["rows_per_event"] == 1911
    
    spacing = gate_json["grid_spacing"]
    assert spacing["x_spacing_m"] == 300.0
    assert spacing["y_spacing_m"] == 300.0


def test_corrected_grid_expectation(gate_json):
    exp = gate_json["corrected_grid_expectation"]
    assert exp["raster_width_cells"] == 392
    assert exp["raster_height_cells"] == 476
    assert exp["rectangular_cell_count"] == 186592
    assert exp["valid_mask_cell_count"] == 185666
    assert exp["expected_7_event_rows"] == 1306144
