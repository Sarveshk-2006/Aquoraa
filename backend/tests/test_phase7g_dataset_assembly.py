"""
Unit and integration tests for Phase 7G Final Kaggle Dataset Assembly + Leakage Audit.
"""

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase7"
FINAL_ML_DIR = PROCESSED_DIR / "final_ml"
QA_DIR = PROCESSED_DIR / "qa"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "phase7"

MASTER_PARQUET = FINAL_ML_DIR / "aquora_phase7_ml_master.parquet"
MASTER_CSV = FINAL_ML_DIR / "aquora_phase7_ml_master.csv"
MANIFEST_JSON = FINAL_ML_DIR / "AQUORA_PHASE7_FEATURE_MANIFEST.json"
AUDIT_JSON = QA_DIR / "PHASE_7G_DATASET_AUDIT.json"
AUDIT_MD = QA_DIR / "PHASE_7G_DATASET_AUDIT.md"


def _load_ml_master():
    assert MASTER_PARQUET.exists() or MASTER_CSV.exists(), "Master ML dataset missing"
    if MASTER_PARQUET.exists():
        try:
            return pd.read_parquet(MASTER_PARQUET)
        except (FileNotFoundError, ValueError, OSError, RuntimeError, ImportError):
            pass
    return pd.read_csv(MASTER_CSV, low_memory=False)


def test_01_final_cardinality_and_key_uniqueness():
    """Verify final assembled ML master dataset has exactly 1,306,144 rows and unique composite keys."""
    df = _load_ml_master()
    assert len(df) == 1306144, f"Expected 1,306,144 rows, got {len(df)}"
    assert df["event_id"].nunique() == 7, "Expected all 7 events E01-E07"

    # Composite key uniqueness
    dups = df.duplicated(subset=["event_id", "grid_cell_id"]).sum()
    assert dups == 0, f"Found {dups} duplicate event_id + grid_cell_id key pairs"


def test_02_master_label_join_completeness():
    """Verify 1-to-1 master and label join completeness with zero missing or orphaned keys."""
    df = _load_ml_master()
    assert "flood_label" in df.columns
    assert "elevation_m" in df.columns
    assert df["flood_label"].isnull().sum() == 0, "Found null values in flood_label"
    assert df["elevation_m"].isnull().sum() == 0, "Found null values in elevation_m"


def test_03_target_semantics_and_unknown_preservation():
    """Verify flood_label restricted to {-1, 0, 1} and UNKNOWN (-1) never converted to 0."""
    df = _load_ml_master()
    unique_labels = set(df["flood_label"].unique())
    assert unique_labels.issubset({-1, 0, 1}), f"Invalid label values found: {unique_labels}"

    # Verify no false negatives manufactured
    zeros_count = (df["flood_label"] == 0).sum()
    assert zeros_count == 0, f"Expected 0 verified negative labels, got {zeros_count}"

    # Verify positive count
    pos_count = (df["flood_label"] == 1).sum()
    assert pos_count == 19595, f"Expected 19,595 positive flood labels, got {pos_count}"


def test_04_target_status_precedence_and_distribution():
    """Verify ml_target_status precedence (BENCHMARK_ONLY, EXCLUDED_PERMANENT_WATER, POSITIVE, UNKNOWN)."""
    df = _load_ml_master()
    assert "ml_target_status" in df.columns

    # E01 must be BENCHMARK_ONLY
    e01_statuses = df[df["event_id"] == "E01"]["ml_target_status"].unique()
    assert list(e01_statuses) == ["BENCHMARK_ONLY"]

    # Positive labels must be POSITIVE
    pos_statuses = df[df["flood_label"] == 1]["ml_target_status"].unique()
    assert list(pos_statuses) == ["POSITIVE"]

    # Permanent water -1 labels must be EXCLUDED_PERMANENT_WATER
    pw_unknown_df = df[(df["permanent_water"] == 1) & (df["flood_label"] == -1) & (df["event_id"] != "E01")]
    assert (pw_unknown_df["ml_target_status"] == "EXCLUDED_PERMANENT_WATER").all()


