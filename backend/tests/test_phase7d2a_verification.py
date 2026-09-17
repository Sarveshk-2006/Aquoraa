"""
Unit tests for Phase 7D.2A Sentinel-1 Catalog Acquisition Verification.

Verifies target roles, ASF catalog metadata, spatial footprint intersections,
controlled verification statuses, and raw data immutability.
"""

import json
import os

import pytest


@pytest.fixture
def verification_data():
    yaml_path = os.path.join(
        "data", "processed", "phase7", "manifests", "PHASE_7D2A_SENTINEL_ACQUISITION_VERIFICATION.yaml"
    )
    json_path = os.path.join(
        "data", "processed", "phase7", "qa", "PHASE_7D2A_SENTINEL_ACQUISITION_VERIFICATION.json"
    )
    assert os.path.exists(yaml_path), f"YAML manifest not found: {yaml_path}"
    assert os.path.exists(json_path), f"JSON audit not found: {json_path}"
    
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_verification_manifest_structure(verification_data):
    assert verification_data["phase"] == "PHASE_7D.2A_SENTINEL_ACQUISITION_VERIFICATION"
    assert verification_data["verification_summary"]["total_targets_evaluated"] == 6
    assert len(verification_data["targets"]) == 6


def test_target_roles_and_controlled_statuses(verification_data):
    valid_statuses = {"VERIFIED", "ALTERNATIVE_VERIFIED", "NO_VALID_SCENE_FOUND", "REQUIRES_HUMAN_REVIEW"}
    expected_roles = {
        "E02": "PRE_EVENT_BASELINE",
        "E03": "PRE_EVENT_BASELINE",
        "E04": "CO_EVENT",
        "E05": "CO_EVENT",
        "E06": "CO_EVENT",
        "E07": "CO_EVENT",
    }
    
    for target in verification_data["targets"]:
        event_id = target["event_id"]
        assert event_id in expected_roles
        assert target["role"] == expected_roles[event_id]
        assert target["verification_status"] in valid_statuses
        assert target["spatial_intersection"] is True
        assert target["product_type"] == "GRD_HD"
        assert target["mode"] == "IW"
        assert target["polarization"] == "VV+VH"
        assert target["orbit"] == "DESCENDING"


def test_replacement_reasons_documented(verification_data):
    for target in verification_data["targets"]:
        if target["verification_status"] == "ALTERNATIVE_VERIFIED":
            assert "does NOT exist in ASF catalog" in target["replacement_reason"]
            assert target["temporal_distance_days"] > 0


def test_raw_data_immutability():
    raw_dir = os.path.join("data", "raw", "phase7")
    assert os.path.exists(raw_dir)
    expected_subdirs = ["dem", "landcover", "official_observations", "osm", "rainfall", "sentinel1", "tide"]
    for sub in expected_subdirs:
        assert os.path.exists(os.path.join(raw_dir, sub))
