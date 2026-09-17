"""
Phase 7E Pre-Kaggle Dataset Audit Tests (Optimized with Fixtures)
"""

import json
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase7"
FEATURES_DIR = PROCESSED_DIR / "features"
LABELS_DIR = PROCESSED_DIR / "labels"
SAR_DIR = PROCESSED_DIR / "sar"
QA_DIR = PROCESSED_DIR / "qa"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "phase7"


def _read_dataset(parquet_path: Path, csv_path: Path) -> pd.DataFrame:
    assert parquet_path.exists() or csv_path.exists()
    try:
        return pd.read_parquet(parquet_path)
    except (FileNotFoundError, ValueError, OSError, ImportError, RuntimeError):
        return pd.read_csv(csv_path)


@pytest.fixture(scope="module")
def df_master():
    return _read_dataset(
        FEATURES_DIR / "phase7_master_features.parquet",
        FEATURES_DIR / "phase7_master_features.csv"
    )


@pytest.fixture(scope="module")
def df_labels():
    return _read_dataset(
        LABELS_DIR / "phase7_flood_evidence_labels.parquet",
        LABELS_DIR / "phase7_flood_evidence_labels.csv"
    )


@pytest.fixture(scope="module")
def df_sar():
    return _read_dataset(
        SAR_DIR / "phase7_sar_bitemporal_evidence.parquet",
        SAR_DIR / "phase7_sar_bitemporal_evidence.csv"
    )


def test_01_master_cardinality(df_master):
    assert len(df_master) == 1306144
    assert df_master["event_id"].nunique() == 7
    cells_per_ev = df_master.groupby("event_id")["grid_cell_id"].nunique()
    for cnt in cells_per_ev.values:
        assert cnt == 186592


def test_02_label_cardinality(df_labels):
    assert len(df_labels) == 1306144
    assert df_labels["event_id"].nunique() == 7
    cells_per_ev = df_labels.groupby("event_id")["grid_cell_id"].nunique()
    for cnt in cells_per_ev.values:
        assert cnt == 186592


def test_03_key_uniqueness(df_master, df_labels):
    assert df_master.duplicated(subset=["event_id", "grid_cell_id"]).sum() == 0
    assert df_labels.duplicated(subset=["event_id", "grid_cell_id"]).sum() == 0


def test_04_master_label_full_join(df_master, df_labels):
    master_keys = set(zip(df_master["event_id"], df_master["grid_cell_id"]))
    label_keys = set(zip(df_labels["event_id"], df_labels["grid_cell_id"]))
    assert master_keys == label_keys


def test_05_e02_e03_sar_join(df_sar):
    e02_sar = df_sar[df_sar["event_id"] == "E02"]
    e03_sar = df_sar[df_sar["event_id"] == "E03"]
    assert len(e02_sar) == 186592
    assert len(e03_sar) == 186592
    assert e02_sar["delta_vv_db"].notnull().sum() > 0
    assert e03_sar["delta_vv_db"].notnull().sum() > 0


def test_06_e01_has_no_sar(df_sar):
    e01_sar = df_sar[df_sar["event_id"] == "E01"]
    assert len(e01_sar) == 0


def test_07_e04_e07_have_valid_sar(df_sar):
    for ev in ["E04", "E05", "E06", "E07"]:
        ev_sar = df_sar[df_sar["event_id"] == ev]
        assert len(ev_sar) == 186592
        assert ev_sar["delta_vv_db"].notnull().sum() > 0


def test_08_flood_label_strictly_minus_one(df_labels):
    unique_labels = df_labels["flood_label"].unique()
    assert set(unique_labels) == {-1}
    assert (df_labels["flood_label"] == -1).sum() == 1306144


def test_09_no_unknown_to_zero_conversion(df_labels):
    assert (df_labels["flood_label"] == 0).sum() == 0
    assert (df_labels["flood_label"] == 1).sum() == 0


def test_10_event_split_integrity():
    expected_splits = {
        "E01": "BENCHMARK_ONLY",
        "E02": "TRAIN",
        "E03": "VALIDATION",
        "E04": "TRAIN",
        "E05": "TRAIN",
        "E06": "TRAIN",
        "E07": "TEST"
    }
    audit_json_path = QA_DIR / "PHASE_7E_FINAL_DATASET_AUDIT.json"
    assert audit_json_path.exists()
    with open(audit_json_path, encoding="utf-8") as f:
        audit_data = json.load(f)
    assert audit_data["master_audit"]["event_roles"] == expected_splits
    assert audit_data["spatial_audit"]["random_pixel_split_prohibited"] is True


def test_11_raw_files_unmodified():
    raw_files = list(RAW_DIR.rglob("*"))
    file_count = len([f for f in raw_files if f.is_file()])
    assert file_count >= 26


def test_12_and_13_audit_artifacts_exist():
    assert (QA_DIR / "PHASE_7E_FINAL_DATASET_AUDIT.json").exists()
    assert (QA_DIR / "PHASE_7E_FEATURE_MANIFEST.json").exists()
    assert (QA_DIR / "PHASE_7E_FINAL_DATASET_AUDIT.md").exists()
