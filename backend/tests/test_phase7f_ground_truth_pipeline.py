"""
Unit and integration tests for Phase 7F Ground-Truth Acquisition and Validated Flood Label Dataset.
"""

import json
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "processed" / "phase7" / "manifests" / "PHASE_7F_VERIFIED_ACQUISITION_CANDIDATES.yaml"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "phase7" / "ground_truth"
PROVENANCE_PATH = OUTPUT_DIR / "PHASE_7F_GROUND_TRUTH_PROVENANCE.json"
AUDIT_JSON_PATH = PROJECT_ROOT / "data" / "processed" / "phase7" / "qa" / "PHASE_7F_GROUND_TRUTH_AUDIT.json"
AUDIT_MD_PATH = PROJECT_ROOT / "data" / "processed" / "phase7" / "qa" / "PHASE_7F_GROUND_TRUTH_AUDIT.md"
MASTER_GRID_PATH = PROJECT_ROOT / "data" / "processed" / "phase7" / "phase7_master_features.parquet"
MASTER_GRID_CSV = PROJECT_ROOT / "data" / "processed" / "phase7" / "phase7_master_features.csv"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "phase7" / "ground_truth"


def test_01_acquisition_manifest_integrity():
    """Verify acquisition manifest exists, is valid YAML, and contains mandatory fields."""
    assert MANIFEST_PATH.exists(), f"Manifest missing at {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    assert "verified_candidates" in data or "candidates" in data
    candidates = data.get("verified_candidates") or data.get("candidates")
    assert len(candidates) >= 6, "Expected candidates for E02..E07"
    for cand in candidates:
        assert "source_id" in cand
        assert "event_id" in cand
        assert "authority_tier" in cand or "source_authority" in cand


def test_02_e05_4963_identity_and_rejection_of_4945():
    """Verify E05 candidate points strictly to DFO #4963 and rejects DFO #4945."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    candidates = data.get("verified_candidates") or data.get("candidates")
    e05_cands = [c for c in candidates if c.get("event_id") == "E05"]
    assert len(e05_cands) == 1
    e05 = e05_cands[0]
    
    assert e05.get("dfo_event_id") == 4963 or "4963" in e05.get("title", "") or "4963" in e05.get("source_id", "")
    assert "4945" not in str(e05)
    assert "4963" in str(e05)


def test_03_payload_integrity_and_raw_immutability():
    """Verify all raw downloaded payloads exist under data/raw/phase7/ground_truth/ and are non-empty."""
    assert RAW_DIR.exists()
    payload_files = list(RAW_DIR.glob("*"))
    assert len(payload_files) >= 6, "Expected at least 6 raw source payload files"
    for pf in payload_files:
        assert pf.stat().st_size > 0, f"Payload file {pf} is empty"


def _load_df():
    parquet_out = OUTPUT_DIR / "phase7_validated_flood_labels.parquet"
    csv_out = OUTPUT_DIR / "phase7_validated_flood_labels.csv"
    if parquet_out.exists():
        try:
            return pd.read_parquet(parquet_out)
        except (FileNotFoundError, ValueError, OSError, RuntimeError, ImportError):
            pass
    return pd.read_csv(csv_out, low_memory=False)


def test_04_master_grid_cardinality_and_key_uniqueness():
    """Verify final validated label dataset matches master grid (1,306,144 rows, unique event_id + grid_cell_id)."""
    df = _load_df()
        
    assert len(df) == 1306144, f"Expected 1,306,144 rows, got {len(df)}"
    assert df["event_id"].nunique() == 7, "Expected all 7 events E01-E07"
    
    # Check cell count per event
    cells_per_event = df.groupby("event_id")["grid_cell_id"].nunique()
    for eid, count in cells_per_event.items():
        assert count == 186592, f"Event {eid} has {count} cells instead of 186,592"
        
    # Check composite key uniqueness
    dups = df.duplicated(subset=["event_id", "grid_cell_id"]).sum()
    assert dups == 0, f"Found {dups} duplicate event_id + grid_cell_id pairs"


def test_05_e01_benchmark_only_handling():
    """Verify E01 maintains 100% UNKNOWN (flood_label = -1) and status BENCHMARK_ONLY."""
    df = _load_df()
    e01_df = df[df["event_id"] == "E01"]
    
    assert len(e01_df) == 186592
    assert (e01_df["flood_label"] == -1).all(), "E01 must have all flood_label = -1"
    assert (e01_df["label_status"] == "BENCHMARK_ONLY").all()


def test_06_permanent_water_behavior():
    """Verify permanent water (class 80) cells are flagged permanent_water=1 and flood_label=-1 unless event inundated."""
    df = _load_df()
    
    pw_df = df[df["permanent_water"] == 1]
    assert len(pw_df) > 0, "Expected permanent water cells in dataset"
    
    # Permanent water without specific positive evidence should be UNKNOWN (-1), never 0 (non-flood)
    pw_non_flood = pw_df[pw_df["flood_label"] == 0]
    assert len(pw_non_flood) == 0, "Permanent water should never be classified as 0 (non-flood)"


def test_07_unknown_preservation_and_no_automatic_negative_labels():
    """Verify non-reported / uncorroborated cells remain UNKNOWN (-1) and are not converted to 0."""
    df = _load_df()
    
    unknown_count = (df["flood_label"] == -1).sum()
    pct_unknown = (unknown_count / len(df)) * 100
    
    assert pct_unknown > 90.0, f"Expected majority UNKNOWN labels, got {pct_unknown:.2f}%"
    
    # Verify no arbitrary negative labels were generated without evidence
    zeros_df = df[df["flood_label"] == 0]
    assert len(zeros_df) == 0, "No evidence supports automatic negative labels in current acquisition"


def test_08_positive_label_spatial_mapping():
    """Verify positive labels exist for E02..E07 from verified sources."""
    df = _load_df()
    
    pos_df = df[df["flood_label"] == 1]
    assert len(pos_df) > 0, "Expected positive flood labels from ground truth acquisition"
    
    events_with_pos = pos_df["event_id"].unique()
    for eid in ["E02", "E03", "E04", "E05", "E06", "E07"]:
        assert eid in events_with_pos, f"Event {eid} should have positive ground truth labels"


def test_09_source_resolution_preservation():
    """Verify source native resolution metadata is strictly preserved (50m for E04/E07, 250m for E05, etc.)."""
    df = _load_df()
    
    e04_res = df[df["event_id"] == "E04"]["source_native_resolution_m"].unique()
    assert 50.0 in e04_res, f"E04 native resolution should preserve 50m, found {e04_res}"
    
    e05_res = df[df["event_id"] == "E05"]["source_native_resolution_m"].unique()
    assert 250.0 in e05_res, f"E05 native resolution should preserve 250m, found {e05_res}"


def test_10_provenance_and_audit_generation():
    """Verify provenance JSON and audit JSON/MD files exist and are well-formed."""
    assert PROVENANCE_PATH.exists()
    assert AUDIT_JSON_PATH.exists()
    assert AUDIT_MD_PATH.exists()
    
    with open(PROVENANCE_PATH, "r", encoding="utf-8") as f:
        prov = json.load(f)
    assert "7F" in prov["phase"]
    assert prov["e05_dfo_correction"]["verified_replacement_used"] == "DFO Event #4963 (Western India & Mumbai Monsoon Flood, 5-7 Aug 2020)"
    
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["total_rows"] == 1306144
    assert audit["overall_label_distribution"]["flood_1"] == 19595
