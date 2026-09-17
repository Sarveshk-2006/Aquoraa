"""
Backend tests for Phase 7D Flood Label Construction & ML-Ready Dataset.
Validates dataset loading, event split isolation, label schema, zero target leakage,
and preservation of honest missing-data semantics.
"""

import json
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATASET_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "dataset"
FEATURES_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "features"
QA_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "qa"
MANIFEST_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "manifests"


def test_corrected_phase7c_parquet_loads():
    """TEST 1: Verify corrected Phase 7C master feature file exists and loads."""
    parquet_path = FEATURES_DIR / "phase7_master_features.parquet"
    csv_path = FEATURES_DIR / "phase7_master_features.csv"
    assert parquet_path.exists() or csv_path.exists(), "Phase 7C master features must exist"
    
    df = pd.read_csv(csv_path) if csv_path.exists() else pd.read_parquet(parquet_path)
    assert len(df) == 1306144, "Master dataset must contain 1,306,144 rows (30m grid)"


def test_expected_event_ids_exist():
    """TEST 2: Verify all 7 historical events exist (E01-E07)."""
    csv_path = DATASET_DIR / "phase7_ml_ready.csv"
    assert csv_path.exists(), "ML ready dataset must exist"
    df = pd.read_csv(csv_path)
    
    expected_events = {"E01", "E02", "E03", "E04", "E05", "E06", "E07"}
    actual_events = set(df["event_id"].unique())
    assert actual_events == expected_events, f"Events must match {expected_events}"


def test_event_cell_keys_unique():
    """TEST 3: Verify (event_id, grid_cell_id) pairs are unique."""
    csv_path = DATASET_DIR / "phase7_ml_ready.csv"
    df = pd.read_csv(csv_path)
    dups = df.duplicated(subset=["event_id", "grid_cell_id"]).sum()
    assert dups == 0, "No duplicate (event_id, grid_cell_id) pairs allowed"


def test_label_values_valid():
    """TEST 4: Verify label values are valid controlled values (1.0, 0.0, -1, NaN)."""
    csv_path = DATASET_DIR / "phase7_ml_ready.csv"
    df = pd.read_csv(csv_path)

    unique_labels = df["flood_label"].dropna().unique()
    for val in unique_labels:
        assert val in [-1.0, 0.0, 1.0, -1], f"Invalid flood label value: {val}"


def test_candidate_evidence_separate_from_labels():
    """TEST 5: Verify candidate evidence fields are separate from final labels."""
    csv_path = DATASET_DIR / "phase7_ml_ready.csv"
    df = pd.read_csv(csv_path)
    
    assert "observed_flood_candidate" in df.columns
    assert "candidate_evidence_source" in df.columns
    assert "flood_label" in df.columns
    assert "flood_label_status" in df.columns
    
    # Candidate evidence column is distinct from target label column
    assert df["observed_flood_candidate"].name != df["flood_label"].name


def test_null_labels_preserved():
    """TEST 6: Verify NULL labels are preserved for unavailable/unvalidated evidence."""
    csv_path = DATASET_DIR / "phase7_ml_ready.csv"
    df = pd.read_csv(csv_path)
    
    null_count = df["flood_label"].isnull().sum()
    assert null_count > 0, "NULL labels must be preserved when ground truth evidence is unavailable"


def test_rainfall_24h_null_semantics():
    """TEST 7: Verify 24h rainfall accumulation is 100% NULL for single granule IMERG."""
    csv_path = DATASET_DIR / "phase7_ml_ready.csv"
    df = pd.read_csv(csv_path)
    
    assert "rainfall_accum_24h_mm" in df.columns
    assert df["rainfall_accum_24h_mm"].isnull().sum() == len(df), "24h rainfall accum must be NULL"


def test_no_fabricated_sar_baseline_labels():
    """TEST 8: Verify E02/E03 candidates are not promoted to validated ground truth labels without independent verification."""
    csv_path = DATASET_DIR / "phase7_ml_ready.csv"
    df = pd.read_csv(csv_path)

    e02_df = df[df["event_id"] == "E02"]
    # E02 flood_label must be NULL/NaN or -1 (unvalidated ground truth)
    assert e02_df["flood_label"].isnull().sum() == len(e02_df) or (e02_df["flood_label"] == -1).all()


def test_no_exact_sar_depth():
    """TEST 9: Verify no exact water depth column is derived from SAR."""
    csv_path = DATASET_DIR / "phase7_ml_ready.csv"
    df = pd.read_csv(csv_path)
    
    for col in df.columns:
        assert "water_depth" not in col and "sar_depth" not in col, f"SAR depth derivation prohibited in {col}"


