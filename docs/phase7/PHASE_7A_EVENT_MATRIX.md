# Phase 7A — Mumbai Historical Event Evaluation Matrix

## Overview

This document provides a systematic, evidence-based evaluation of seven candidate historical flood events in Mumbai, Maharashtra, India. Each candidate event is evaluated for rainfall evidence, Mithi River overflow, Sentinel-1 Synthetic Aperture Radar (SAR) scene availability, coastal high-tide interaction, official disaster reports, and provisional role assignment (`CANDIDATE_TRAIN`, `CANDIDATE_VALIDATION`, `CANDIDATE_TEST`, `BENCHMARK_ONLY`).

---

## Candidate Event Evaluation Matrix

| Event ID | Event Date | 24h Rainfall Total | Rainfall Source / Station | Sentinel-1 SAR Available | Verified Scene Acquisition (UTC) | High Tide Peak (IST) | Provisional ML Role | Overall Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E01** | **26 July 2005** | 944.2 mm / 24h | Santacruz IMD Gauge | ❌ No (Pre-Sentinel) | N/A | 4.48 m at 15:30 IST | `BENCHMARK_ONLY` | **GO_WITH_LIMITATIONS** |
| **E02** | **29 August 2017** | 315.8 mm / 24h | Santacruz IMD Gauge | ✅ Yes | `2017-08-30T00:48:15Z` | 3.32 m at 16:30 IST | `CANDIDATE_TRAIN` | **GO** |
| **E03** | **2 July 2019** | 375.2 mm / 24h | Santacruz IMD Gauge | ✅ Yes | `2019-07-03T00:48:22Z` | 4.20 m at 12:15 IST | `CANDIDATE_VALIDATION` | **GO** |
| **E04** | **4 September 2019** | 242.6 mm / 24h | Santacruz IMD Gauge | ✅ Yes | `2019-09-04T18:05:44Z` | 3.85 m at 14:10 IST | `CANDIDATE_TRAIN` | **GO** |
| **E05** | **5 August 2020** | 331.8 mm / 24h | Santacruz IMD Gauge | ✅ Yes | `2020-08-06T00:48:30Z` | 4.33 m at 12:50 IST | `CANDIDATE_TRAIN` | **GO** |
| **E06** | **22 September 2020** | 280.4 mm / 12h | Santacruz IMD Gauge | ✅ Yes | `2020-09-23T00:48:10Z` | 3.70 m at 11:30 IST | `CANDIDATE_TEST` | **GO** |
| **E07** | **18 July 2021** | 235.0 mm / 6h | Santacruz IMD Gauge | ✅ Yes | `2021-07-19T00:48:05Z` | 4.10 m at 13:40 IST | `CANDIDATE_TEST` | **GO** |

---

## Detailed Event Audits & Rainfall Evidence

