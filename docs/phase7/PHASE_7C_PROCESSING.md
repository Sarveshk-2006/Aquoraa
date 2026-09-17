# Phase 7C — Real Data Preprocessing & Feature Engineering (Corrected & Audited Pass)

## Overview & Scientific Integrity Audit Summary

Phase 7C implements local, deterministic data processing and spatial-temporal feature engineering for the Mithi River urban catchment in Mumbai, Maharashtra, India. Following a comprehensive scientific integrity audit, all 10 data-integrity corrections have been strictly applied:

1. **IMERG Temporal Coverage**: Enforced single 30-minute granule semantics per event. Unsupported `rainfall_accum_24h_mm` features are set to explicit `NaN` / `NULL` with a provenance disclaimer.
2. **Sentinel-1 Source -> Output Audit**: Confirmed exactly 6 valid Sentinel-1 scenes exist (E02–E07). Spurious/unsupported E01 SAR outputs have been removed and set to `NaN`.
3. **SAR Temporal Baseline Validity**: Timestamps established that E04–E07 (2019–2021) postdate E02 (2017) and E03 (July 2019). No valid pre-event baseline exists (`NO_VALID_BASELINE`), so SAR change detection is marked `UNAVAILABLE` (`NaN`).
4. **Removal of Fixed <5° Slope Exclusion**: Removed universal `<5°` slope cutoff on candidate inundation masks. Candidate evidence is saved strictly as `OBSERVED_FLOOD_CANDIDATE` (never `FINAL_FLOOD_LABEL`).
5. **Drainage Proxy Reconciliation**: Renamed dimensionless heuristic from `drainage_proxy_m` to `drainage_proxy_score` (removed `_m` unit label).
6. **Slope & Aspect Semantics**: `slope_deg` represents terrain slope angle in degrees [0, 90°]; `aspect_deg` represents orientation in compass degrees [0, 360°].
7. **Tide Event Alignment**: Normalized UHSLC Mumbai Port hourly tide series to UTC ISO-8601 and calculated anomalies relative to station mean MSL (1.42 m).
8. **Master Dataset Integrity**: Consolidated 13,377 grid rows across 7 events in `phase7_master_features.parquet` and `phase7_master_features.csv` with honest `NaN` values for unsupported features.
9. **Source-Native Resolution Provenance**: Preserved explicit native vs master 30m grid resolution mapping.
10. **Raw Immutability Verification**: Cryptographic SHA-256 hashes confirm 100% immutability of all files under `data/raw/phase7/`.

---

## 1. Master Computational Grid & Coordinate Reference Systems

### Coordinate Systems
- **Canonical Stored Vector CRS**: EPSG:4326 (WGS84 Geographic)
- **Web Display CRS**: EPSG:3857 (Web Mercator)
- **Authoritative Analysis CRS**: `EPSG:32643` (UTM Zone 43N, meters)

### Master Grid Definition
- **Resolution**: 30.0 meters x 30.0 meters
- **Bounding Box (EPSG:4326)**:
  - Min Longitude: `72.82° E`
  - Max Longitude: `72.93° E`
  - Min Latitude: `19.03° N`
  - Max Latitude: `19.16° N`
- **Grid Dimensions**: `386` rows x `481` columns (`1,911` decision domain cells per event).

---

## 2. Multi-Source Native Resolutions & Resampling Provenance

| Dataset Source | Source Native Resolution | Temporal Resolution | Resampling Method | Nodata / Unsupported Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Copernicus DEM** | ~30 m (1 arcsec) | Static (2021) | Bilinear | Explicit NaN / -9999 |
| **ESA WorldCover** | 10 m | Static (2021) | Nearest Neighbor / Built Fraction | 0 (Unclassified) |
| **OpenStreetMap** | Vector / Native | Dynamic / Static | Euclidean Distance (m) | 0.0 m |
| **NASA IMERG (HDF5/NetCDF)** | 0.1° (~10 km) | 30-minute | Bilinear to 30m Grid | Single Granule Only; 24h Accum = NaN |
| **Sentinel-1 GRD** | 10 m x 10 m pixel spacing | Scene timestamps | Bilinear | E01 = NaN; Change dB = NaN (No Baseline) |
| **UHSLC Tide** | Station point | Hourly | Nearest UTC | MSL 1.42 m Anomaly |

---

## 3. Component Data Processing Pipelines

### Terrain Processing (`data/processed/phase7/terrain/`)
- **Elevation**: Resampled Copernicus DEM to EPSG:32643 30 m grid (`elevation_30m.tif`).
- **Slope & Aspect**: Computed `slope_deg` [0, 90°] and `aspect_deg` [0, 360°].
- **Flow Accumulation**: Single D8 flow direction and accumulation (`flow_accumulation_30m.tif`).
- **Drainage Proxy Score**: Reused Phase 4 dimensionless heuristic: `drainage_proxy_score = log1p(FlowAcc) / (Slope + 1.0)` (`drainage_proxy_30m.tif`).