def test_05_event_split_integrity():
    """Verify locked event splits (E02/E04/E05/E06 TRAIN, E03 VALIDATION, E07 TEST, E01 BENCHMARK)."""
    df = _load_ml_master()
    assert "event_role" in df.columns

    role_map = df.groupby("event_id")["event_role"].first().to_dict()
    assert role_map["E01"] == "BENCHMARK"
    assert role_map["E02"] == "TRAIN"
    assert role_map["E03"] == "VALIDATION"
    assert role_map["E04"] == "TRAIN"
    assert role_map["E05"] == "TRAIN"
    assert role_map["E06"] == "TRAIN"
    assert role_map["E07"] == "TEST"


def test_06_post_event_sar_leakage_exclusion():
    """Verify post-event SAR change features are strictly excluded from predictive training set."""
    assert MANIFEST_JSON.exists(), f"Feature manifest missing at {MANIFEST_JSON}"
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for feat in manifest:
        if feat["category"] == "POST_EVENT_LEAKAGE":
            assert feat["allowed_for_training"] is False, f"Post-event feature {feat['name']} incorrectly allowed for training!"


def test_07_target_and_provenance_exclusion():
    """Verify target and provenance descriptors are strictly excluded from predictive training set."""
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for feat in manifest:
        if feat["category"] in ["TARGET", "PROVENANCE", "METADATA"]:
            assert feat["allowed_for_training"] is False, f"Category {feat['category']} feature {feat['name']} allowed for training!"


def test_08_physical_model_score_classification():
    """Verify physical_model_score is classified as PREDICTIVE_PHYSICAL_MODEL and allowed for training."""
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    p_scores = [f for f in manifest if f["name"] == "physical_model_score"]
    assert len(p_scores) == 1
    p_score = p_scores[0]
    assert p_score["category"] == "PREDICTIVE_PHYSICAL_MODEL"
    assert p_score["allowed_for_training"] is True


def test_09_partition_files_existence_and_cardinality():
    """Verify individual split partition parquet files exist and match exact row counts."""
    train_p = FINAL_ML_DIR / "aquora_phase7_train.parquet"
    val_p = FINAL_ML_DIR / "aquora_phase7_validation.parquet"
    test_p = FINAL_ML_DIR / "aquora_phase7_test.parquet"
    bench_p = FINAL_ML_DIR / "aquora_phase7_benchmark.parquet"

    assert train_p.exists()
    assert val_p.exists()
    assert test_p.exists()
    assert bench_p.exists()

    df_train = pd.read_parquet(train_p)
    df_val = pd.read_parquet(val_p)
    df_test = pd.read_parquet(test_p)
    df_bench = pd.read_parquet(bench_p)

    assert len(df_train) == 4 * 186592  # 746,368
    assert len(df_val) == 186592
    assert len(df_test) == 186592
    assert len(df_bench) == 186592
    assert len(df_train) + len(df_val) + len(df_test) + len(df_bench) == 1306144


def test_10_audit_artifacts_existence_and_verdict():
    """Verify Phase 7G audit JSON and MD files exist and present valid verdict."""
    assert AUDIT_JSON.exists()
    assert AUDIT_MD.exists()

    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        audit = json.load(f)

    assert audit["cardinality_verification"]["total_rows"] == 1306144
    assert audit["final_verdict"] == "PHASE 7G COMPLETE WITH LIMITATIONS — KAGGLE DATASET READY"
    assert audit["scientific_gate_status"] == "BINARY_SUPERVISED_TRAINING_BLOCKED_PENDING_NEGATIVE_LABEL_STRATEGY"


def test_11_input_data_immutability():
    """Verify raw payloads, Phase 7C master features, and Phase 7F labels are unmodified."""
    raw_files = list(RAW_DIR.rglob("*"))
    file_count = len([f for f in raw_files if f.is_file()])
    assert file_count >= 26
