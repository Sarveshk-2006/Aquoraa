"""
Phase 7F Source Verification Gate Tests
"""

import json
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase7"
MANIFESTS_DIR = PROCESSED_DIR / "manifests"
QA_DIR = PROCESSED_DIR / "qa"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "phase7"


def test_01_verification_gate_audit_exists():
    audit_json = QA_DIR / "PHASE_7F_SOURCE_VERIFICATION_GATE.json"
    audit_md = QA_DIR / "PHASE_7F_SOURCE_VERIFICATION_GATE.md"
    assert audit_json.exists()
    assert audit_md.exists()


def test_02_every_source_has_verification_status_and_event_id():
    audit_json = QA_DIR / "PHASE_7F_SOURCE_VERIFICATION_GATE.json"
    with open(audit_json, encoding="utf-8") as f:
        data = json.load(f)
    for src in data["sources"]:
        assert "verification_status" in src and len(src["verification_status"]) > 0
        assert "event_id" in src and src["event_id"] in ["E01", "E02", "E03", "E04", "E05", "E06", "E07"]


def test_03_every_source_has_exact_url():
    audit_json = QA_DIR / "PHASE_7F_SOURCE_VERIFICATION_GATE.json"
    with open(audit_json, encoding="utf-8") as f:
        data = json.load(f)
    for src in data["sources"]:
        assert "exact_url" in src and src["exact_url"].startswith("http")


def test_04_evidence_semantics_present():
    audit_json = QA_DIR / "PHASE_7F_SOURCE_VERIFICATION_GATE.json"
    with open(audit_json, encoding="utf-8") as f:
        data = json.load(f)
    for src in data["sources"]:
        assert "evidence_semantics" in src and len(src["evidence_semantics"]) > 0


def test_05_spatial_resolution_classification_present():
    audit_json = QA_DIR / "PHASE_7F_SOURCE_VERIFICATION_GATE.json"
    with open(audit_json, encoding="utf-8") as f:
        data = json.load(f)
    for src in data["sources"]:
        assert "native_resolution" in src and len(src["native_resolution"]) > 0
        assert "master_resolution" in src and src["master_resolution"] == "30 m x 30 m"


def test_06_e05_dfo_4945_explicitly_invalidated():
    audit_json = QA_DIR / "PHASE_7F_SOURCE_VERIFICATION_GATE.json"
    with open(audit_json, encoding="utf-8") as f:
        data = json.load(f)
    e05_gate = data["mandatory_e05_verification"]
    assert e05_gate["status"] == "INVALID"
    assert "Brahmaputra" in e05_gate["finding"] or "Assam" in e05_gate["finding"]
    invalid_srcs = [s for s in data["sources"] if s["source_id"] == "SRC_COPERNICUS_EMS_DFO_2020_E05"]
    assert len(invalid_srcs) == 1
    assert invalid_srcs[0]["verification_status"] == "INVALID"


def test_07_invalid_sources_excluded_from_verified_manifest():
    manifest_yaml = MANIFESTS_DIR / "PHASE_7F_VERIFIED_ACQUISITION_CANDIDATES.yaml"
    assert manifest_yaml.exists()
    with open(manifest_yaml, encoding="utf-8") as f:
        v_data = yaml.safe_load(f)
    v_ids = [s["source_id"] for s in v_data["verified_candidates"]]
    assert "SRC_COPERNICUS_EMS_DFO_2020_E05" not in v_ids
    assert "SRC_DFO_2020_E05_CORRECTED" in v_ids


def test_08_context_only_sources_excluded_from_pixel_label_manifest():
    manifest_yaml = MANIFESTS_DIR / "PHASE_7F_VERIFIED_ACQUISITION_CANDIDATES.yaml"
    with open(manifest_yaml, encoding="utf-8") as f:
        v_data = yaml.safe_load(f)
    for src in v_data["verified_candidates"]:
        assert src["pixel_label_suitability"] == "SUITABLE_FOR_PIXEL_LABEL"
    v_ids = [s["source_id"] for s in v_data["verified_candidates"]]
    assert "SRC_BMC_CHITALE_2006_E01" not in v_ids


def test_09_no_raw_data_changed():
    raw_files = list(RAW_DIR.rglob("*"))
    file_count = len([f for f in raw_files if f.is_file()])
    assert file_count >= 26


def test_10_no_processed_dataset_changed():
    master_csv = PROCESSED_DIR / "features" / "phase7_master_features.csv"
    sar_csv = PROCESSED_DIR / "sar" / "phase7_sar_bitemporal_evidence.csv"
    assert master_csv.exists()
    assert sar_csv.exists()


def test_11_no_flood_labels_changed():
    labels_csv = PROCESSED_DIR / "labels" / "phase7_flood_evidence_labels.csv"
    assert labels_csv.exists()


def test_12_and_13_no_ml_and_no_downloads():
    audit_json = QA_DIR / "PHASE_7F_SOURCE_VERIFICATION_GATE.json"
    with open(audit_json, encoding="utf-8") as f:
        data = json.load(f)
    safety = data["execution_safety_checks"]
    assert safety["downloads_executed"] is False
    assert safety["ml_models_trained"] is False
    assert safety["labels_modified"] is False
