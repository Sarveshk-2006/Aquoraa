# Phase 7D.1 — Flood Label Evidence Gap Audit & Specification

## Executive Summary

This specification documents the **Phase 7D.1 Flood Label Evidence Gap Audit** for the **Aquora Urban Flood Intelligence & Response Platform**, covering the Mithi River urban catchment (Kurla–Saki Naka–Kalina–Sion corridor) in Mumbai, Maharashtra, India.

A comprehensive audit of the local Phase 7 dataset reveals that **supervised flood label construction is currently NOT possible (`supervised_labels_currently_possible = "NO"`)**. While 13,377 feature rows across 7 historical events (`E01`–`E07`) exist on the 30m computational grid, **zero validated binary flood labels (`flood_label = 1` or `flood_label = 0`) can be defensibly assigned**.

- **E01 (2005)**: Pre-satellite event (`BENCHMARK_ONLY`), no SAR satellite coverage exists.
- **E02 (2017) & E03 (2019-07)**: Post-event Sentinel-1 SAR scenes exist, but **pre-event monsoonal SAR baselines are missing** in local storage, preventing bitemporal change detection ($\Delta \gamma^0$).
- **E04 (2019-09), E05 (2020-08), E06 (2020-09), & E07 (2021-07)**: Pre-event SAR scenes exist, but **co-event / post-event SAR scenes are missing** in local storage.
- **Authoritative Ground Records**: Zero municipal (BMC) or hydrological (CWC) flood observations are present in local storage (`data/raw/phase7/official_observations/` is empty).

Promoting unvalidated candidate signals to ground truth or fabricating labels from rainfall/terrain features would violate Phase 7A label specifications and introduce target contamination. This document specifies the **exact minimum 6-scene Sentinel-1 SAR acquisition set** required to unlock bitemporal change detection and establish a supervised flood target.

---

## 1. Reconstructed Event Evidence Matrix

The table below summarizes the observational evidence currently present in local storage across all 7 pilot events:

| Event ID | Event Date | Provisional ML Role | Rainfall Coverage (IMERG) | Local SAR Scene ID | SAR Acquisition (UTC) | Pre-Event Baseline Present? | Local Candidate Evidence Cells | Local Authoritative Observations | Current Label Status | Labelability Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E01** | 2005-07-26 | `BENCHMARK_ONLY` | 1 Granule (2005-07-26T09:30Z) | None | N/A | N/A | 0 | None | `UNAVAILABLE` | `BENCHMARK_ONLY` |
| **E02** | 2017-08-29 | `TRAIN` | 1 Granule (2017-08-29T10:00Z) | `S1A_..._E820` | 2017-08-29T01:02:48Z | ❌ Missing | 134 cells | None | `UNVALIDATED_CANDIDATE` | `LABELABLE_WITH_ADDITIONAL_EVIDENCE` |
| **E03** | 2019-07-02 | `VALIDATION` | 1 Granule (2019-07-02T01:00Z) | `S1A_..._DDDA` | 2019-07-02T01:02:58Z | ❌ Missing | 196 cells | None | `UNVALIDATED_CANDIDATE` | `LABELABLE_WITH_ADDITIONAL_EVIDENCE` |
| **E04** | 2019-09-04 | `TRAIN` | 1 Granule (2019-09-04T08:30Z) | `S1A_..._FA1B` | 2019-08-31T01:03:01Z | ✅ Present (2019-08-31) | 0 | None | `UNAVAILABLE` | `LABELABLE_WITH_ADDITIONAL_EVIDENCE` |
| **E05** | 2020-08-05 | `TRAIN` | 1 Granule (2020-08-05T12:00:00Z) | `S1A_..._4FB3` | 2020-08-01T01:03:18Z | ✅ Present (2020-08-01) | 0 | None | `UNAVAILABLE` | `LABELABLE_WITH_ADDITIONAL_EVIDENCE` |
| **E06** | 2020-09-22 | `TRAIN` | 1 Granule (2020-09-22T21:30:00Z) | `S1A_..._2BB1` | 2020-09-18T01:03:21Z | ✅ Present (2020-09-18) | 0 | None | `UNAVAILABLE` | `LABELABLE_WITH_ADDITIONAL_EVIDENCE` |
| **E07** | 2021-07-18 | `TEST` | 1 Granule (2021-07-18T01:00:00Z) | `S1A_..._1EE0` | 2021-07-15T01:03:21Z | ✅ Present (2021-07-15) | 0 | None | `UNAVAILABLE` | `LABELABLE_WITH_ADDITIONAL_EVIDENCE` |

