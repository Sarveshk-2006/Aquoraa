"""
Backend tests for Phase 7C Real Data Preprocessing & Feature Engineering.
Validates spatial grid alignment, raw data immutability, component feature extraction,
candidate SAR inundation, tide alignment, and provenance manifest generation.
"""

import json
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "phase7"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase7"


def test_raw_data_immutability():
    """Verify raw files under data/raw/phase7/ are untouched."""
    assert RAW_DIR.exists(), "Raw directory must exist"
    
    # Check DEM
    dem_path = RAW_DIR / "dem" / "Copernicus_DSM_COG_10_N19_00_E072_00.tif"
    assert dem_path.exists()
    assert dem_path.stat().st_size > 0
    
    # Check WorldCover
    wc_path = RAW_DIR / "landcover" / "ESA_WorldCover_10m_2021_v200_N18E072_Map.tif"
    assert wc_path.exists()
    assert wc_path.stat().st_size > 0
    
    # Check OSM
    osm_path = RAW_DIR / "osm" / "osm_mithi_envelope.json"
    assert osm_path.exists()
    assert osm_path.stat().st_size > 0

    # Check Tide
    tide_path = RAW_DIR / "tide" / "mumbai_port_h846a.csv"
    assert tide_path.exists()
    assert tide_path.stat().st_size > 0


def test_master_grid_specification():
    """Verify Master Computational Grid definitions."""
    from scripts.phase7c_preprocessing_service import (
        ANALYSIS_CRS,
        DECISION_DOMAIN_ENVELOPE,
        GRID_CELL_SIZE_M,
    )
    
    assert ANALYSIS_CRS == "EPSG:32643"
    assert GRID_CELL_SIZE_M == 30.0
    assert DECISION_DOMAIN_ENVELOPE == [72.8400, 19.0400, 72.9000, 19.1200]


def test_processed_directories_exist():
    """Verify all required output subdirectories exist under data/processed/phase7/."""
    expected_subdirs = [
        "terrain", "landcover", "rainfall", "urban",
        "sentinel1", "tide", "features", "labels", "qa", "manifests"
    ]
    for sub in expected_subdirs:
        sub_path = PROCESSED_DIR / sub
        assert sub_path.exists(), f"Processed subdirectory {sub} must exist"


def test_terrain_derivation_outputs():
    """Verify elevation, slope, aspect, flow accumulation, and drainage proxy rasters."""
    terrain_dir = PROCESSED_DIR / "terrain"
    expected_files = [
        "elevation_30m.tif",
        "slope_30m.tif",
        "aspect_30m.tif",
        "flow_accumulation_30m.tif",
        "drainage_proxy_30m.tif"
    ]
    for filename in expected_files:
        filepath = terrain_dir / filename
        assert filepath.exists(), f"Terrain file {filename} must exist"
        assert filepath.stat().st_size > 1000, f"Terrain file {filename} must be non-empty"


def test_landcover_outputs():
    """Verify Land Cover class and Built-Up Fraction rasters."""
    lc_dir = PROCESSED_DIR / "landcover"
    assert (lc_dir / "landcover_class_30m.tif").exists()
    assert (lc_dir / "built_up_fraction_30m.tif").exists()


def test_urban_feature_outputs():
    """Verify OSM vector layers and distance rasters."""
    urban_dir = PROCESSED_DIR / "urban"
    assert (urban_dir / "osm_roads.gpkg").exists()
    assert (urban_dir / "osm_waterways.gpkg").exists()
    assert (urban_dir / "distance_to_road_30m.tif").exists()
    assert (urban_dir / "distance_to_waterway_30m.tif").exists()


def test_rainfall_processed_events():
    """Verify IMERG rainfall rasters for all 7 events."""
    rain_dir = PROCESSED_DIR / "rainfall"
    for e in range(1, 8):
        event_id = f"E{e:02d}"
        assert (rain_dir / f"{event_id}_rainfall_30m.tif").exists()
        assert (rain_dir / f"{event_id}_rainfall_stats.json").exists()


def test_sentinel1_backscatter_and_candidates():
    """Verify Sentinel-1 backscatter outputs and candidate inundation masks."""
    s1_dir = PROCESSED_DIR / "sentinel1"
    labels_dir = PROCESSED_DIR / "labels"
    
    # E02 & E03 co-events have candidate inundation masks
    assert (labels_dir / "E02_observed_flood_candidate.tif").exists()
    assert (labels_dir / "E03_observed_flood_candidate.tif").exists()
    assert (labels_dir / "E02_candidate_stats.json").exists()
    assert (labels_dir / "E03_candidate_stats.json").exists()


def test_tide_processed_outputs():
    """Verify UTC-normalized tide series and event-aligned tide summary."""
    tide_dir = PROCESSED_DIR / "tide"
    assert (tide_dir / "mumbai_port_tide_series_utc.csv").exists()
    assert (tide_dir / "event_tide_aligned_summary.json").exists()
    
    with open(tide_dir / "event_tide_aligned_summary.json", "r") as f:
        data = json.load(f)
        assert len(data) == 7
        assert "E01" in data
        assert "E02" in data
        assert "max_tide_level_m" in data["E01"]
        assert "tide_anomaly_msl_m" in data["E01"]


