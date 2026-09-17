# Phase 13 — Ground Truth + Photo Verification

## 1. Executive Summary
Phase 13 implements the **Ground Truth + Photo Verification** observation and evidence layer for AQUORA. It establishes the observational feedback loop:
$$\text{PREDICT} \longrightarrow \text{OBSERVE} \longrightarrow \text{COMPARE} \longrightarrow \text{CORROBORATE/CHALLENGE} \longrightarrow \text{LEARN} \longrightarrow \text{PREDICT BETTER}$$

### Key Principles & Governance
1. **Evidence vs. Truth**: An observation is *evidence*; it is **NOT** automatically verified ground truth and does **NOT** silently replace physics models or Digital Twin forecasts.
2. **Multi-Source Verification**:
   - `UNVERIFIED`: Single observation report, single photo, or single computer vision (CV) score.
   - `CORROBORATED`: $\ge 2$ independent compatible sources or spatial/temporal consistency.
   - `CONFIRMED`: Authoritative field team confirmation or explicit strong multi-source corroboration.
3. **Mandatory Governance Disclaimer**:
   > *"Ground Truth provides observational evidence and model-comparison support. It does not automatically certify observations, replace official ground truth, or issue emergency or municipal orders."*

---

## 2. Core Data Models

### `FloodObservation`
- **`observation_id`**: Unique observation identifier.
- **`latitude` / `longitude`**: WGS84 coordinates.
- **`location_source`**: `GPS`, `EXIF`, `MANUAL`, `UNKNOWN`.
- **`observed_at` / `received_at`**: Separate timestamps representing when condition occurred vs. when received by AQUORA.
- **`source` / `observer_type`**: `COMMUNITY`, `FIELD_TEAM`, `AUTHORITY`, `SENSOR`, `OTHER`.
- **`flood_presence`**: `FLOOD_PRESENT`, `NO_FLOOD_OBSERVED`, `UNKNOWN`.
- **`water_depth_class`**: Categorical classes (`DRY`, `<10CM`, `10_TO_20CM`, `20_TO_40CM`, `>40CM`, `UNKNOWN`). *Exact depth estimation from photos is strictly prohibited.*
- **`road_passability`**: `PASSABLE`, `DIFFICULT`, `NOT_PASSABLE`, `UNKNOWN`.
- **`verification_state`**: `UNVERIFIED`, `CORROBORATED`, `CONFIRMED`.
- **`evidence_strength`**: `WEAK`, `MODERATE`, `STRONG`, `UNKNOWN`.

### `ObservationMedia`
- File-backed storage under `data/processed/ground_truth/<obs_id>/`.
- Secure validation: SHA256 file hashing, MIME validation (`image/jpeg`, `image/png`, `image/webp`, `video/mp4`), 20MB file size limit, and path traversal protection.
- Bounded quality and image analysis (`SUFFICIENT`, `LIMITED`, `INSUFFICIENT`) without claiming fake neural network precision.

### `FloodIncident`
- Clustered incident grouping observations within `OBSERVATION_CLUSTER_RADIUS_M` (250m) and `OBSERVATION_CLUSTER_TIME_MINUTES` (60m).
- Unique source counting to prevent artificial corroboration from duplicate reports.

---

## 3. Digital Twin ↔ Observation Comparison

### Temporal & Spatial Matching
- **Run Start Anchor**: Observation time `observed_at` is evaluated relative to Digital Twin run start timestamp:
  $$\text{elapsed\_minutes} = \frac{\text{observed\_at} - \text{run\_start\_time}}{60}$$
- **Nearest Canonical Slice**: Maps elapsed time to canonical slices ($0, 30, 60, 90, 120, 150, 180 \text{ min}$) within tolerance (`DIGITAL_TWIN_OBSERVATION_MAX_TIME_DIFF_MINUTES` = 20 min). Out of tolerance $\implies$ `TIME_MISMATCH`.
- **Spatial Affine Lookup**: Transforms WGS84 point to Digital Twin raster cell. Out of bounds $\implies$ `LOCATION_MISMATCH`.

### Comparison States
- **`MODEL_SUPPORTS_OBSERVATION`**: Modeled severity is consistent with observed flood presence/depth.
- **`MODEL_CONTRADICTS_OBSERVATION`**: Modeled state differs from observed condition (surfaced cautiously as "Potential model/observation mismatch").
- **`MODEL_NO_DATA` / `TIME_MISMATCH` / `LOCATION_MISMATCH`**: Inconclusive spatial or temporal matching.

---

## 4. API Endpoints
- `POST /api/v1/ground-truth/observations`: Submit observation report.
- `GET /api/v1/ground-truth/observations`: List observations with filters.
- `POST /api/v1/ground-truth/observations/{id}/media`: Upload photo/video evidence.
- `GET /api/v1/ground-truth/incidents`: Retrieve clustered incidents.
- `POST /api/v1/ground-truth/runs`: Trigger ground truth analysis run.
- `GET /api/v1/ground-truth/observations/{id}/comparison`: Inspect model comparison.
