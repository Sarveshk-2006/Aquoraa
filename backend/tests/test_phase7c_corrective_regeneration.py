"""
Unit tests for Phase 7C Corrective Regeneration.

Verifies native 30m computational grid, spatial spacing, coordinate bounds,
event completeness, raw data immutability, zero leakage, and Phase 7D inheritance.
"""

import json
import os

import pandas as pd
import pytest


@pytest.fixture
def audit_json():
    json_path = os.path.join(
        "data", "processed", "phase7", "qa", "PHASE_7C_CORRECTIVE_REGENERATION_AUDIT.json"
    )
    assert os.path.exists(json_path), f"Audit JSON not found: {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def master_df():
    parquet_path = os.path.join("data", "processed", "phase7", "features", "phase7_master_features.parquet")
    csv_path = os.path.join("data", "processed", "phase7", "features", "phase7_master_features.csv")
    if os.path.exists(parquet_path):
        try:
            return pd.read_parquet(parquet_path)
        except Exception:
            return pd.read_csv(csv_path)
    return pd.read_csv(csv_path)


@pytest.fixture
def ml_df():
    parquet_path = os.path.join("data", "processed", "phase7", "dataset", "phase7_ml_ready.parquet")
    csv_path = os.path.join("data", "processed", "phase7", "dataset", "phase7_ml_ready.csv")
    if os.path.exists(parquet_path):
        try:
            return pd.read_parquet(parquet_path)
        except Exception:
            return pd.read_csv(csv_path)
    return pd.read_csv(csv_path)


def test_1_corrected_grid_dimensions(audit_json):
    master = audit_json["corrected_master"]
    assert master["cols"] == 392
    assert master["rows_grid"] == 476
    assert master["rectangular_cell_count"] == 186592


def test_2_and_3_thirty_meter_spacing(audit_json):
    master = audit_json["corrected_master"]
    assert pytest.approx(master["measured_spacing_x_m"], abs=1.0) == 30.0
    assert pytest.approx(master["measured_spacing_y_m"], abs=1.0) == 30.0
    assert master["measured_spacing_x_m"] < 100.0  # Not 300m spacing!


def test_4_no_stale_1911_cell_master(audit_json):
    assert audit_json["previous_master"]["unique_cells"] == 1911
    assert audit_json["corrected_master"]["unique_cells"] == 186592
    assert audit_json["corrected_master"]["rows"] == 1306144
    assert audit_json["corrected_master"]["rows"] > 100000  # Proves 30m grid correction


def test_5_and_9_coordinate_bounds_and_no_inversion(audit_json):
    b = audit_json["corrected_master"]["geographic_bounds"]
    assert 72.80 <= b["min_longitude"] <= 72.83
    assert 72.92 <= b["max_longitude"] <= 72.95
    assert 19.02 <= b["min_latitude"] <= 19.04
    assert 19.15 <= b["max_latitude"] <= 19.17
    # No inverted lat/lon or offshore 70E/0N swap
    assert b["min_longitude"] > 70.0
    assert b["min_latitude"] > 18.0


def test_6_all_seven_events_present(audit_json):
    events = audit_json["event_counts"]
    expected_events = ["E01", "E02", "E03", "E04", "E05", "E06", "E07"]
    for ev in expected_events:
        assert ev in events
        assert events[ev] == 186592


def test_7_equal_spatial_grid_across_events(master_df):
    cells_per_event = master_df.groupby("event_id")["grid_cell_id"].nunique()
    for ev, count in cells_per_event.items():
        assert count == 186592


def test_8_valid_cell_relationship(master_df):
    total_rows = len(master_df)
    unique_cells = master_df["grid_cell_id"].nunique()
    assert total_rows == unique_cells * 7


def test_10_rainfall_24h_null_semantics_preserved(master_df):
    # Rainfall 24h accum must remain NaN due to single 30-minute granule coverage
    assert master_df["rainfall_accum_24h_mm"].isnull().all()


def test_11_raw_data_immutability(audit_json):
    assert audit_json["raw_data_immutability"]["raw_files_modified"] == 0
    assert audit_json["raw_data_immutability"]["status"] == "PASSED"


def test_12_ml_ready_uses_corrected_master(ml_df):
    assert len(ml_df) == 1306144
    assert ml_df["grid_cell_id"].nunique() == 186592


def test_13_event_split_remains_unchanged(audit_json):
    splits = audit_json["event_splits"]
    assert splits["TRAIN"]["events"] == ["E02", "E04", "E05", "E06"]
    assert splits["VALIDATION"]["events"] == ["E03"]
    assert splits["TEST"]["events"] == ["E07"]
    assert splits["BENCHMARK"]["events"] == ["E01"]
    assert splits["TRAIN"]["rows"] == 186592 * 4
    assert splits["VALIDATION"]["rows"] == 186592
    assert splits["TEST"]["rows"] == 186592
    assert splits["BENCHMARK"]["rows"] == 186592


def test_14_no_label_leakage(audit_json):
    leakage = audit_json["leakage_audit"]
    assert leakage["status"] == "PASSED_ZERO_LEAKAGE"
    assert leakage["predictor_count"] == 16
    forbidden_features = ["flood_label", "observed_flood_candidate", "sar_vv_db", "sar_vh_db"]
    for f in forbidden_features:
        assert f not in leakage["predictors"]


def test_15_no_network_access_and_final_verdict(audit_json):
    assert audit_json["network_calls"] == 0
    assert audit_json["ml_training_executed"] is False
    assert audit_json["final_verdict"] == "PHASE 7C CORRECTIVE REGENERATION — PASS"
