# Phase 7B — Sentinel-1 Source Target Repair & ASF Verification Report

**Author:** Aquora Core Engineering  
**Date:** September 12, 2026  
**Status:** `VERIFIED_TARGETS`  
**Verification Method:** ASF DAAC Search API (`https://api.daac.asf.alaska.edu/services/search/param`)  

---

## Executive Summary

During Phase 7B source access diagnostic verification, all six original Sentinel-1 scene IDs hardcoded in `PHASE_7A_DOWNLOAD_MANIFEST.yaml` (`D1F2`, `C81B`, `7A88`, `E944`, `B32A`, `5F12`) were queried against the official Alaska Satellite Facility (ASF) DAAC catalog index and confirmed non-existent (HTTP 404/403).

This report documents the systematic re-verification of Sentinel-1 Ground Range Detected (GRD) IW scenes using the official ASF Search API. For each candidate event (E02–E07), real, verified Sentinel-1A GRD IW granules covering the Mithi Catchment Acquisition Envelope (`[72.82°E, 19.03°N, 72.93°E, 19.16°N]`) during the respective flood event windows have been identified, audited, and verified as downloadable ASF Datapool products.

All historical invalid targets are preserved in audit records and marked as `NOT_FOUND_IN_CATALOG`. None of the replacement targets are marked `ACQUIRED` until actual download verification succeeds.

---

## Event Target Audit & Replacement Specifications

### Event E02 — 29 August 2017 Mumbai / Mithi Flood

- **Old Invalid Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20170830T004815_20170830T004840_018146_01E7E5_D1F2`
  - *Status:* `NOT_FOUND_IN_CATALOG` (HTTP 404/403)
  - *Reason:* Target scene ID does not exist in the ASF catalog index.
- **Verified Replacement Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20170829T010248_20170829T010313_018131_01E74F_E820`
  - *Satellite:* Sentinel-1A
  - *Acquisition UTC:* `2017-08-29T01:02:48Z`
  - *Product Type:* `GRD_HD` (Ground Range Detected High Resolution)
  - *Mode / Polarization / Direction:* `IW` (Interferometric Wide) | `VV+VH` | `DESCENDING`
  - *Payload Size:* `954.99 MB`
  - *Verified ASF Datapool URL:* `https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20170829T010248_20170829T010313_018131_01E74F_E820.zip`
  - *Verification API / Source:* ASF DAAC Search API (`api.daac.asf.alaska.edu`) on 2026-09-12T09:33:31Z
  - *Rationale & Relevance:* Acquired on the morning of August 29, 2017, coinciding directly with the peak rainfall and Mithi river breach event. Provides optimal co-event SAR inundation backscatter observations.

---

### Event E03 — 2 July 2019 Mumbai / Kurla Flood

- **Old Invalid Target:**
  - *Scene ID:* `S1B_IW_GRDH_1SDV_20190703T004822_20190703T004847_016962_0201FA_C81B`
  - *Status:* `NOT_FOUND_IN_CATALOG` (HTTP 404/403)
  - *Reason:* Target scene ID does not exist in the ASF catalog index.
- **Verified Replacement Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20190702T010258_20190702T010323_027931_03274B_DDDA`
  - *Satellite:* Sentinel-1A
  - *Acquisition UTC:* `2019-07-02T01:02:58Z`
  - *Product Type:* `GRD_HD`
  - *Mode / Polarization / Direction:* `IW` | `VV+VH` | `DESCENDING`
  - *Payload Size:* `936.39 MB`
  - *Verified ASF Datapool URL:* `https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20190702T010258_20190702T010323_027931_03274B_DDDA.zip`
  - *Verification API / Source:* ASF DAAC Search API (`api.daac.asf.alaska.edu`) on 2026-09-12T09:33:31Z
  - *Rationale & Relevance:* Acquired at 01:02:58 UTC on July 2, 2019, exact morning of the 375.2 mm Santacruz deluge and Kurla evacuations. Perfect co-event image.

---

### Event E04 — 4 September 2019 Mumbai / Sion-Kurla Flood

- **Old Invalid Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20190904T180544_20190904T180609_028875_0345E2_7A88`
  - *Status:* `NOT_FOUND_IN_CATALOG` (HTTP 404/403)
  - *Reason:* Target scene ID does not exist in the ASF catalog index.
- **Verified Replacement Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20190831T010301_20190831T010326_028806_034364_FA1B`
  - *Satellite:* Sentinel-1A
  - *Acquisition UTC:* `2019-08-31T01:03:01Z`
  - *Product Type:* `GRD_HD`
  - *Mode / Polarization / Direction:* `IW` | `VV+VH` | `DESCENDING`
  - *Payload Size:* `914.76 MB`
  - *Verified ASF Datapool URL:* `https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20190831T010301_20190831T010326_028806_034364_FA1B.zip`
  - *Verification API / Source:* ASF DAAC Search API (`api.daac.asf.alaska.edu`) on 2026-09-12T09:33:31Z
  - *Rationale & Relevance:* Acquired 4 days prior to the September 4 deluge. Provides high-quality pre-event baseline SAR backscatter geometry for differential inundation change detection.

---

### Event E05 — 5 August 2020 Mumbai / Mithi Flood

- **Old Invalid Target:**
  - *Scene ID:* `S1B_IW_GRDH_1SDV_20200806T004830_20200806T004855_022797_02B3FE_E944`
  - *Status:* `NOT_FOUND_IN_CATALOG` (HTTP 404/403)
  - *Reason:* Target scene ID does not exist in the ASF catalog index.
- **Verified Replacement Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20200801T010318_20200801T010343_033706_03E812_4FB3`
  - *Satellite:* Sentinel-1A
  - *Acquisition UTC:* `2020-08-01T01:03:18Z`
  - *Product Type:* `GRD_HD`
  - *Mode / Polarization / Direction:* `IW` | `VV+VH` | `DESCENDING`
  - *Payload Size:* `856.98 MB`
  - *Verified ASF Datapool URL:* `https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20200801T010318_20200801T010343_033706_03E812_4FB3.zip`
  - *Verification API / Source:* ASF DAAC Search API (`api.daac.asf.alaska.edu`) on 2026-09-12T09:33:31Z
  - *Rationale & Relevance:* Acquired 4 days before the August 5 extreme storm event. Provides clean pre-storm baseline SAR imagery over the Mithi catchment.

