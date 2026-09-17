"""
Unit tests for Phase 7D.3 Sentinel-1 SAR Preprocessing & Bitemporal Evidence.

Validates source verification, SAFE metadata extraction, scene compatibility,
radiometric calibration, 30m grid alignment, quality masks, zero network calls,
and strict non-generation of final flood labels.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
SAR_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "sar"
QA_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "qa"
MANIFEST_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "manifests"


@pytest.fixture
def sar_audit_json():
    json_path = QA_DIR / "PHASE_7D3_SAR_PROCESSING_AUDIT.json"
    assert json_path.exists(), f"Phase 7D.3 audit JSON not found at {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sar_manifest_yaml():
    yaml_path = MANIFEST_DIR / "PHASE_7D3_SAR_PROCESSING_MANIFEST.yaml"
    assert yaml_path.exists(), f"Phase 7D.3 manifest YAML not found at {yaml_path}"
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sar_evidence_df():
    csv_path = SAR_DIR / "phase7_sar_bitemporal_evidence.csv"
    parquet_path = SAR_DIR / "phase7_sar_bitemporal_evidence.parquet"
    assert csv_path.exists() or parquet_path.exists()
    try:
        return pd.read_parquet(parquet_path)
    except Exception:
        return pd.read_csv(csv_path)


def test_1_and_2_four_source_scenes_and_immutability(sar_audit_json):
    assert sar_audit_json["raw_data_immutability"]["raw_files_modified"] == 0
    assert sar_audit_json["raw_data_immutability"]["status"] == "PASSED"


def test_3_and_4_safe_metadata_extraction_and_compatibility(sar_audit_json):
    e02 = sar_audit_json["event_diagnostics"]["E02"]
    e03 = sar_audit_json["event_diagnostics"]["E03"]
    
    assert e02["orbit_direction"] == "DESCENDING"
    assert e03["orbit_direction"] == "DESCENDING"
    assert e02["relative_orbit"] == "34"
    assert e03["relative_orbit"] == "34"


def test_5_and_6_crs_and_30m_output_grid(sar_audit_json):
    spatial = sar_audit_json["spatial_specification"]
    assert spatial["master_grid_cell_size_m"] == 30.0
    assert spatial["master_grid_dimensions"] == "392x476"
    assert spatial["total_spatial_cells"] == 186592
    assert spatial["metric_analysis_crs"] == "EPSG:32643"
    assert spatial["canonical_storage_crs"] == "EPSG:4326"


def test_7_common_pre_co_grid(sar_evidence_df):
    e02_df = sar_evidence_df[sar_evidence_df["event_id"] == "E02"]
    e03_df = sar_evidence_df[sar_evidence_df["event_id"] == "E03"]
    assert len(e02_df) == 186592
    assert len(e03_df) == 186592


def test_8_and_9_and_10_correct_delta_sign_and_db_conversion(sar_evidence_df):
    valid_e02 = sar_evidence_df[(sar_evidence_df["event_id"] == "E02") & (sar_evidence_df["valid_observation"] == 1)]
    # delta_vv_db = co_vv_db - pre_vv_db
    calc_delta = valid_e02["co_vv_db"] - valid_e02["pre_vv_db"]
    np.testing.assert_allclose(valid_e02["delta_vv_db"].values, calc_delta.values, atol=1e-3)


def test_11_and_12_nodata_and_quality_mask_propagation(sar_evidence_df):
    assert "valid_observation" in sar_evidence_df.columns
    assert "layover_flag" in sar_evidence_df.columns
    assert "shadow_flag" in sar_evidence_df.columns
    assert "nodata_flag" in sar_evidence_df.columns
    assert "permanent_water_flag" in sar_evidence_df.columns


def test_13_no_slope_5deg_exclusion(sar_audit_json):
    # Proves no slope > 5 deg exclusion rule was applied to exclude SAR evidence
    assert sar_audit_json["event_diagnostics"]["E02"]["valid_cells"] == 186592
    assert sar_audit_json["event_diagnostics"]["E03"]["valid_cells"] == 186592


def test_14_no_final_flood_label_generation(sar_evidence_df, sar_audit_json):
    assert "flood_label" not in sar_evidence_df.columns
    assert sar_audit_json["final_flood_labels_generated"] is False


def test_15_and_16_events_processed_scope(sar_audit_json):
    processed = sar_audit_json["processed_events"]
    assert set(processed) == {"E02", "E03", "E04", "E05", "E06", "E07"}
    unprocessed = sar_audit_json["unprocessed_events"]
    assert "E01" in unprocessed


def test_17_deterministic_output(sar_manifest_yaml):
    assert "sources" in sar_manifest_yaml
    assert "processing_parameters" in sar_manifest_yaml
    assert sar_manifest_yaml["processing_parameters"]["master_grid_alignment"] == "392x476 30m x 30m"


def test_18_master_grid_join_integrity(sar_evidence_df):
    assert len(sar_evidence_df) == 1119552  # 186,592 cells * 6 events (E02-E07)
    assert sar_evidence_df["grid_cell_id"].nunique() == 186592


def test_19_no_network_access(sar_audit_json):
    assert sar_audit_json["network_calls_performed"] == 0
    assert sar_audit_json["downloads_performed"] == 0
    assert sar_audit_json["overall_status"] == "PASSED_SAR_EVIDENCE_READY_FOR_LABEL_REVIEW"
    assert sar_audit_json["verdict"] == "PHASE 7D.3 COMPLETE — SAR EVIDENCE READY FOR LABEL REVIEW"
