# Phase 7B — Real Data Acquisition & Verification Report

## Overview

This report documents the verification, acquisition, cryptographic integrity checking, spatial/temporal metadata validation, and provenance registration for historical flood datasets covering the **Mithi River Urban Catchment** and **Kurla–Saki Naka–Kalina–Sion Decision Corridor** in Mumbai, Maharashtra, India.

---

## 1. Execution Objectives & Phase Boundaries

Phase 7B establishes an auditable, reproducible real-data foundation for the pilot study. In strict accordance with the Phase 7B contract:

- **IN SCOPE**: Manifest validation, provider source URL verification, acquisition smoke testing, raw file storage (`data/raw/phase7/`), SHA-256 cryptographic hash computation, raster/vector metadata checks, and provenance registration (`data/processed/phase7/verification/PHASE_7B_ACQUISITION_REGISTRY.yaml`).
- **OUT OF SCOPE**: ML model training, Kaggle pipeline creation, scikit-learn/XGBoost fitting, feature engineering, master Parquet feature matrix compilation, flood predictions, or frontend digital twin visualization.

---

## 2. Source Verification & Acquisition Table

| ID | Data Category | Product / Tile / Scene | Status | Verification Result | Local Path / Storage | Size (MB) | Cryptographic SHA-256 Hash |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DL-DEM-001** | Terrain | Copernicus DEM GLO-30 (`Copernicus_DSM_COG_10_N19_00_E072_00`) | `DOWNLOADED` | Verified & Downloaded | `data/raw/phase7/dem/Copernicus_DSM_COG_10_N19_00_E072_00.tif` | 12.72 | `b90f91a2b8cd69da327d8c133417d119a44f9880c8bb080114be5d8e9cf3dcdd` |
| **DL-LC-001** | Land Cover | ESA WorldCover 2021 10m V200 (`ESA_WorldCover_10m_2021_v200_N18E072`) | `DOWNLOADED` | Verified & Downloaded | `data/raw/phase7/landcover/ESA_WorldCover_10m_2021_v200_N18E072_Map.tif` | 119.94 | `2d28650e0eba865efb08656e45b75a269eaf535f9260a245ae5aad72ee5a5c63` |
| **DL-OSM-001** | Urban Data | OpenStreetMap Bounding Box Extract (`[19.03, 72.82, 19.16, 72.93]`) | `DOWNLOADED` | Verified & Downloaded via Overpass API | `data/raw/phase7/osm/osm_mithi_envelope.json` | 47.63 | `6db1f6781c5d5641da2aa9693703054310389e3f02825de746e987779ff8500a` |
| **DL-TIDE-001**| Coastal Tide | Mumbai Port Trust Hourly Tide Data (UHSLC Station 846A / Indian Ocean) | `DOWNLOADED` | Verified & Downloaded | `data/raw/phase7/tide/mumbai_port_h846a.csv` | 0.01 | `7eb2ba13900de76a774be47bfb7426507da07085c758f1c77611fa84ed4b7b22` |
| **DL-RAIN-E01**| Precipitation | NASA GPM IMERG V07B Final Half-Hourly (E01 2005) | `NEEDS_MANUAL_AUTH` | Provider URL verified | `data/raw/phase7/rainfall/E01/` | 0.0 | *Requires Earthdata Token* |
| **DL-RAIN-E02**| Precipitation | NASA GPM IMERG V07B Final Half-Hourly (E02 2017) | `NEEDS_MANUAL_AUTH` | Provider URL verified | `data/raw/phase7/rainfall/E02/` | 0.0 | *Requires Earthdata Token* |
| **DL-RAIN-E03**| Precipitation | NASA GPM IMERG V07B Final Half-Hourly (E03 2019-07) | `NEEDS_MANUAL_AUTH` | Provider URL verified | `data/raw/phase7/rainfall/E03/` | 0.0 | *Requires Earthdata Token* |
| **DL-RAIN-E04**| Precipitation | NASA GPM IMERG V07B Final Half-Hourly (E04 2019-09) | `NEEDS_MANUAL_AUTH` | Provider URL verified | `data/raw/phase7/rainfall/E04/` | 0.0 | *Requires Earthdata Token* |
| **DL-RAIN-E05**| Precipitation | NASA GPM IMERG V07B Final Half-Hourly (E05 2020-08) | `NEEDS_MANUAL_AUTH` | Provider URL verified | `data/raw/phase7/rainfall/E05/` | 0.0 | *Requires Earthdata Token* |
| **DL-RAIN-E06**| Precipitation | NASA GPM IMERG V07B Final Half-Hourly (E06 2020-09) | `NEEDS_MANUAL_AUTH` | Provider URL verified | `data/raw/phase7/rainfall/E06/` | 0.0 | *Requires Earthdata Token* |
| **DL-RAIN-E07**| Precipitation | NASA GPM IMERG V07B Final Half-Hourly (E07 2021-07) | `NEEDS_MANUAL_AUTH` | Provider URL verified | `data/raw/phase7/rainfall/E07/` | 0.0 | *Requires Earthdata Token* |
| **DL-SAR-E02** | SAR Ground Truth| Sentinel-1A GRD IW (`S1A_IW_GRDH_1SDV_20170830T004815...`) | `NEEDS_MANUAL_AUTH` | Scene verified on ASF DAAC | `data/raw/phase7/sentinel1/E02/` | 0.0 | *Requires Earthdata Token* |
| **DL-SAR-E03** | SAR Ground Truth| Sentinel-1B GRD IW (`S1B_IW_GRDH_1SDV_20190703T004822...`) | `NEEDS_MANUAL_AUTH` | Scene verified on ASF DAAC | `data/raw/phase7/sentinel1/E03/` | 0.0 | *Requires Earthdata Token* |
| **DL-SAR-E04** | SAR Ground Truth| Sentinel-1A GRD IW (`S1A_IW_GRDH_1SDV_20190904T180544...`) | `NEEDS_MANUAL_AUTH` | Scene verified on ASF DAAC | `data/raw/phase7/sentinel1/E04/` | 0.0 | *Requires Earthdata Token* |
| **DL-SAR-E05** | SAR Ground Truth| Sentinel-1B GRD IW (`S1B_IW_GRDH_1SDV_20200806T004830...`) | `NEEDS_MANUAL_AUTH` | Scene verified on ASF DAAC | `data/raw/phase7/sentinel1/E05/` | 0.0 | *Requires Earthdata Token* |
| **DL-SAR-E06** | SAR Ground Truth| Sentinel-1A GRD IW (`S1A_IW_GRDH_1SDV_20200923T004810...`) | `NEEDS_MANUAL_AUTH` | Scene verified on ASF DAAC | `data/raw/phase7/sentinel1/E06/` | 0.0 | *Requires Earthdata Token* |
| **DL-SAR-E07** | SAR Ground Truth| Sentinel-1A GRD IW (`S1A_IW_GRDH_1SDV_20210719T004805...`) | `NEEDS_MANUAL_AUTH` | Scene verified on ASF DAAC | `data/raw/phase7/sentinel1/E07/` | 0.0 | *Requires Earthdata Token* |

