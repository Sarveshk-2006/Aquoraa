# Aquora Phase 7 Model Card — Prototype XGBoost Flood Risk Model

**Model Status:** `PROTOTYPE_ONLY`  
**Model Name:** `aquora_xgboost_prototype`  
**Version:** 1.0.0  
**Created At:** 2026-09-16T19:41:44.127235+00:00  
**Authoritative Status:** SECONDARY / PROTOTYPE PROBABILITY SIGNAL ONLY (NOT Authoritative Flood Engine)  

---

## 1. Governance & Disclaimer
> [!IMPORTANT]
> **PROTOTYPE ONLY**: This XGBoost machine-learning model is trained as a statistical pattern-matching baseline on historical Sentinel-1 satellite SAR observations. It is **NOT** a hydraulic physics solver, **NOT** an authoritative flood inundation engine, and **MUST NEVER** override or replace the deterministic physical engine (Phase 6). The predictions represent secondary empirical flood risk probabilities.

---

## 2. Intended & Non-Intended Use

### Intended Use
- Secondary probability signal to complement deterministic physical hydraulic depth calculations.
- Rapid pattern analysis across the 12 approved geospatial and hydrometeorological features for historical events.
- Evaluation of empirical flood risk sensitivity to elevation, drainage, land cover, rainfall intensity, and coastal tide levels.

### Non-Intended Use
- Operational real-time disaster response decision-making without physical engine confirmation.
- Replacement of shallow-water / hydrodynamic flow accumulation models.
- Extrapolation beyond the Mithi River Catchment study domain or outside observed rainfall/tide envelopes.
- Claiming causal relationship from feature importance rankings.

---

## 3. Approved Predictors (Exact 12 Features)
The predictor matrix \(X\) uses **ONLY** the 12 approved pre-event / static / meteorologic predictors from `PHASE_7_FEATURE_POLICY.yaml`:

1. `elevation_m` — Copernicus DEM GLO-30 surface elevation (m)
2. `slope_deg` — Terrain slope angle (degrees)
3. `aspect_deg` — Terrain orientation angle (degrees)
4. `flow_accumulation_cells` — Vectorized D8 flow accumulation cell count
5. `drainage_proxy_score` — Surface drainage proxy score
6. `landcover_class` — ESA WorldCover 2021 categorical land-cover class
7. `built_up_fraction` — 3x3 spatial window built-up fraction
8. `distance_to_road_m` — Euclidean distance to OpenStreetMap road network (m)
9. `distance_to_waterway_m` — Euclidean distance to OpenStreetMap waterway network (m)
10. `rainfall_30min_mm` — NASA GPM IMERG Final V07B 30-minute precipitation accumulation (mm)
11. `rainfall_intensity_mm_hr` — Instantaneous precipitation rate (mm/hr)
12. `tide_level_m` — UHSLC Mumbai Port observed tide level (m)

### Explicit Leakage Prevention Audit
- **Zero SAR backscatter delta / candidate mask leakage**: SAR VV/VH levels, SAR deltas, and SAR inundation candidates are **strictly excluded** from \(X\).
- **Zero Target Leakage**: `flood_label`, `label_status`, `evidence_strength`, and `observed_flood_candidate` are **strictly excluded** from \(X\).
- **Zero Physical Model Leakage**: `physical_model_score` and post-event variables are **strictly excluded**.
- **Zero 24h Accumulation Leakage**: `rainfall_accum_24h_mm` is excluded while unapproved.

---

## 4. Target Definition
- **Target Variable:** `observed_flood_candidate` (Binary: 1.0 for evidence-supported inundation candidates, 0.0 for non-flood land).
- **Evidence Source:** Bitemporal Copernicus Sentinel-1 GRD SAR backscatter drops (SAR delta VV < -3.0 dB or SAR delta VH < -3.0 dB) on non-permanent-water land.

---

## 5. Historical Event Coverage & Split Isolation
To eliminate temporal and spatial data leakage, data is partitioned by discrete historical events:

| Partition | Event ID | Date | Total Cells | Observed Positives | Positive % | Role |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **TRAIN** | E02, E04, E05, E06 | 2017–2020 | 746,368 | 14,957 | 2.004% | Model Supervised Fitting |
| **VALIDATION** | E03 | 2019-07-02 | 186,592 | 0 | 0.000% | Hyperparameter / Baseline Verification |
| **TEST** | E07 | 2021-07-15 | 186,592 | 13,137 | 7.040% | **Untouched** Final Generalization Evaluation |
| **BENCHMARK ONLY** | E01 | 2005-07-26 | 186,592 | N/A | N/A | Excluded (No Sentinel-1 observation) |