### Land Cover Processing (`data/processed/phase7/landcover/`)
- **Land Cover Class**: ESA WorldCover 2021 class values mapped to 30 m grid (`landcover_class_30m.tif`).
- **Built-Up Fraction**: ESA WorldCover class 50 (Built-up) aggregated into 30 m cell area coverage fractions `[0.0, 1.0]` (`built_up_fraction_30m.tif`).

### OSM Urban Infrastructure Processing (`data/processed/phase7/urban/`)
- Parsed 463,132 OSM elements into road and waterway spatial masks.
- Computed continuous Euclidean distance (in meters) to nearest mapped road (`distance_to_road_30m.tif`) and waterway (`distance_to_waterway_30m.tif`) via `scipy.ndimage.distance_transform_edt`.

### Rainfall Processing (`data/processed/phase7/rainfall/`)
- Extracted 30-minute IMERG precipitation rate (`precipitationCal` / `precipitation`) for events E01 through E07.
- **Single Granule Semantics**: Set `rainfall_accum_24h_mm = NaN` with explicit provenance disclaimer: *"24-hour/event-total rainfall features are unavailable where the acquired IMERG temporal coverage does not span the required window."*

### Sentinel-1 SAR Processing & Inundation Candidates (`data/processed/phase7/sentinel1/`, `data/processed/phase7/labels/`)
- Processed 6 valid Sentinel-1 GRD scenes (E02–E07). Excluded spurious E01 backscatter output.
- **SAR Baseline Validity**: Determined that no valid pre-event baselines exist (`NO_VALID_BASELINE`), so SAR change detection is `UNAVAILABLE` (`NaN`).
- **Candidate Inundation (`OBSERVED_FLOOD_CANDIDATE`)**: Identified low VV backscatter candidate pixels over non-permanent water areas without applying a universal `<5°` slope exclusion.

### UHSLC Tide Processing (`data/processed/phase7/tide/`)
- Processed 302,481 hourly tide records from UHSLC Mumbai Port station (1985–2023).
- Normalized timestamps to UTC ISO-8601 and derived tide anomaly relative to mean MSL (1.42 m).

---

## 4. Master Parquet Feature Dataset (`data/processed/phase7/features/`)

- **Master Parquet & CSV**: `phase7_master_features.parquet`, `phase7_master_features.csv`
- **Individual Event CSVs**: `event_E01_features.csv` ... `event_E07_features.csv`
- **Total Dataset Rows**: `13,377` rows (1,911 spatial grid cells x 7 severe flood events).

---

## 5. Artifact Audit Verification

- **QA Report**: [`PHASE_7C_QA_REPORT.json`](file:///c:/Users/thaka/OneDrive/Desktop/Hackathon/NextStep%20Hacks/data/processed/phase7/qa/PHASE_7C_QA_REPORT.json) (`status: PASSED`)
- **Correction Audit**: [`PHASE_7C_CORRECTION_AUDIT.json`](file:///c:/Users/thaka/OneDrive/Desktop/Hackathon/NextStep%20Hacks/data/processed/phase7/qa/PHASE_7C_CORRECTION_AUDIT.json) (`status: PASSED_WITH_CORRECTIONS`)
- **Processing Manifest**: [`PHASE_7C_PROCESSING_MANIFEST.yaml`](file:///c:/Users/thaka/OneDrive/Desktop/Hackathon/NextStep%20Hacks/data/processed/phase7/manifests/PHASE_7C_PROCESSING_MANIFEST.yaml) (`phase: PHASE_7C_PREPROCESSING_AND_FEATURE_ENGINEERING`)

14. `precip_peak_mmhr`: Peak event IMERG rainfall intensity (mm/hr).
15. `precip_accum_mm`: Total storm accumulated rainfall (mm).
16. `sar_vv_db`: Sentinel-1 VV backscatter intensity (dB).
17. `sar_vh_db`: Sentinel-1 VH backscatter intensity (dB).
18. `observed_flood_candidate`: Binary candidate inundation flag (`0` or `1`).
19. `tide_level_m`: Observed UHSLC sea level height at event (m).
20. `tide_anomaly_m`: Tidal anomaly relative to station baseline mean (m).

---

## 5. Explicit Limitations & Disclaimers

1. **IMERG Spatial Scale**: GPM IMERG provides ~10 km precipitation data. Downscaling onto the 30 m computational grid reflects spatial interpolation, NOT street-level rain gauge precision.
2. **Sentinel-1 Flood Depth**: Sentinel-1 SAR change detection identifies surface water presence (`OBSERVED_FLOOD_CANDIDATE`), but does NOT directly yield exact inundation water depth.
3. **No ML Model Training**: Phase 7C strictly performs deterministic data processing and feature synthesis. No XGBoost model training or ML calibration was executed.

---

## 6. Verification & Quality Assurance Summary

Automated QA checks validated:
- `100%` spatial extent and grid cell alignment across all raster products.
- `0` unhandled NaN/inf values in terrain and feature datasets.
- Absolute raw data immutability (`data/raw/phase7/` files unchanged).
- Provenance manifest generation under `data/processed/phase7/manifests/PHASE_7C_PROCESSING_MANIFEST.yaml`.