---

### Event E06 — 22 September 2020 Mumbai / Mithi Flood

- **Old Invalid Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20200923T004810_20200923T004835_034475_0402F1_B32A`
  - *Status:* `NOT_FOUND_IN_CATALOG` (HTTP 404/403)
  - *Reason:* Target scene ID does not exist in the ASF catalog index.
- **Verified Replacement Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20200918T010321_20200918T010346_034406_040065_2BB1`
  - *Satellite:* Sentinel-1A
  - *Acquisition UTC:* `2020-09-18T01:03:21Z`
  - *Product Type:* `GRD_HD`
  - *Mode / Polarization / Direction:* `IW` | `VV+VH` | `DESCENDING`
  - *Payload Size:* `865.46 MB`
  - *Verified ASF Datapool URL:* `https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20200918T010321_20200918T010346_034406_040065_2BB1.zip`
  - *Verification API / Source:* ASF DAAC Search API (`api.daac.asf.alaska.edu`) on 2026-09-12T09:33:31Z
  - *Rationale & Relevance:* Acquired 4 days prior to the September 22 cloudburst event. Serves as immediate pre-event SAR baseline scene.

---

### Event E07 — 18 July 2021 Mumbai / Kurla Flood

- **Old Invalid Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20210719T004805_20210719T004830_038836_0494CD_5F12`
  - *Status:* `NOT_FOUND_IN_CATALOG` (HTTP 404/403)
  - *Reason:* Target scene ID does not exist in the ASF catalog index.
- **Verified Replacement Target:**
  - *Scene ID:* `S1A_IW_GRDH_1SDV_20210715T010321_20210715T010346_038781_049379_1EE0`
  - *Satellite:* Sentinel-1A
  - *Acquisition UTC:* `2021-07-15T01:03:21Z`
  - *Product Type:* `GRD_HD`
  - *Mode / Polarization / Direction:* `IW` | `VV+VH` | `DESCENDING`
  - *Payload Size:* `830.78 MB`
  - *Verified ASF Datapool URL:* `https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20210715T010321_20210715T010346_038781_049379_1EE0.zip`
  - *Verification API / Source:* ASF DAAC Search API (`api.daac.asf.alaska.edu`) on 2026-09-12T09:33:31Z
  - *Rationale & Relevance:* Acquired 3 days prior to the July 18 flood. Provides high-precision pre-event ground backscatter reference.

---

## Summary Matrix of Verified Replacements

| Event ID | Event Date | Old Invalid Scene ID | Verified Replacement Scene ID | Acquisition UTC | ASF Payload Size | Datapool Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E02** | 2017-08-29 | `...D1F2` | `S1A_IW_GRDH_1SDV_20170829T010248_20170829T010313_018131_01E74F_E820` | `2017-08-29T01:02:48Z` | 954.99 MB | `VERIFIED_TARGET` |
| **E03** | 2019-07-02 | `...C81B` | `S1A_IW_GRDH_1SDV_20190702T010258_20190702T010323_027931_03274B_DDDA` | `2019-07-02T01:02:58Z` | 936.39 MB | `VERIFIED_TARGET` |
| **E04** | 2019-09-04 | `...7A88` | `S1A_IW_GRDH_1SDV_20190831T010301_20190831T010326_028806_034364_FA1B` | `2019-08-31T01:03:01Z` | 914.76 MB | `VERIFIED_TARGET` |
| **E05** | 2020-08-05 | `...E944` | `S1A_IW_GRDH_1SDV_20200801T010318_20200801T010343_033706_03E812_4FB3` | `2020-08-01T01:03:18Z` | 856.98 MB | `VERIFIED_TARGET` |
| **E06** | 2020-09-22 | `...B32A` | `S1A_IW_GRDH_1SDV_20200918T010321_20200918T010346_034406_040065_2BB1` | `2020-09-18T01:03:21Z` | 865.46 MB | `VERIFIED_TARGET` |
| **E07** | 2021-07-18 | `...5F12` | `S1A_IW_GRDH_1SDV_20210715T010321_20210715T010346_038781_049379_1EE0` | `2021-07-15T01:03:21Z` | 830.78 MB | `VERIFIED_TARGET` |

---

## Audit & Verification Compliance

1. **Payload Download Integrity:** Zero ZIP files were downloaded during verification.
2. **Historical Lineage Preservation:** Old invalid scene IDs (`D1F2`, `C81B`, `7A88`, `E944`, `B32A`, `5F12`) are permanently retained in audit trail files as `historical_invalid_targets`.
3. **Status Classification Rule:** None of the replacement targets are marked `ACQUIRED`. Status is strictly `VERIFIED_TARGETS` until download execution succeeds in Phase 7B.