---

## 3. Smoke Test Results

The acquisition smoke test verified the functionality of the public download pipeline (`scripts/phase7b_acquisition_service.py --mode smoke`):

1. **Copernicus DEM GLO-30**: Downloaded `Copernicus_DSM_COG_10_N19_00_E072_00.tif` (12.72 MB). Validated GeoTIFF driver and dimensions via `rasterio`.
2. **ESA WorldCover 2021 Tile**: Downloaded `ESA_WorldCover_10m_2021_v200_N18E072_Map.tif` (119.94 MB). Validated GeoTIFF driver and dimensions via `rasterio`.
3. **OpenStreetMap Overpass Extractor**: Executed spatial bounding box query for Mithi envelope `[19.03, 72.82, 19.16, 72.93]`. Validated GeoJSON structure (47.63 MB).
4. **UHSLC Coastal Tide Series**: Downloaded `mumbai_port_h846a.csv` successfully. SHA-256 hash verified.

---

## 4. Authentication & Credentials Isolation

- **NASA Earthdata Access**: Downloading NASA GPM IMERG precipitation files and ASF DAAC Sentinel-1 SAR scenes requires Earthdata user authentication.
- **Security Invariant**: Environment variable `EARTHDATA_TOKEN` is used exclusively for request headers. Secrets are strictly isolated and are **NEVER** committed, printed to console logs, or stored in YAML registries.
- **Manual Configuration Requirement**: To download the full 13 authenticated scenes, export `EARTHDATA_TOKEN=<your_token>` and rerun `python scripts/phase7b_acquisition_service.py --mode acquire`.

---

## 5. Explicit Audit of Non-Executed Tasks

In strict adherence to Phase 7B scope boundaries:

- ❌ No machine learning models (XGBoost, Random Forest, scikit-learn) were trained or fitted.
- ❌ No Kaggle notebooks or pipelines were created.
- ❌ No master Parquet feature matrix was compiled.
- ❌ No feature engineering (lagged rainfall, rolling accumulations, distance metrics) was executed.
- ❌ No Phase 8 nowcasting or Phase 9 frontend digital twin development was performed.
