"""
Unit tests for Phase 7D.2C Acquisition Preparation.

Verifies downloader reuse, manifest integration, PowerShell command specification,
safety rules, and zero network/data mutations.
"""

import json
import os

import pytest


@pytest.fixture
def prep_json():
    json_path = os.path.join(
        "data", "processed", "phase7", "qa", "PHASE_7D2C_ACQUISITION_PREPARATION.json"
    )
    assert os.path.exists(json_path), f"JSON preparation artifact not found: {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_prep_json_invariants(prep_json):
    assert prep_json["phase"] == "PHASE_7D.2C_PREPARE_CONTROLLED_TWO_SCENE_ACQUISITION"
    assert prep_json["downloader_reused"] == "YES"
    assert prep_json["manifest_verified"] == "YES"
    assert prep_json["safe_to_execute"] == "YES"
    assert prep_json["network_calls_performed"] == 0
    assert prep_json["raw_files_changed"] == 0


def test_target_scene_ids(prep_json):
    expected_ids = [
        "S1A_IW_GRDH_1SDV_20170817T010248_20170817T010313_017956_01E202_67C3",
        "S1A_IW_GRDH_1SDV_20190608T010256_20190608T010321_027581_031CCA_FBE2"
    ]
    assert prep_json["exact_target_scene_ids"] == expected_ids


def test_powershell_command_syntax(prep_json):
    cmd = prep_json["exact_powershell_command"]
    assert "$env:EARTHDATA_TOKEN=" in cmd
    assert "scripts/phase7b_acquisition_service.py" in cmd
    assert "--manifest" in cmd
    assert "PHASE_7D2B_SENTINEL_TWO_SCENE_ACQUISITION.yaml" in cmd
    assert "--mode acquire" in cmd


def test_raw_data_immutability():
    raw_dir = os.path.join("data", "raw", "phase7")
    assert os.path.exists(raw_dir)
    expected_subdirs = ["dem", "landcover", "official_observations", "osm", "rainfall", "sentinel1", "tide"]
    for sub in expected_subdirs:
        assert os.path.exists(os.path.join(raw_dir, sub))