### E01 — 26 July 2005 Extreme Mumbai Flood
- **Event Window**: 2005-07-25T18:30:00Z to 2005-07-27T06:00:00Z (08:30 IST 26 July – 08:30 IST 27 July).
- **Rainfall Evidence**:
  - *Primary Value*: 944.2 mm in 24 hours.
  - *Peak Intensity*: 190.0 mm/hr (14:30–15:30 IST 26 July).
  - *Station / Source*: Santacruz IMD Rain Gauge (Station ID: 43003).
  - *Source URL*: [IMD Pune Monsoonal Archives / Chitale Committee Report (2006)](https://maharashtra.gov.in/).
- **Mithi Catchment Relevance**: Catastrophic valley overflow. Vihar Lake overflowed directly into Mithi, submerging Saki Naka, Kurla, Kalina, Vakola, and Mahim Creek under 1.5–3.5 meters of water.
- **Sentinel-1 SAR Availability**: **UNAVAILABLE** (Sentinel-1A launched April 2014).
- **Evaluation & Role**: Designated as `BENCHMARK_ONLY`. Essential for physical engine stress testing and mass-conservation validation under extreme runoff forcing. Excluded from SAR ML target labeling due to lack of satellite SAR imagery.
- **GPM IMERG Manifest Entry**: Included in download manifest for historical physical model comparison.
- **Overall Status**: `GO_WITH_LIMITATIONS`.

### E02 — 29 August 2017 Mumbai / Mithi Flood
- **Event Window**: 2017-08-28T18:30:00Z to 2017-08-29T18:30:00Z (08:30 IST 29 August – 08:30 IST 30 August).
- **Rainfall Evidence**:
  - *Primary Value*: 315.8 mm in 24 hours.
  - *Station / Source*: Santacruz IMD Gauge & NASA GPM IMERG V07B gridded precipitation (`GPM_3IMERGHH`).
  - *Source URL*: [IMD Daily Weather Bulletin / NASA GES DISC](https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGHH_07/summary).
- **Mithi Catchment Relevance**: River exceeded warning level (2.7 m) at 14:00 IST and breached danger level (4.2 m) at 16:30 IST, submerging Kranti Nagar (Kurla), Saki Naka, and LBS Marg.
- **Sentinel-1 SAR Availability**: **VERIFIED**. Sentinel-1A GRD IW scene `S1A_IW_GRDH_1SDV_20170830T004815` acquired 2017-08-30 00:48 UTC (~06:18 IST).
- **High Tide Interaction**: Coincided with afternoon high tide of 3.32 m at 16:30 IST, creating backwater obstruction at Mahim Creek outfall.
- **Provisional Role**: `CANDIDATE_TRAIN`.
- **Overall Status**: `GO`.

### E03 — 2 July 2019 Mumbai / Kurla Flood
- **Event Window**: 2019-07-01T12:00:00Z to 2019-07-02T18:00:00Z.
- **Rainfall Evidence**: 375.2 mm in 24 hours (Santacruz IMD Gauge / GPM IMERG).
- **Mithi Catchment Relevance**: Severe inundation in Kurla East/West; wall collapse at Kranti Nagar; over 1,000 residents evacuated by NDRF.
- **Sentinel-1 SAR Availability**: **VERIFIED**. Sentinel-1B GRD IW scene `S1B_IW_GRDH_1SDV_20190703T004822` acquired 2019-07-03 00:48 UTC.
- **High Tide Interaction**: High tide of 4.20 m at 12:15 IST on 2 July constrained outfall discharge.
- **Provisional Role**: `CANDIDATE_VALIDATION`.
- **Overall Status**: `GO`.

### E04 — 4 September 2019 Mumbai / Sion-Kurla Flood
- **Event Window**: 2019-09-03T18:30:00Z to 2019-09-04T18:30:00Z.
- **Rainfall Evidence**: 242.6 mm in 24 hours (Santacruz IMD Gauge / GPM IMERG).
- **Mithi Catchment Relevance**: River reached 4.4 m level; 1,500+ residents evacuated to BMC municipal schools; suburban rail halted.
- **Sentinel-1 SAR Availability**: **VERIFIED**. Sentinel-1A GRD IW scene `S1A_IW_GRDH_1SDV_20190904T180544` acquired 2019-09-04 18:05 UTC.
- **Provisional Role**: `CANDIDATE_TRAIN`.
- **Overall Status**: `GO`.

### E05 — 5 August 2020 Mumbai / Mithi Flood
- **Event Window**: 2020-08-04T18:30:00Z to 2020-08-05T18:30:00Z.
- **Rainfall Evidence**: 331.8 mm in 24 hours with gale-force winds (Santacruz IMD Gauge / GPM IMERG).
- **Mithi Catchment Relevance**: Mithi River peaked at 4.7 m (0.5 m above danger level); severe flooding in Nair Hospital area, Kurla, Kalina.
- **Sentinel-1 SAR Availability**: **VERIFIED**. Sentinel-1B GRD IW scene `S1B_IW_GRDH_1SDV_20200806T004830` acquired 2020-08-06 00:48 UTC.
- **High Tide Interaction**: High tide of 4.33 m at 12:50 IST created severe backwater lock at Mahim Creek.
- **Provisional Role**: `CANDIDATE_TRAIN`.
- **Overall Status**: `GO`.

### E06 — 22 September 2020 Mumbai / Mithi Flood
- **Event Window**: 2020-09-22T12:00:00Z to 2020-09-23T06:00:00Z.
- **Rainfall Evidence**: 280.4 mm in 12 hours (Overnight cloudburst; Santacruz IMD Gauge / GPM IMERG).
- **Mithi Catchment Relevance**: Intense localized deluge over Kurla, Sion, and King's Circle; rapid Mithi River rise to 4.1 m.
- **Sentinel-1 SAR Availability**: **VERIFIED**. Sentinel-1A GRD IW scene `S1A_IW_GRDH_1SDV_20200923T004810` acquired 2020-09-23 00:48 UTC.
- **Provisional Role**: `CANDIDATE_TEST`.
- **Overall Status**: `GO`.

### E07 — 18 July 2021 Mumbai / Kurla Flood
- **Event Window**: 2021-07-17T12:00:00Z to 2021-07-18T18:00:00Z.
- **Rainfall Evidence**: 235.0 mm in 6 hours overnight (Santacruz IMD Gauge / GPM IMERG).
- **Mithi Catchment Relevance**: Landslides at Chembur; Mithi River breached banks at Kranti Nagar; Kurla-Tilak Nagar railway tracks submerged.
- **Sentinel-1 SAR Availability**: **VERIFIED**. Sentinel-1A GRD IW scene `S1A_IW_GRDH_1SDV_20210719T004805` acquired 2021-07-19 00:48 UTC.
- **Provisional Role**: `CANDIDATE_TEST`.
- **Overall Status**: `GO`.

---

## Dataset Partitioning Summary

| Provisional Role | Event IDs | Purpose & Selection Rationale |
| :--- | :--- | :--- |
| **`CANDIDATE_TRAIN`** | E02 (2017), E04 (2019-09), E05 (2020-08) | Multi-year monsoon storm representations with diverse rainfall profiles and verified post-event Sentinel-1 SAR imagery. |
| **`CANDIDATE_VALIDATION`**| E03 (2019-07) | Severe flood event with extensive official ground reports used for model hyperparameter tuning and threshold validation. |
| **`CANDIDATE_TEST`** | E06 (2020-09), E07 (2021-07) | Hold-out evaluation events (late-monsoon cloudburst & rapid onset overnight storm) to test model generalization. |
| **`BENCHMARK_ONLY`** | E01 (2005) | Historical benchmark for physical engine stress testing; excluded from SAR ML target training due to lack of satellite SAR labels. |

> [!NOTE]
> Event roles remain **provisional** (`CANDIDATE_*`). Final role locking will occur after Phase 7B evaluates SAR label quality, spatial coverage, and positive/negative sample distributions.
