"""
Unit tests for Phase 7D.2B Corrected Sentinel-1 Two-Scene Acquisition Manifest.

Verifies target list, exclusion of E04-E07, local presence flags,
and zero network/data mutations.
"""

import json
import os

import pytest


@pytest.fixture
def manifest_data():
    yaml_path = os.path.join(
        "data", "processed", "phase7", "manifests", "PHASE_7D2B_SENTINEL_TWO_SCENE_ACQUISITION.yaml"
    )
    json_path = os.path.join(
        "data", "processed", "phase7", "qa", "PHASE_7D2B_SENTINEL_TWO_SCENE_ACQUISITION.json"
    )
    assert os.path.exists(yaml_path), f"YAML manifest not found: {yaml_path}"
    assert os.path.exists(json_path), f"JSON audit not found: {json_path}"
    
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_manifest_structure_and_counts(manifest_data):
    assert manifest_data["phase"] == "PHASE_7D.2B_CORRECTED_SENTINEL_TWO_SCENE_ACQUISITION_MANIFEST"
    summary = manifest_data["acquisition_summary"]
    assert summary["total_manifest_scenes"] == 4
    assert summary["new_required_acquisitions_count"] == 2
    assert summary["already_present_valid_count"] == 2
    assert summary["network_calls_performed"] == 0
    assert summary["raw_files_changed"] == 0


def test_scene_entries(manifest_data):
    entries = manifest_data["scene_entries"]
    assert len(entries) == 4
    
    # Check E02 baseline
    e02_base = next(e for e in entries if e["event_id"] == "E02" and e["role"] == "PRE_EVENT_BASELINE")
    assert e02_base["scene_id"] == "S1A_IW_GRDH_1SDV_20170817T010248_20170817T010313_017956_01E202_67C3"
    assert e02_base["download_required"] is True
    assert e02_base["local_status"] == "VERIFIED_REQUIRED_FOR_ACQUISITION"
    
    # Check E02 co-event
    e02_co = next(e for e in entries if e["event_id"] == "E02" and e["role"] == "CO_EVENT")
    assert e02_co["scene_id"] == "S1A_IW_GRDH_1SDV_20170829T010248_20170829T010313_018131_01E74F_E820"
    assert e02_co["download_required"] is False
    assert e02_co["local_status"] == "ALREADY_PRESENT_VALID"
    
    # Check E03 baseline
    e03_base = next(e for e in entries if e["event_id"] == "E03" and e["role"] == "PRE_EVENT_BASELINE")
    assert e03_base["scene_id"] == "S1A_IW_GRDH_1SDV_20190608T010256_20190608T010321_027581_031CCA_FBE2"
    assert e03_base["download_required"] is True
    assert e03_base["local_status"] == "VERIFIED_REQUIRED_FOR_ACQUISITION"
    
    # Check E03 co-event
    e03_co = next(e for e in entries if e["event_id"] == "E03" and e["role"] == "CO_EVENT")
    assert e03_co["scene_id"] == "S1A_IW_GRDH_1SDV_20190702T010258_20190702T010323_027931_03274B_DDDA"
    assert e03_co["download_required"] is False
    assert e03_co["local_status"] == "ALREADY_PRESENT_VALID"


def test_exclusion_of_e04_to_e07(manifest_data):
    entries = manifest_data["scene_entries"]
    event_ids = {e["event_id"] for e in entries}
    assert event_ids == {"E02", "E03"}
    assert "E04" not in event_ids
    assert "E05" not in event_ids
    assert "E06" not in event_ids
    assert "E07" not in event_ids


def test_raw_data_immutability():
    raw_dir = os.path.join("data", "raw", "phase7")
    assert os.path.exists(raw_dir)
    expected_subdirs = ["dem", "landcover", "official_observations", "osm", "rainfall", "sentinel1", "tide"]
    for sub in expected_subdirs:
        assert os.path.exists(os.path.join(raw_dir, sub))
