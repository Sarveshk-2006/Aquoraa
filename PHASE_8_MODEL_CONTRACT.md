# Aquora Phase 8 Operational Model Contract — Prototype XGBoost Flood Risk Model

**Document Status:** ACTIVE OPERATIONAL CONTRACT  
**Model Status:** `PROTOTYPE_ONLY`  
**Calibration Status:** `NOT_CALIBRATED`  
**Authoritative Engine:** FALSE (Secondary Empirical Risk Signal Only)  
**Physical Flood Engine Authority:** TRUE (Phase 6 Deterministic Engine is Sole Inundation Authority)  

---

## 1. Operational Invariants & System Scope

> [!IMPORTANT]
> **SYSTEM-WIDE INVARIANT**: The statistical XGBoost model is registered strictly as a secondary empirical pattern-matching risk signal. It **MUST NEVER** override, replace, or supersede physical hydrodynamic simulation output from the Phase 6 deterministic flood engine.

- **Primary Physical Engine Authority:** The Phase 6 2D hydrodynamic flow solver provides authoritative inundation depths, flow velocities, and flood extents.
- **Secondary Statistical Signal Role:** The XGBoost model provides fast empirical risk probabilities $[0.0, 1.0]$ by analyzing historical co-occurrence patterns across 12 approved geospatial and meteorologic features.
- **Sentinel-1 SAR Role:** Satellite Synthetic Aperture Radar (SAR) bitemporal backscatter drops serve as the historical observational ground truth candidate label source during supervised training. SAR features are **strictly excluded** from the model predictor matrix $X$.

---

## 2. Input Predictor Matrix Contract ($X$)

The model accepts **EXACTLY 12 APPROVED PREDICTORS** in the following mandatory order:

| Index | Feature Name | Data Type | Source Provider | Physical Unit | Description |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | `elevation_m` | `float32` | Copernicus DEM GLO-30 | meters (m) | Terrain surface elevation above MSL |
| 2 | `slope_deg` | `float32` | Copernicus DEM Derivative | degrees ($^\circ$) | Local terrain slope angle |
| 3 | `aspect_deg` | `float32` | Copernicus DEM Derivative | degrees ($^\circ$) | Terrain orientation angle |
| 4 | `flow_accumulation_cells` | `float32` | D8 Flow Direction Raster | cell count | Upstream drainage area in 30m grid cells |
| 5 | `drainage_proxy_score` | `float32` | Terrain Derivative | dimensionless | Logarithmic surface drainage index |
| 6 | `landcover_class` | `uint8` | ESA WorldCover 2021 v200 | class code (10–90) | Land cover classification code |
| 7 | `built_up_fraction` | `float32` | ESA WorldCover Window | fraction $[0, 1]$ | 3x3 window built-up area density |
| 8 | `distance_to_road_m` | `float32` | OpenStreetMap Highway | meters (m) | Euclidean distance to nearest road |
| 9 | `distance_to_waterway_m` | `float32` | OpenStreetMap Waterway | meters (m) | Euclidean distance to nearest channel |
| 10 | `rainfall_30min_mm` | `float32` | NASA GPM IMERG V07B | millimeters (mm) | 30-minute precipitation accumulation |
| 11 | `rainfall_intensity_mm_hr` | `float32` | NASA GPM IMERG V07B | mm/hour | Instantaneous rainfall rate |
| 12 | `tide_level_m` | `float32` | UHSLC Mumbai Port | meters (m) | Observed coastal sea surface height |

### Explicit Forbidden Feature List
The following features are **STRICTLY PROHIBITED** from entering $X$:
- Target & Label Evidence: `flood_label`, `label_status`, `evidence_strength`, `observed_flood_candidate`.
- SAR Observations & Change Rasters: `sar_pre_vv_db`, `sar_co_vv_db`, `sar_delta_vv_db`, `sar_pre_vh_db`, `sar_co_vh_db`, `sar_delta_vh_db`, `sar_strong_negative_change`, `sar_moderate_negative_change`, `sar_weak_negative_change`, `sar_usable_for_label`.
- Physical Engine Outputs: `physical_model_score`.
- Post-Event & Unapproved Variables: `rainfall_accum_24h_mm`, `permanent_water_mask`, `permanent_water`.

---

## 3. Output Contract & Semantics

- **Output Field:** `statistical_flood_risk_probability` (float in range $[0.0, 1.0]$)
- **Status Metadata:** `model_status: PROTOTYPE_ONLY`, `calibration_status: NOT_CALIBRATED`
- **Authority Flag:** `is_authoritative_engine: false`

---

## 4. UI & API Terminology Guidelines

To maintain clear scientific semantics across backend API endpoints and frontend UI interfaces:

### Approved Terminology
- **Statistical Risk Signal** — XGBoost model risk probability $[0, 1]$
- **Empirical ML Probability** — Uncalibrated pattern-matching risk score
- **Physical Flood Simulation** — Phase 6 deterministic hydraulic depth & velocity output
- **Observed SAR Evidence** — Sentinel-1 bitemporal satellite backscatter change observation

### Prohibited Terminology
- ❌ *"Predicted Flood Truth"*
- ❌ *"Actual Flood"*
- ❌ *"Satellite Flood Prediction"*
- ❌ *"Observed Depth"* (when referring to ML output)
- ❌ *"Hydraulic Simulation Output"* (when referring to ML output)

---

## 5. Artifact Hashes & Files

- **Model File:** `backend/data/models/aquora_xgboost_prototype.joblib`
- **Metadata File:** `backend/data/models/aquora_xgboost_metadata.json`
- **Model Card:** `PHASE_7_MODEL_CARD.md`
- **Operational Contract:** `PHASE_8_MODEL_CONTRACT.md`
- **Model SHA-256:** `ba96ed00159dabd8f332674c113e96310e8bf0284a07f0f31485df7103aebe4d`