---

## 2. Detailed Event-by-Event Labelability Justifications

1. **E01 (26 July 2005)** — `BENCHMARK_ONLY`
   - *Justification*: Event occurred prior to Sentinel-1 launch (April 2014). Satellite SAR target labeling is impossible. E01 is reserved strictly for physical hydrodynamic engine stress testing under extreme rainfall forcing (944.2 mm/24h).
2. **E02 (29 August 2017)** — `LABELABLE_WITH_ADDITIONAL_EVIDENCE`
   - *Justification*: Single-scene VV backscatter drops (< -18 dB) identified 134 candidate cells (`observed_flood_candidate = 1.0`). However, without a dry pre-event monsoonal SAR baseline (July/August 2017), backscatter drop $\Delta \gamma^0$ cannot be computed. Cannot be promoted to `flood_label = 1`.
3. **E03 (2 July 2019)** — `LABELABLE_WITH_ADDITIONAL_EVIDENCE`
   - *Justification*: Single-scene VV backscatter drops (< -18 dB) identified 196 candidate cells (`observed_flood_candidate = 1.0`). Requires a dry pre-event monsoonal SAR baseline (June 2019) to compute bitemporal backscatter drop $\Delta \gamma^0$.
4. **E04 (4 September 2019)** — `LABELABLE_WITH_ADDITIONAL_EVIDENCE`
   - *Justification*: Local scene `S1A_..._FA1B` acquired on 2019-08-31 acts as a valid dry pre-event baseline. However, the co-event scene acquired on 2019-09-04 (`S1A_IW_GRDH_1SDV_20190904T180544`) is missing in local storage.
5. **E05 (5 August 2020)** — `LABELABLE_WITH_ADDITIONAL_EVIDENCE`
   - *Justification*: Local scene `S1A_..._4FB3` acquired on 2020-08-01 acts as a valid dry pre-event baseline. The co-event scene acquired on 2020-08-06 (`S1B_IW_GRDH_1SDV_20200806T004830`) is missing in local storage.
6. **E06 (22 September 2020)** — `LABELABLE_WITH_ADDITIONAL_EVIDENCE`
   - *Justification*: Local scene `S1A_..._2BB1` acquired on 2020-09-18 acts as a valid dry pre-event baseline. The co-event scene acquired on 2020-09-23 (`S1A_IW_GRDH_1SDV_20200923T004810`) is missing in local storage.
7. **E07 (18 July 2021)** — `LABELABLE_WITH_ADDITIONAL_EVIDENCE`
   - *Justification*: Local scene `S1A_..._1EE0` acquired on 2021-07-15 acts as a valid dry pre-event baseline. The co-event scene acquired on 2021-07-19 (`S1A_IW_GRDH_1SDV_20210719T004805`) is missing in local storage.

---

## 3. Strict Positive & Negative Ground-Truth Protocols

### 3.1 Positive-Label Protocol (`flood_label = 1`)
A grid cell may ONLY be assigned `flood_label = 1` if it satisfies at least ONE of the following evidence rules:
1. **SAR Bitemporal Change Detection**: Bitemporal backscatter drop $\Delta \gamma^0 = 10 \log_{10} (\gamma^0_{\text{event}} / \gamma^0_{\text{pre}}) < -3.0 \text{ dB}$ on native 10m Sentinel-1 VV polarization aggregated to the 30m grid cell, AND non-building layover (`is_urban_masked = false`).
2. **Authoritative Ground Record**: Cell geometry intersects a georeferenced municipal flood record from BMC or CWC river gauge breach records during the event window.
3. **Multi-Source Evidence Agreement**: Coincident candidate SAR signal corroborated by independent citizen/news report within 500m.

