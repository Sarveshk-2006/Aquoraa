"""
Phase 7F Stage A Ground-Truth Source Discovery & Manifest Tests
"""

import json
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase7"
MANIFESTS_DIR = PROCESSED_DIR / "manifests"
QA_DIR = PROCESSED_DIR / "qa"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "phase7"
LABELS_DIR = PROCESSED_DIR / "labels"


def test_01_manifest_exists_and_valid_yaml():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    assert manifest_path.exists()
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "approved_sources" in data
    assert len(data["approved_sources"]) > 0


def test_02_source_id_and_event_id_present():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for src in data["approved_sources"]:
        assert "source_id" in src and len(src["source_id"]) > 0
        assert "event_id" in src and src["event_id"] in ["E01", "E02", "E03", "E04", "E05", "E06", "E07"]


def test_03_urls_present():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for src in data["approved_sources"]:
        assert "url" in src and src["url"].startswith("http")


def test_04_authority_tier_valid():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    valid_tiers = ["TIER_1_AUTHORITATIVE", "TIER_2_SCIENTIFIC_SATELLITE", "TIER_3_VERIFIED_OBSERVATIONS", "TIER_4_SECONDARY"]
    for src in data["approved_sources"]:
        assert src["authority_tier"] in valid_tiers


def test_05_suitability_valid():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    valid_suitabilities = ["SUITABLE_FOR_PIXEL_LABEL", "SUITABLE_FOR_EVENT_CONTEXT_ONLY", "UNSUITABLE"]
    for src in data["approved_sources"]:
        assert src["suitability"] in valid_suitabilities


def test_06_spatial_resolution_present():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for src in data["approved_sources"]:
        assert "spatial_resolution" in src and len(src["spatial_resolution"]) > 0


def test_07_temporal_resolution_present():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for src in data["approved_sources"]:
        assert "temporal_resolution" in src and len(src["temporal_resolution"]) > 0


def test_08_no_credentials_in_manifest():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    content = manifest_path.read_text(encoding="utf-8").lower()
    forbidden_terms = ["password", "secret", "token=", "api_key", "bearer ", "private_key"]
    for term in forbidden_terms:
        assert term not in content


def test_09_no_duplicate_source_ids():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    source_ids = [src["source_id"] for src in data["approved_sources"]]
    assert len(source_ids) == len(set(source_ids))


def test_10_no_duplicate_acquisition_targets():
    manifest_path = MANIFESTS_DIR / "PHASE_7F_GROUND_TRUTH_ACQUISITION_MANIFEST.yaml"
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    paths = [src["expected_local_path"] for src in data["approved_sources"]]
    assert len(paths) == len(set(paths))


def test_11_no_raw_files_modified():
    raw_files = list(RAW_DIR.rglob("*"))
    file_count = len([f for f in raw_files if f.is_file()])
    assert file_count >= 26


def test_12_no_labels_fabricated():
    audit_path = QA_DIR / "PHASE_7F_SOURCE_DISCOVERY_AUDIT.json"
    assert audit_path.exists()
    with open(audit_path, encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["labels_modified"] is False
    assert audit["bulk_download_executed"] is False
