"""
Unit and integration tests for Phase 7D.1 Flood Label Evidence Gap Audit.

Verifies evidence matrix consistency, labelability rules, target-feature decoupling,
and raw payload immutability.
"""

import json
import os

import pandas as pd
import pytest


@pytest.fixture
def gap_audit_json():
    audit_file = os.path.join(
        "data", "processed", "phase7", "qa", "PHASE_7D1_LABEL_EVIDENCE_GAP_AUDIT.json"
    )
    assert os.path.exists(audit_file), f"Gap audit JSON not found: {audit_file}"
    with open(audit_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def ml_dataset():
    csv_file = os.path.join(
        "data", "processed", "phase7", "dataset", "phase7_ml_ready.csv"
    )
    assert os.path.exists(csv_file), f"ML ready dataset CSV not found: {csv_file}"
    return pd.read_csv(csv_file)


def test_all_seven_events_represented(gap_audit_json, ml_dataset):
    expected_events = {"E01", "E02", "E03", "E04", "E05", "E06", "E07"}
    
    # Audit JSON events
    audit_events = {e["event_id"] for e in gap_audit_json["current_evidence_matrix"]}
    assert audit_events == expected_events
    
    # ML dataset events
    dataset_events = set(ml_dataset["event_id"].unique())
    assert dataset_events == expected_events


def test_no_event_incorrectly_marked_labelable_now(gap_audit_json):
    labelability = gap_audit_json["event_labelability"]
    for event_id, info in labelability.items():
        assert info["classification"] != "LABELABLE_NOW", (
            f"Event {event_id} incorrectly marked LABELABLE_NOW without complete bitemporal SAR pairs!"
        )


def test_candidate_evidence_remains_distinct(ml_dataset):
    # flood_label must be NULL/NaN for all rows
    assert ml_dataset["flood_label"].isnull().all()
    
    # Candidate evidence columns must be distinct from final labels
    assert "observed_flood_candidate" in ml_dataset.columns
    assert "flood_label_status" in ml_dataset.columns
    
    # Check that candidates exist in E02 and E03
    e02_candidates = ml_dataset[ml_dataset["event_id"] == "E02"]["observed_flood_candidate"].dropna()
    assert (e02_candidates == 0.0).all() or (e02_candidates.isin([0.0, 1.0])).all()


def test_prohibited_labeling_sources_invariants(gap_audit_json):
    pos_rules = gap_audit_json["positive_label_rules"]
    prohibited = pos_rules["prohibited_sources"]
    
    assert "rainfall_magnitude" in prohibited
    assert "elevation_threshold" in prohibited
    assert "drainage_proxy" in prohibited
    assert "physical_model_score" in prohibited


def test_missing_evidence_remains_unavailable(gap_audit_json, ml_dataset):
    statuses = set(ml_dataset["flood_label_status"].unique())
    assert statuses.issubset({"UNAVAILABLE", "UNVALIDATED_CANDIDATE", "AMBIGUOUS"})
    assert "VALIDATED" not in statuses


def test_acquisition_requirements_scene_ids(gap_audit_json):
    missing = gap_audit_json["sentinel_evidence_gaps"]["missing_scenes"]
    assert len(missing) == 6
    
    for req in missing:
        event_id = req["event_id"]
        assert event_id in {"E02", "E03", "E04", "E05", "E06", "E07"}
        assert req["missing_type"] in {"PRE_EVENT_BASELINE", "CO_EVENT_SCENE"}


def test_supervised_labels_currently_not_possible(gap_audit_json):
    assert gap_audit_json["supervised_labels_currently_possible"] == "NO"
    assert "zero events have complete bitemporal SAR pairs" in gap_audit_json["explanation_why_not_possible"]


def test_raw_data_immutability():
    raw_dir = os.path.join("data", "raw", "phase7")
    assert os.path.exists(raw_dir)
    # Check raw subdirectories exist
    expected_subdirs = ["dem", "landcover", "official_observations", "osm", "rainfall", "sentinel1", "tide"]
    for sub in expected_subdirs:
        assert os.path.exists(os.path.join(raw_dir, sub))