> [!CAUTION]
> **Prohibited Positive Labeling Methods**:
> - High IMERG rainfall magnitude $\neq$ flood label at every cell.
> - Low elevation or depression in DEM $\neq$ flood label.
> - High drainage proxy score $\neq$ flood label.
> - Phase 6 hydrodynamic simulation output $\neq$ flood label (Circular Feedback Loop).

### 3.2 Negative-Label Protocol (`flood_label = 0`)
A grid cell may ONLY be assigned `flood_label = 0` if it satisfies the following rule:
1. **Validated Dry SAR Change Detection**: Cell is within valid SAR observation bounds, free from radar shadow/layover, AND bitemporal backscatter change $|\Delta \gamma^0| < 1.0 \text{ dB}$ (indicating stable non-flooded surface).

> [!CAUTION]
> **Prohibited Negative Labeling Assumptions**:
> - `observed_flood_candidate = 0` (or `NaN`) MUST NOT automatically become `flood_label = 0`.
> - Cells with missing SAR observations MUST remain `flood_label = NULL` (`flood_label_status = UNAVAILABLE`).
> - Unobserved cells MUST NOT be zero-filled for class balancing.

---

## 4. Analysis of Ancillary Evidence

1. **NASA IMERG Precipitation**:
   - Local storage contains 1 30-minute IMERG granule per event.
   - *Verdict*: IMERG rainfall is a **Model Input Predictor (`MODEL_INPUT`)**, NOT a ground-truth flood target. Additional IMERG rainfall history is not a blocker for ground-truth label construction.
2. **Municipal & Authoritative Ground Data**:
   - `data/raw/phase7/official_observations/` is currently empty.
   - *Verdict*: While municipal waterlogging records would provide valuable secondary validation, satellite SAR bitemporal change detection serves as the primary scientific ground truth source.
3. **UHSLC Sea Level / Tidal Observations**:
   - Local storage contains sea level observations for all 7 events.
   - *Verdict*: Tide height and anomaly represent physical boundary conditions (**Model Input Predictor**). Tide height MUST NOT be used directly to label cells as flooded.

---

## 5. Prioritized Acquisition Requirements (P0 / P1 / P2)

To enable supervised flood label construction, missing evidence is prioritized as follows:

### P0 Requirements (Essential for Supervised Target Construction)
The following **6 Sentinel-1 SAR scenes** are required to establish bitemporal pairs across events E02–E07:

1. **E02 Baseline**: Sentinel-1A GRD IW dry pre-event scene acquired July/August 2017 (Orbit 018).
2. **E03 Baseline**: Sentinel-1A/B GRD IW dry pre-event scene acquired June 2019 (Orbit 018).
3. **E04 Co-Event**: Sentinel-1A GRD IW scene `S1A_IW_GRDH_1SDV_20190904T180544` acquired 2019-09-04 18:05 UTC.
4. **E05 Co-Event**: Sentinel-1B GRD IW scene `S1B_IW_GRDH_1SDV_20200806T004830` acquired 2020-08-06 00:48 UTC.
5. **E06 Co-Event**: Sentinel-1A GRD IW scene `S1A_IW_GRDH_1SDV_20200923T004810` acquired 2020-09-23 00:48 UTC.
6. **E07 Co-Event**: Sentinel-1A GRD IW scene `S1A_IW_GRDH_1SDV_20210719T004805` acquired 2021-07-19 00:48 UTC.

### P1 Requirements (Recommended Validation Support)
- BMC official municipal waterlogging and evacuation records (GeoJSON/CSV format) for events E02–E07.

### P2 Requirements (Optional)
- CWC Mithi River hourly gauge level records during peak deluge windows.

---

## 6. Implementation Readiness & Next Steps

This specification completes **Phase 7D.1 Flood Label Evidence Gap Audit**.

- **Current Status**: Phase 7D.1 Complete (`PHASE 7D.1 COMPLETE — READY FOR EVIDENCE ACQUISITION REVIEW`).
- **Phase Boundary Integrity**: No external data downloads were initiated, no network calls were made, raw data remains 100% immutable, and no ML models were trained.
- **Next Action**: Human review of this evidence gap specification to authorize the controlled acquisition of the **6 P0 Sentinel-1 SAR scenes** in Phase 7D.2.
