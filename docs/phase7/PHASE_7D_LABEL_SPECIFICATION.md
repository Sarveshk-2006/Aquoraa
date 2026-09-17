# Phase 7D — Ground-Truth Flood Label & Dataset Specification

## Overview

This specification establishes the scientific principles, evidence-based label hierarchy, feature-label decoupling, zero-leakage constraints, and event-based partitioning governing the **Aquora Urban Flood Intelligence & Response Platform** ML-ready dataset for the Mithi River catchment in Mumbai, Maharashtra, India.

---

## 1. Evidence-Based Label Construction Philosophy

Aquora enforces a strict multi-tier distinction between raw remote sensing observations, candidate flood evidence, validated targets, and quality ratings:

```text
RAW OBSERVATIONS (Sentinel-1 SAR, IMERG Rain, UHSLC Tide, OSM Infrastructure)
                              ↓
DERIVED CANDIDATE EVIDENCE (observed_flood_candidate = 1/0/NaN, candidate_evidence_source)
                              ↓
VALIDATED FLOOD LABELS (flood_label = 1/0/NaN, flood_label_status, flood_label_source)
                              ↓
QUALITY & CONFIDENCE METADATA (flood_label_quality, flood_label_reason)
```

> [!IMPORTANT]
> **No Fabricated Target Labels**: A candidate inundation signal derived from single-scene low SAR backscatter (e.g. E02, E03) WITHOUT a pre-event baseline (`NO_VALID_BASELINE`) MUST NOT be automatically promoted to `flood_label = 1`. In the absence of multi-source ground truth validation or pre-event change detection, `flood_label_status` is designated as `UNVALIDATED_CANDIDATE` and `flood_label` is preserved as `NULL`.

---

## 2. Label Taxonomy & Controlled Vocabulary

| Schema Column | Data Type | Permitted Controlled Values | Description & Provenance |
| :--- | :--- | :--- | :--- |
| `flood_label` | Float / Nullable | `1.0` (Validated Flood), `0.0` (Validated Dry), `NaN` (NULL / Insufficient Evidence) | Binary ground-truth target label. `NaN` when evidence is unvalidated, absent, or ambiguous. |
| `flood_label_status` | String | `VALIDATED`, `UNVALIDATED_CANDIDATE`, `UNAVAILABLE`, `AMBIGUOUS` | High-level status of target label validation. |
| `flood_label_source` | String | `SENTINEL1`, `MULTI_SOURCE`, `COMMUNITY`, `AUTHORITATIVE`, `NONE` | Originating data source of the validated label. |
| `flood_label_quality` | String | `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN` | Confidence level of label assignment. |
| `flood_label_reason` | String | Free text explanatory string | Scientific justification for label or `NULL` assignment. |
| `observed_flood_candidate`| Float / Nullable | `1.0` (Candidate Flood), `0.0` (Non-candidate), `NaN` (No SAR Scene) | Raw candidate inundation evidence derived from Sentinel-1 VV backscatter (< -18 dB). |
| `candidate_evidence_source`| String | `SENTINEL1`, `NONE` | Source of raw candidate evidence. |
| `candidate_evidence_reason`| String | Free text explanatory string | Justification for candidate evidence classification. |

---

## 3. Strict Feature vs. Target Decoupling (Zero Target Leakage)

To prevent circular feedback loops and data leakage, all dataset fields are strictly partitioned into **Predictive Inputs (`MODEL_INPUT`)** versus **Target Evidence (`LABEL_EVIDENCE` / `TARGET_LABEL`)**:

### 3.1 Legitimate Predictive Input Features (16 Features)
The following 16 features are strictly antecedent or static physical drivers and may be used by ML predictors:
1. `elevation_m`: Terrain surface elevation from Copernicus DEM GLO-30 (m).
2. `slope_deg`: Terrain slope angle in degrees [0, 90°].
3. `aspect_deg`: Terrain aspect orientation in compass degrees [0, 360°].
4. `flow_accumulation_cells`: Single D8 flow accumulation cell count.
5. `drainage_proxy_score`: Dimensionless surface drainage score $\log(1 + \text{FlowAcc}) / (\text{Slope} + 1.0)$.
6. `landcover_class`: ESA WorldCover 2021 land cover class code.
7. `built_up_fraction`: Area fraction of built-up land cover `[0.0, 1.0]`.
8. `is_built_up`: Binary indicator of built-up land cover.
9. `is_vegetation`: Binary indicator of vegetative land cover.
10. `is_water`: Binary indicator of permanent water bodies.
11. `distance_to_road_m`: Continuous Euclidean distance to nearest OSM road (m).
12. `distance_to_waterway_m`: Continuous Euclidean distance to nearest OSM waterway (m).
13. `rainfall_30min_mm`: NASA IMERG 30-minute precipitation accumulation (mm).
14. `rainfall_intensity_mm_hr`: NASA IMERG instantaneous precipitation rate (mm/hr).
15. `tide_level_m`: Observed UHSLC sea level height at event time (m).
16. `tide_anomaly_m`: Tidal anomaly relative to station MSL (1.42 m).

### 3.2 Target & Evidence Columns (EXCLUDED from Model Predictors)
The following fields directly encode target outcomes or post-event observations and **MUST NEVER** be included in model input feature matrices:
- `flood_label`, `flood_label_status`, `flood_label_source`, `flood_label_quality`, `flood_label_reason`
- `observed_flood_candidate`, `candidate_evidence_source`, `candidate_evidence_reason`
- `sar_vv_db`, `sar_vh_db`, `sar_vv_vh_ratio`
- `physical_model_score`

---

## 4. Leakage-Safe Event-Based Dataset Partitioning

To avoid spatial and temporal autocorrelation leakage between neighboring grid cells during training, Aquora enforces **strict event-based splits**:

```text
+-----------------------------------------------------------------------------------+
|  PHASE 7D MASTER DATASET (13,377 Rows = 1,911 Grid Cells × 7 Events)               |
+-----------------------------------------------------------------------------------+
       │                       │                       │                     │
       ▼                       ▼                       ▼                     ▼
  TRAIN SPLIT             VALIDATION SPLIT         TEST SPLIT         BENCHMARK ONLY
  (7,644 rows / 57.1%)    (1,911 rows / 14.3%)   (1,911 rows / 14.3%) (1,911 rows / 14.3%)
  - E02 (2017-08)         - E03 (2019-07)         - E07 (2021-07)       - E01 (2005-07)
  - E04 (2019-09)
  - E05 (2020-08)
  - E06 (2020-09)
```

- **Rationale**:
  - `E01` (2005 extreme deluge) is pre-Sentinel-1 and reserved as a physical engine stress-testing benchmark (`BENCHMARK_ONLY`).
  - `E02`, `E04`, `E05`, `E06` represent diverse monsoon storm regimes across 2017–2020 (`TRAIN`).
  - `E03` (July 2019 Kurla deluge) is held out for hyperparameter validation (`VALIDATION`).
  - `E07` (July 2021 cloudburst) is held out as the final unseen temporal test set (`TEST`).

---

## 5. Explicit Limitations & Disclaimers

1. **Hackathon / Experimental Scale**: This dataset is an experimental hackathon dataset spanning 7 monsoon flood events and 1,911 computational grid cells. It is not an operational municipal flood-risk benchmark.
2. **Limited Ground Truth Coverage**: Satellite SAR backscatter and citizen reports provide sparse observations. Unvalidated candidate signals remain `NULL` rather than forced binary labels.
3. **IMERG Spatial Granularity**: NASA IMERG rainfall (~10 km native) is bilinearly interpolated onto the 30m grid and does not reflect micro-scale gauge variations.