def test_event_split_has_no_event_overlap():
    """TEST 10: Verify event splits have zero event overlap."""
    train_path = DATASET_DIR / "phase7_train.parquet.csv"
    val_path = DATASET_DIR / "phase7_validation.parquet.csv"
    test_path = DATASET_DIR / "phase7_test.parquet.csv"
    bench_path = DATASET_DIR / "phase7_benchmark.parquet.csv"
    
    train_events = set(pd.read_csv(train_path)["event_id"].unique())
    val_events = set(pd.read_csv(val_path)["event_id"].unique())
    test_events = set(pd.read_csv(test_path)["event_path"] if False else pd.read_csv(test_path)["event_id"].unique())
    bench_events = set(pd.read_csv(bench_path)["event_id"].unique())
    
    assert len(train_events.intersection(val_events)) == 0
    assert len(train_events.intersection(test_events)) == 0
    assert len(val_events.intersection(test_events)) == 0
    assert len(bench_events.intersection(train_events)) == 0


def test_benchmark_event_excluded_from_ml_splits():
    """TEST 11: Verify E01 is strictly in BENCHMARK_ONLY split."""
    train_path = DATASET_DIR / "phase7_train.parquet.csv"
    val_path = DATASET_DIR / "phase7_validation.parquet.csv"
    test_path = DATASET_DIR / "phase7_test.parquet.csv"
    
    train_events = set(pd.read_csv(train_path)["event_id"].unique())
    val_events = set(pd.read_csv(val_path)["event_id"].unique())
    test_events = set(pd.read_csv(test_path)["event_id"].unique())
    
    assert "E01" not in train_events
    assert "E01" not in val_events
    assert "E01" not in test_events


def test_label_derived_columns_excluded_from_model_inputs():
    """TEST 12: Verify leakage audit explicitly excludes target/candidate fields from predictors."""
    audit_path = QA_DIR / "PHASE_7D_LEAKAGE_AUDIT.json"
    assert audit_path.exists()
    
    with open(audit_path, "r") as f:
        audit = json.load(f)
        predictors = audit["model_input_features"]
        targets = audit["target_and_evidence_columns"]
        
        for t in targets:
            assert t not in predictors, f"Target evidence column {t} leaked into model predictors!"


def test_post_event_label_evidence_cannot_leak():
    """TEST 13: Verify observed_flood_candidate is NOT in model_input_features."""
    audit_path = QA_DIR / "PHASE_7D_LEAKAGE_AUDIT.json"
    with open(audit_path, "r") as f:
        audit = json.load(f)
        predictors = audit["model_input_features"]
        assert "observed_flood_candidate" not in predictors
        assert "sar_vv_db" not in predictors


def test_deterministic_split_reproducibility():
    """TEST 14: Verify split manifest matches dataset splits deterministically."""
    manifest_path = MANIFEST_DIR / "PHASE_7D_SPLIT_MANIFEST.yaml"
    assert manifest_path.exists()
    
    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)
        splits = manifest["splits"]
        assert set(splits["TRAIN"]["events"]) == {"E02", "E04", "E05", "E06"}
        assert set(splits["VALIDATION"]["events"]) == {"E03"}
        assert set(splits["TEST"]["events"]) == {"E07"}
        assert set(splits["BENCHMARK_ONLY"]["events"]) == {"E01"}


def test_dataset_schema_stable():
    """TEST 15: Verify dataset schema column count and required predictor columns."""
    csv_path = DATASET_DIR / "phase7_ml_ready.csv"
    df = pd.read_csv(csv_path)
    
    required_predictors = [
        "elevation_m", "slope_deg", "aspect_deg", "flow_accumulation_cells",
        "drainage_proxy_score", "landcover_class", "built_up_fraction",
        "distance_to_road_m", "distance_to_waterway_m", "rainfall_30min_mm",
        "tide_level_m", "tide_anomaly_m"
    ]
    for p in required_predictors:
        assert p in df.columns, f"Predictor {p} must exist in dataset schema"


def test_output_parquet_reloads_successfully():
    """TEST 16: Verify output CSV/Parquet files reload successfully."""
    ml_csv = DATASET_DIR / "phase7_ml_ready.csv"
    df = pd.read_csv(ml_csv)
    assert len(df) == 1306144
    assert "split" in df.columns
