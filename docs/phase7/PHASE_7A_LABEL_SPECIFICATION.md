# Phase 7A — Ground-Truth Labeling & Target Specification

## Overview

This document specifies the scientific methodology, label source hierarchy, quality scoring, and strict decoupling principles governing independent ground-truth target generation for the **Aquora Urban Flood Intelligence & Response Platform**.

---

## 1. Absolute Decoupling Principle

```text
+------------------------------------+       +------------------------------------+
|  PHASE 6 PHYSICAL ENGINE OUTPUTS  |       |  INDEPENDENT GROUND-TRUTH LABELS   |
|  - physical_flood_state            |       |  - Sentinel-1 SAR Backscatter      |
|  - surface_storage_m3              |  ≠    |  - BMC Inundation Reports          |
|  - modeled_water_depth_m           |       |  - CWC River Bank Breach Gauges    |
|  (PHYSICAL BASELINE / FEATURES)    |       |  (TARGET LABELS: observed_flood)   |
+------------------------------------+       +------------------------------------+
```

> [!CAUTION]
> **Never use Phase 6 physical simulation outputs as ML ground-truth labels.** Using model predictions to label training data creates a circular feedback loop that prevents ML from learning and correcting physical model bias. Physical outputs serve strictly as model inputs/features.

---

## 2. Satellite SAR Target Generation Methodology

Ground-truth surface water extent is derived independently using **Sentinel-1 SAR Bitemporal Change Detection**:

### 2.1 Preprocessing & Detection Workflow (Phase 7B Processing Spec)
1. **Scene Pair Selection**: Select a pre-event baseline scene ($\gamma^0_{\text{pre}}$) under dry conditions during the same monsoon season and an event scene ($\gamma^0_{\text{event}}$) acquired immediately following peak rainfall.
2. **Radiometric Calibration**: Calibrate raw Sentinel-1 GRD intensity to terrain-flattened backscatter $\gamma^0$ in linear scale.
3. **Speckle Filtering**: Apply a 5x5 Refined Lee Filter to reduce granular SAR speckle noise while preserving urban edges.
4. **Terrain Correction**: Perform Range Doppler Terrain Correction using Copernicus DEM GLO-30.
5. **Backscatter Ratio Calculation**:
   Calculate backscatter difference in dB:
   $$\Delta \gamma^0 = 10 \cdot \log_{10} \left( \frac{\gamma^0_{\text{event}}}{\gamma^0_{\text{pre\_event}}} \right)$$
   Surface water causes specular reflection of radar signals, resulting in a dramatic drop in backscatter intensity.
6. **Candidate Thresholding**:
   Apply a candidate threshold:
   $$\Delta \gamma^0 < \text{CANDIDATE\_THRESHOLD} \quad (\text{Initial candidate value: } -3.0 \text{ dB})$$
   Thresholds are designated as `CANDIDATE_THRESHOLD` and will be validated against actual scene statistics in Phase 7B.
7. **Spatial Aggregation**: Detection is performed on native resolution SAR calibrated products before aggregating the resulting binary flood mask and quality layer onto the 30m master computational grid.

---

## 3. SAR Quality Flags & Urban Masking Rules

SAR imagery penetrates cloud cover; therefore, cloud cover is **NOT** a SAR quality limitation. Quality flags account for radar geometry and urban backscatter effects:

| Quality Indicator | Description & Handling |
| :--- | :--- |
| **Radar Shadow & Layover** | High-rise urban structures create radar shadow and layover. Cells within building shadow masks are tagged with `is_urban_masked = true` and `observation_quality = LOW`. |
| **Permanent Water Mask** | Permanent water bodies (Powai Lake, Vihar Lake, Mahim Bay) are masked using pre-event baseline imagery (`observed_flood = -1`). |
| **Temporal Mismatch** | Evaluates the time delta between peak rainfall and SAR pass. Delays $> 12\text{ hours}$ lower confidence score. |
| **Terrain Slope Context** | Steep terrain slope is preserved as a physical feature and quality indicator. Slope does **NOT** act as an absolute hard exclusion rule. |

---

## 4. Multi-Source Evidence Fusion Model

Official textual reports (e.g., BMC reports stating "Kurla submerged") provide corroborating evidence. They are **NOT** automatically converted into pixel-level labels for every 30m cell in a neighborhood.

Aquora maintains separate evidence layers:

```text
Sentinel-1 SAR Flood Mask  +  BMC Official Text Reports  +  CWC Gauge Breach Records
                                       ↓
                             Multi-Source Evidence Fusion
                                       ↓
                      observed_flood (0 / 1 / -1) + Quality Metadata
```

### Data Schema for Label Records

| Column Name | Type | Description | Allowed Values / Range |
| :--- | :--- | :--- | :--- |
| `observed_flood` | Integer / Enum | Binary inundation label | `0` (Dry), `1` (Observed Inundation), `-1` (Masked/Unknown) |
| `observation_source` | String | Originating label source | `SENTINEL_1_SAR`, `BMC_OFFICIAL_REPORT`, `CWC_GAUGE_BREACH` |
| `observation_quality` | String | Data quality rating | `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN` |
| `observation_confidence`| Float | Label confidence score | `0.00` to `1.00` |
| `sar_backscatter_diff_db`| Float | Bitemporal backscatter drop (dB) | Numeric |
| `is_urban_masked` | Boolean | True if masked due to building shadow | `true`, `false` |
