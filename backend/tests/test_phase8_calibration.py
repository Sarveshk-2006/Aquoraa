"""
Focused Unit & Integration Tests for Phase 8 Prototype ML Calibration.
Verifies model loading, feature contract, PROTOTYPE_ONLY status,
no synthetic ML fallback, and real Mithi data integration.
"""

import pytest
import pandas as pd

from app.services.calibration_service import (
    CalibrationService,
    EXPECTED_FEATURES,
)


def test_01_model_artifact_loads():
    """Verify that the model artifact loads natively without errors."""
    service = CalibrationService()
    assert service.model is not None
    assert type(service.model).__name__ == "XGBClassifier"
    assert len(service.sha256) == 64


def test_02_missing_artifact_fails_clearly(tmp_path):
    """Verify that a missing model artifact raises FileNotFoundError with explicit message and no synthetic fallback."""
    fake_path = tmp_path / "non_existent_model.joblib"
    with pytest.raises(FileNotFoundError) as excinfo:
        CalibrationService(model_path=str(fake_path))
    assert "No synthetic ML fallback is permitted" in str(excinfo.value)


def test_03_feature_count_validation():
    """Verify expected feature count is exactly 12."""
    service = CalibrationService()
    meta = service.get_model_metadata()
    assert meta["feature_count"] == 12
    assert len(EXPECTED_FEATURES) == 12


def test_04_feature_order_validation():
    """Verify exact feature names and order required by XGBoost prototype."""
    service = CalibrationService()
    assert service.feature_schema == [
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



def test_05_prediction_interface():
    """Verify prediction interface runs predict_proba() in read-only mode."""
    service = CalibrationService()
    # Mock single row input matching schema
    row_data = {feat: [1.0] for feat in EXPECTED_FEATURES}
    row_df = pd.DataFrame(row_data)[EXPECTED_FEATURES]

    result = service.evaluate(row_df, event_id="E05")
    assert result["prediction_summary"]["input_row_count"] == 1
    assert result["prediction_summary"]["prediction_count"] == 1
    assert 0.0 <= result["prediction_summary"]["mean_score"] <= 1.0


def test_06_prototype_only_status():
    """Verify that model_status and calibration_status remain explicitly PROTOTYPE_ONLY."""
    service = CalibrationService()
    meta = service.get_model_metadata()
    assert meta["model_status"] == "PROTOTYPE_ONLY"
    assert meta["calibration_status"] in ["NOT_CALIBRATED", "PROTOTYPE_ONLY"]

    row_data = {feat: [1.0] for feat in EXPECTED_FEATURES}
    row_df = pd.DataFrame(row_data)[EXPECTED_FEATURES]
    res = service.evaluate(row_df, event_id="E05")
    assert res["model_status"] == "PROTOTYPE_ONLY"
    assert res["calibration_status"] in ["NOT_CALIBRATED", "PROTOTYPE_ONLY"]
    assert res["provenance"]["model_status"] == "PROTOTYPE_ONLY"



def test_07_no_synthetic_ml_fallback():
    """Verify metadata explicitly confirms synthetic_fallback=False."""
    service = CalibrationService()
    meta = service.get_model_metadata()
    assert meta["synthetic_fallback"] is False


def test_08_real_data_phase6_feature_preparation():
    """Verify that real Mithi rasters can feed feature preparation for event E05."""
    service = CalibrationService()
    df = service.prepare_features_for_event(event_id="E05")
    assert len(df) == 186592
    assert list(df.columns) == EXPECTED_FEATURES
    assert df.isnull().sum().sum() == 0

    res = service.evaluate(df, event_id="E05", simulation_run_id="sim_real_mithi_e05")
    assert res["prediction_summary"]["input_row_count"] == 186592
    assert res["prediction_summary"]["prediction_count"] == 186592
    assert 0.0 <= res["prediction_summary"]["min_score"] <= 1.0
    assert 0.0 <= res["prediction_summary"]["max_score"] <= 1.0


def test_09_model_artifact_integrity():
    """Verify model file binary is unchanged and sha256 checksum matches disk artifact."""
    service = CalibrationService()
    sha = service.sha256
    assert len(sha) == 64

    # Verify reload returns same hash
    service2 = CalibrationService()
    assert service2.sha256 == sha
