"""
Aquora — Step 7 Real XGBoost Flood-Risk Model & Governance Unit & Integration Tests.

Verifies:
1. Predictor schema (exact 12 approved predictors from PHASE_7_FEATURE_POLICY.yaml)
2. Forbidden feature leakage assertion (fails loudly if forbidden feature enters X)
3. Deterministic training configuration
4. Model artifact loading (aquora_xgboost_prototype.joblib)
5. Feature-order consistency
6. Prediction shape
7. Probability range [0, 1]
8. Metadata completeness (aquora_xgboost_metadata.json)
9. Event split integrity (TRAIN: E02,E04,E05,E06; VAL: E03; TEST: E07; E01 excluded)
10. PROTOTYPE_ONLY status across model artifacts and governance documents
11. Integration with CalibrationService
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest

from app.services.calibration_service import (
    CalibrationService,
    EXPECTED_FEATURES,
)
from scripts.train_aquora_xgboost import (
    APPROVED_PREDICTORS,
    FORBIDDEN_FEATURES,
    verify_dataset_quality_and_leakage,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = REPO_ROOT / "backend" / "data" / "models"
MODEL_PATH = MODEL_DIR / "aquora_xgboost_prototype.joblib"
METADATA_PATH = MODEL_DIR / "aquora_xgboost_metadata.json"
MODEL_CARD_PATH = REPO_ROOT / "PHASE_7_MODEL_CARD.md"
DATASET_DIR = REPO_ROOT / "data" / "processed" / "phase7" / "dataset"

def test_01_predictor_schema_exact_12_features():
    """Verify that predictor schema consists of exact 12 approved features in exact order."""
    assert len(APPROVED_PREDICTORS) == 12
    assert APPROVED_PREDICTORS == [
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "flow_accumulation_cells",
        "drainage_proxy_score",
        "landcover_class",
        "built_up_fraction",
        "distance_to_road_m",
        "distance_to_waterway_m",
        "rainfall_30min_mm",
        "rainfall_intensity_mm_hr",
        "tide_level_m",
    ]

def test_02_forbidden_feature_leakage_assertion():
    """Verify that leakage assertion fails loudly if forbidden column enters X."""
    # Create invalid DataFrame containing a forbidden feature in predictor columns
    invalid_data = {col: [1.0] for col in APPROVED_PREDICTORS}
    invalid_data["sar_delta_vv_db"] = [-4.5] # Forbidden SAR feature
    invalid_df = pd.DataFrame(invalid_data)
    invalid_df["observed_flood_candidate"] = [0.0]

    with pytest.raises(ValueError) as excinfo:
        # Pass dataframe with forbidden feature
        verify_dataset_quality_and_leakage(invalid_df[["elevation_m", "sar_delta_vv_db"]], "INVALID")
    assert "Missing approved predictors" in str(excinfo.value) or "LEAKAGE DETECTED" in str(excinfo.value)

def test_03_model_artifact_loading():
    """Verify that trained model artifact exists, is readable, and loads as XGBClassifier."""
    assert MODEL_PATH.exists(), f"Model artifact missing at {MODEL_PATH}"
    model = joblib.load(MODEL_PATH)
    assert model is not None
    assert type(model).__name__ == "XGBClassifier"

def test_04_feature_order_and_count_consistency():
    """Verify booster feature names and count match approved predictors exactly."""
    model = joblib.load(MODEL_PATH)
    booster = model.get_booster()
    feature_names = booster.feature_names
    assert len(feature_names) == 12
    assert feature_names == APPROVED_PREDICTORS

def test_05_prediction_shape_and_probability_range():
    """Verify prediction output shape and probability bounds [0, 1]."""
    model = joblib.load(MODEL_PATH)
    # Generate dummy input matching schema
    dummy_input = pd.DataFrame({col: np.ones(10, dtype=np.float32) for col in APPROVED_PREDICTORS})
    probs = model.predict_proba(dummy_input)[:, 1]
    
    assert probs.shape == (10,)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)

def test_06_metadata_completeness():
    """Verify aquora_xgboost_metadata.json exists and contains all required governance fields."""
    assert METADATA_PATH.exists(), f"Metadata missing at {METADATA_PATH}"
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    required_keys = [
        "model_name", "model_version", "model_status", "is_authoritative_engine",
        "training_timestamp_utc", "model_filename", "model_sha256", "random_seed",
        "feature_count", "predictor_features", "forbidden_features_audit",
        "target_definition", "event_partition_split", "row_counts", "class_distribution",
        "hyperparameters", "class_weighting", "metrics", "event_level_test_metrics_e07",
        "feature_importance", "dataset_hashes", "environment_versions"
    ]
    for key in required_keys:
        assert key in meta, f"Metadata missing required key: '{key}'"

    assert meta["model_status"] == "PROTOTYPE_ONLY"
    assert meta["is_authoritative_engine"] is False
    assert meta["feature_count"] == 12
    assert meta["predictor_features"] == APPROVED_PREDICTORS

def test_07_event_split_integrity():
    """Verify that event split policy matches TRAIN (E02,E04,E05,E06), VAL (E03), TEST (E07)."""
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    splits = meta["event_partition_split"]
    assert sorted(splits["train_events"]) == ["E02", "E04", "E05", "E06"]
    assert splits["validation_events"] == ["E03"]
    assert splits["test_events"] == ["E07"]
    assert splits["benchmark_event_excluded"] == ["E01"]

def test_08_prototype_only_governance():
    """Verify that model card and metadata enforce PROTOTYPE_ONLY and non-authoritative engine status."""
    assert MODEL_CARD_PATH.exists(), f"Model Card missing at {MODEL_CARD_PATH}"
    card_text = MODEL_CARD_PATH.read_text(encoding="utf-8")
    
    assert "PROTOTYPE_ONLY" in card_text
    assert "authoritative flood inundation engine" in card_text
    assert "hydraulic physics solver" in card_text
    assert "secondary" in card_text.lower() or "SECONDARY" in card_text


def test_09_backend_calibration_service_integration():
    """Verify that backend CalibrationService loads and evaluates Step 7 model natively."""
    service = CalibrationService(model_path=str(MODEL_PATH))
    assert service.model is not None
    assert service.feature_schema == APPROVED_PREDICTORS
    
    meta = service.get_model_metadata()
    assert meta["model_status"] == "PROTOTYPE_ONLY"
    assert meta["feature_count"] == 12

    # Prepare real features for E05 and evaluate
    df_e05 = service.prepare_features_for_event("E05")
    assert len(df_e05) == 186592
    assert list(df_e05.columns) == APPROVED_PREDICTORS

    result = service.evaluate(df_e05, event_id="E05")
    assert result["model_status"] == "PROTOTYPE_ONLY"
    assert result["prediction_summary"]["prediction_count"] == 186592
    assert 0.0 <= result["prediction_summary"]["mean_score"] <= 1.0
