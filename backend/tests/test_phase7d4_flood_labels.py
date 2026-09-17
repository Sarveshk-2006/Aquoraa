"""
Unit tests for Phase 7D.4 Flood Evidence + Label Construction.

Validates conservative label philosophy, permanent water treatment, SAR evidence thresholding,
non-fabrication of ground truth, cardinal output integrity, and zero target leakage.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
LABELS_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "labels"
QA_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "qa"
FEATURES_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "features"


@pytest.fixture
def label_audit_json():
    json_path = QA_DIR / "PHASE_7D4_LABEL_AUDIT.json"
    assert json_path.exists(), f"Phase 7D.4 audit JSON not found at {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def label_provenance_json():
    json_path = LABELS_DIR / "PHASE_7D4_LABEL_PROVENANCE.json"
    assert json_path.exists(), f"Phase 7D.4 provenance JSON not found at {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def labels_df():
    csv_path = LABELS_DIR / "phase7_flood_evidence_labels.csv"
    parquet_path = LABELS_DIR / "phase7_flood_evidence_labels.parquet"
    assert csv_path.exists() or parquet_path.exists()
    try:
        return pd.read_parquet(parquet_path)
    except (FileNotFoundError, ValueError, OSError, ImportError, RuntimeError):
        return pd.read_csv(csv_path)


def test_1_permanent_water_treatment(labels_df):
    pw_rows = labels_df[labels_df["permanent_water"] == 1]
    assert len(pw_rows) > 0
    # Permanent water cells get flood_label = -1
    assert (pw_rows["flood_label"] == -1).all()
    # Non-E01 permanent water cells get label_status = EXCLUDED_PERMANENT_WATER
    pw_non_e01 = pw_rows[pw_rows["event_id"] != "E01"]
    assert (pw_non_e01["label_status"] == "EXCLUDED_PERMANENT_WATER").all()


def test_2_missing_sar_label_unknown(labels_df):
    missing_sar = labels_df[labels_df["sar_delta_vv_db"].isnull()]
    assert len(missing_sar) > 0
    assert (missing_sar["flood_label"] == -1).all()


def test_3_strong_negative_sar_candidate_not_verified_flood(labels_df):
    strong_sar = labels_df[(labels_df["sar_strong_negative_change"] == 1) & (labels_df["permanent_water"] == 0) & (labels_df["sar_usable_for_label"] == 1)]
    assert len(strong_sar) > 0
    # Strong negative SAR creates evidence candidate, but is NOT promoted to VERIFIED ground truth
    assert (strong_sar["flood_label"] == -1).all()
    statuses = set(strong_sar["label_status"].unique())
    assert "VERIFIED" not in statuses
    assert "EVIDENCE_SUPPORTED" in statuses


def test_4_moderate_negative_sar_evidence_strength(labels_df):
    mod_sar = labels_df[(labels_df["sar_moderate_negative_change"] == 1) & (labels_df["sar_strong_negative_change"] == 0) & (labels_df["permanent_water"] == 0) & (labels_df["sar_usable_for_label"] == 1)]
    assert len(mod_sar) > 0
    assert (mod_sar["evidence_strength"] == "MODERATE").all()


def test_5_weak_negative_sar_evidence_strength(labels_df):
    weak_sar = labels_df[(labels_df["sar_weak_negative_change"] == 1) & (labels_df["sar_moderate_negative_change"] == 0) & (labels_df["permanent_water"] == 0) & (labels_df["sar_usable_for_label"] == 1)]
    assert len(weak_sar) > 0
    assert (weak_sar["evidence_strength"] == "WEAK").all()


def test_6_stable_sar_not_automatically_non_flood(labels_df):
    stable_sar = labels_df[(labels_df["event_id"].isin(["E02", "E03"])) & (labels_df["sar_strong_negative_change"] == 0) & (labels_df["sar_moderate_negative_change"] == 0) & (labels_df["sar_weak_negative_change"] == 0) & (labels_df["permanent_water"] == 0) & (labels_df["sar_usable_for_label"] == 1)]
    assert len(stable_sar) > 0
    # Stable SAR does NOT automatically become 0 (non-flood)
    assert (stable_sar["flood_label"] == -1).all()
    assert (stable_sar["label_status"] == "UNKNOWN").all()


def test_7_e01_benchmark_only_no_sar(labels_df):
    e01_df = labels_df[labels_df["event_id"] == "E01"]
    assert len(e01_df) == 186592
    assert (e01_df["flood_label"] == -1).all()
    assert (e01_df["label_status"] == "BENCHMARK_ONLY").all()
    assert (e01_df["sar_usable_for_label"] == 0).all()


def test_8_and_9_e02_and_e03_sar_join(labels_df):
    e02_df = labels_df[labels_df["event_id"] == "E02"]
    e03_df = labels_df[labels_df["event_id"] == "E03"]
    assert len(e02_df) == 186592
    assert len(e03_df) == 186592
    assert (e02_df["sar_usable_for_label"].sum()) > 150000
    assert (e03_df["sar_usable_for_label"].sum()) > 150000


def test_10_e04_to_e07_no_fabricated_sar_evidence(labels_df):
    other_df = labels_df[labels_df["event_id"].isin(["E04", "E05", "E06", "E07"])]
    assert len(other_df) == 186592 * 4
    # In Step 5, real official Sentinel-1 GRD imagery was acquired & processed for E04-E07
    non_water = other_df[other_df["permanent_water"] == 0]
    assert (non_water["sar_usable_for_label"].sum()) > 600000
    assert (other_df["flood_label"] == -1).all()


def test_11_and_14_no_duplicates_and_unique_keys(labels_df):
    dups = labels_df.duplicated(subset=["event_id", "grid_cell_id"]).sum()
    assert dups == 0


def test_12_and_13_exact_cardinality_1306144(labels_df):
    assert len(labels_df) == 1306144
    events = set(labels_df["event_id"].unique())
    assert events == {"E01", "E02", "E03", "E04", "E05", "E06", "E07"}
    cells_per_event = labels_df.groupby("event_id")["grid_cell_id"].nunique()
    for cnt in cells_per_event.values:
        assert cnt == 186592


def test_15_master_grid_join_integrity(labels_df):
    master_csv = FEATURES_DIR / "phase7_master_features.csv"
    master_parquet = FEATURES_DIR / "phase7_master_features.parquet"
    try:
        df_master = pd.read_parquet(master_parquet)
    except (FileNotFoundError, ValueError, OSError, ImportError, RuntimeError):
        df_master = pd.read_csv(master_csv)

    master_keys = set(zip(df_master["event_id"], df_master["grid_cell_id"]))
    label_keys = set(zip(labels_df["event_id"], labels_df["grid_cell_id"]))
    assert master_keys == label_keys


def test_16_raw_data_immutability(label_audit_json):
    assert label_audit_json["raw_data_immutability"]["raw_files_modified"] == 0
    assert label_audit_json["raw_data_immutability"]["status"] == "PASSED"


def test_17_no_network_calls(label_audit_json):
    assert label_audit_json["network_calls_performed"] == 0


def test_18_no_ml_training(label_audit_json):
    assert label_audit_json["ml_training_executed"] is False
    assert label_audit_json["verdict"] == "PHASE 7D.4 COMPLETE WITH LIMITATIONS — READY FOR DATASET AUDIT"