---

## 6. Model Hyperparameters & Training Configuration
- **Algorithm:** `xgboost.XGBClassifier`
- **Random Seed:** `42`
- **Class Weighting:** `scale_pos_weight = 48.900916` (derived strictly from TRAIN partition ratio)
- **Trees (`n_estimators`):** `100`
- **Max Depth (`max_depth`):** `6`
- **Learning Rate (`learning_rate`):** `0.05`
- **Subsample Ratio (`subsample`):** `0.8`
- **Column Subsample (`colsample_bytree`):** `0.8`
- **Evaluation Metric:** `logloss`

---

## 7. Performance Evaluation Metrics

### Partition-Level Metrics Summary (Probability Threshold = 0.5)

| Metric | TRAIN (E02, E04, E05, E06) | VALIDATION (E03) | TEST (E07 - Untouched) |
| :--- | :---: | :---: | :---: |
| **ROC-AUC** | `0.7370` | `N/A (Single Class)` | `0.5914` |
| **PR-AUC / Average Precision** | `0.0465` | `N/A (Single Class)` | `0.0890` |
| **Precision** | `0.0304` | `0.0000` | `0.0775` |
| **Recall** | `0.9848` | `0.0000` | `0.9533` |
| **F1-Score** | `0.0590` | `0.0000` | `0.1434` |
| **Accuracy** | `0.3703` | `1.0000` | `0.1983` |
| **Brier Score** | `0.2295` | `0.0000` | `0.2990` |
| **Actual Positive Rate** | `0.0200` | `0.0000` | `0.0704` |
| **Predicted Positive Rate** | `0.6491` | `0.0000` | `0.8655` |

### TEST Set (E07) Confusion Matrix (Threshold = 0.5)
- **True Positives (TP):** `12,523`
- **True Negatives (TN):** `24,480`
- **False Positives (FP):** `148,975`
- **False Negatives (FN):** `614`

---

## 8. Feature Importance Diagnostic (Gain Importance)
*Note: Feature importances serve as diagnostic pattern indicators and DO NOT convey causality.*

| Rank | Feature Name | Gain Importance | Weight (Split Frequency) |
| :---: | :--- | :---: | :---: |
|  1 | `rainfall_30min_mm` | `27425.3633` | `70` |
|  2 | `rainfall_intensity_mm_hr` | `16351.8662` | `25` |
|  3 | `landcover_class` | `2969.7341` | `208` |
|  4 | `distance_to_road_m` | `230.4837` | `576` |
|  5 | `distance_to_waterway_m` | `181.2923` | `637` |
|  6 | `aspect_deg` | `181.2250` | `75` |
|  7 | `elevation_m` | `178.9166` | `618` |
|  8 | `built_up_fraction` | `145.8977` | `181` |
|  9 | `slope_deg` | `113.7587` | `90` |
| 10 | `flow_accumulation_cells` | `110.8253` | `62` |
| 11 | `drainage_proxy_score` | `103.3956` | `89` |
| 12 | `tide_level_m` | `0.0000` | `0` |

---

## 9. Known Limitations & Caveats
1. **Class Imbalance:** Flood evidence cells represent ~2.0% of training data and ~7.0% of test data. High precision requires careful threshold tuning.
2. **Sentinel-1 SAR Constraints:** Satellite observations record surface specular reflection change, which can be affected by dense urban canopy shadowing, radar specular bounce on smooth non-flooded pavement, or temporal acquisition lag.
3. **Event Generalization:** Performance is evaluated on 7 historical events in Mumbai; generalization to unprecedented meteorological conditions or different geographic catchments is unverified.
4. **E01 Exclusion:** Event E01 (2005 Mumbai Flood) lacks Sentinel-1 satellite observation and is strictly reserved for deterministic hydrodynamic benchmark comparison.
5. **Non-Hydraulic Nature:** The model evaluates spatial co-occurrence patterns of elevation, slope, rainfall, and tide, but does not solve mass conservation, momentum equations, or pipe network drainage capacities.

---

**Artifact Path:** `backend/data/models/aquora_xgboost_prototype.joblib`  
**Metadata Path:** `backend/data/models/aquora_xgboost_metadata.json`  
**Model SHA256:** `ba96ed00159dabd8f332674c113e96310e8bf0284a07f0f31485df7103aebe4d`  