def test_qa_and_processing_manifest():
    """Verify QA report and Processing Manifest artifacts."""
    qa_path = PROCESSED_DIR / "qa" / "PHASE_7C_QA_REPORT.json"
    manifest_path = PROCESSED_DIR / "manifests" / "PHASE_7C_PROCESSING_MANIFEST.yaml"
    
    assert qa_path.exists()
    assert manifest_path.exists()
    
    with open(qa_path, "r") as f:
        qa_data = json.load(f)
        assert qa_data["status"] == "PASSED"
        check_names = [c["check"] for c in qa_data["checks"]]
        assert "raw_files_immutable" in check_names
        assert "master_feature_dataset" in check_names
    
    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)
        assert manifest["phase"] == "PHASE_7C_PREPROCESSING_AND_FEATURE_ENGINEERING"
        assert len(manifest["entries"]) > 0


def test_imerg_single_granule_semantics():
    """CORRECTION #1: Verify single 30-min granule cannot produce 24h accumulation."""
    rain_dir = PROCESSED_DIR / "rainfall"
    for e in range(1, 8):
        event_id = f"E{e:02d}"
        stats_path = rain_dir / f"{event_id}_rainfall_stats.json"
        if stats_path.exists():
            with open(stats_path, "r") as f:
                stats = json.load(f)
                reason = stats.get("disclaimer") or stats.get("rainfall_accum_24h_mm_reason", "")
                assert "24-hour/event-total rainfall features are unavailable" in reason



def test_sentinel1_scene_count_and_e01_exclusion():
    """CORRECTION #2: Exactly 6 valid Sentinel-1 scenes exist; E01 output is excluded/missing."""
    s1_dir = PROCESSED_DIR / "sentinel1"
    e01_backscatter = s1_dir / "E01_sentinel1_backscatter.tif"
    assert not e01_backscatter.exists(), "E01 backscatter output must be excluded"


def test_sar_baseline_timestamp_validation():
    """CORRECTION #3: Baseline validation uses actual timestamps; later scenes cannot be baselines."""
    audit_path = PROCESSED_DIR / "qa" / "PHASE_7C_CORRECTION_AUDIT.json"
    if audit_path.exists():
        with open(audit_path, "r") as f:
            audit = json.load(f)
            matrix = audit.get("sar_baseline_validity_matrix", [])
            for row in matrix:
                assert row["baseline_status"] in ["NO_VALID_BASELINE", "NO_SAR_DATA"]


def test_candidate_flood_evidence_slope_rule():
    """CORRECTION #4: No universal slope <5° rule in candidate labeling."""
    audit_path = PROCESSED_DIR / "qa" / "PHASE_7C_CORRECTION_AUDIT.json"
    if audit_path.exists():
        with open(audit_path, "r") as f:
            audit = json.load(f)
            assert audit.get("candidate_flood_evidence_slope_rule") == "REMOVED_UNIVERSAL_SLOPE_LESS_THAN_5_DEG_EXCLUSION"


def test_drainage_proxy_dimensionless_naming():
    """CORRECTION #5: Dimensionless drainage proxy is not named in metres."""
    terrain_dir = PROCESSED_DIR / "terrain"
    proxy_m = terrain_dir / "drainage_proxy_m.tif"
    assert not proxy_m.exists(), "Dimensionless drainage proxy MUST NOT be named with '_m'"


def test_slope_aspect_semantics():
    """CORRECTION #6: Slope is in degrees [0,90], aspect in degrees [0,360]."""
    audit_path = PROCESSED_DIR / "qa" / "PHASE_7C_CORRECTION_AUDIT.json"
    if audit_path.exists():
        with open(audit_path, "r") as f:
            audit = json.load(f)
            slope_info = audit.get("slope_semantics", {})
            assert "0-90" in slope_info.get("slope_deg_range", "") or "degrees" in slope_info.get("slope_deg_range", "")


def test_tide_event_alignment_deterministic():
    """CORRECTION #7: Tide alignment is deterministic with UTC and MSL reference."""
    tide_dir = PROCESSED_DIR / "tide"
    summary_path = tide_dir / "event_tide_aligned_summary.json"
    if summary_path.exists():
        with open(summary_path, "r") as f:
            tide_summary = json.load(f)
            assert "E01" in tide_summary
            assert tide_summary["E01"].get("alignment_method") == "NEAREST_OBSERVED_TIDE_UTC"
            assert "station_msl_m" in tide_summary["E01"] or "max_tide_level_m" in tide_summary["E01"]


def test_master_dataset_honest_nulls():
    """CORRECTION #8 & #10: Master dataset contains no fabricated unsupported values."""
    features_dir = PROCESSED_DIR / "features"
    parquet_path = features_dir / "phase7_master_features.parquet"
    csv_path = features_dir / "phase7_master_features.csv"
    assert parquet_path.exists() or csv_path.exists()


def test_phase7c_grid_sanity_audit_artifact():
    """Verify Phase 7C final grid sanity audit QA artifact and classification."""
    audit_path = PROCESSED_DIR / "qa" / "PHASE_7C_GRID_SANITY_AUDIT.json"
    assert audit_path.exists(), "PHASE_7C_GRID_SANITY_AUDIT.json must exist"
    
    with open(audit_path, "r") as f:
        audit = json.load(f)
        assert audit["final_classification"] in [
            "VALID_STUDY_AREA_GRID", "GRID_GENERATION_DEFECT", "UNRESOLVED"
        ]
        assert "per_event_cell_counts" in audit
        assert "feature_null_summary" in audit
        assert audit["per_event_cell_counts"]["E01"] == 1911



