# Phase 10 — Flood-Aware Routing & Travel Window

## Overview & Objectives
Phase 10 introduces flood-aware route analysis and temporal travel window estimation for the Aquora Urban Flood Intelligence Platform.
It answers the core operational question:

> *"Can I still take this route, and how much usable travel window do I have before modeled flooding renders it unsuitable?"*

### Core Architectural Invariants
1. **Separation of Concerns**: Phase 10 does **NOT** simulate flooding. It consumes time-indexed flood state rasters produced by the Phase 9 Digital Twin.
2. **Canonical Time Slices**: Evaluates candidate routes across exactly **7 canonical Digital Twin time slices** ($0, 30, 60, 90, 120, 150, 180$ minutes).
3. **Canonical Coordinate System**: Route requests and candidates use `EPSG:4326` (WGS84). Distance metrics and spatial sampling use `GEOSPATIAL_ANALYSIS_CRS` (configurable UTM / EPSG:32633 for Mumbai).
4. **Provider Abstraction**: Decoupled routing engine interface (`BaseRoutingProvider`) supporting both live HTTP routing (`OSRMRoutingProvider`) and deterministic test fixture generation (`SyntheticRoutingProvider`).
5. **No Silent Synthetic Fallback**: In production-configured environments, an unavailable routing provider raises a controlled `503 Service Unavailable` status rather than silently substituting synthetic geometry.
6. **Training Label Isolation**: Phase 7 ground-truth training labels (`flood_label`, `label_status`) are strictly excluded from operational routing schemas.
7. **Prototype ML Non-Dominance**: Phase 8 prototype ML scores are tagged `PROTOTYPE_ONLY` and cannot override physical flood severity or independently determine safety recommendations.

---

## Technical Architecture & Pipeline

```
Origin + Destination
      ↓
BaseRoutingProvider (OSRM / Synthetic)
      ↓
Candidate Route Geometry (LineString EPSG:4326)
      ↓
Metric Distance Sampling (Default 100m interval)
      ↓
Phase 9 Digital Twin GeoTIFF Raster Intersection (7 Slices)
      ↓
Route Segment Severity Aggregation & Exposure Metrics
      ↓
Modeled Flood Onset Calculation (Earliest slice ≥ ROUTE_IMPACT_SEVERITY)
      ↓
Usable Travel Window Computation (Onset - Duration - Buffer)
      ↓
Deterministic Recommendation Engine (GO_NOW / ALTERNATE_RECOMMENDED / AVOID / UNKNOWN)
      ↓
Causal Human-Readable Explanation
```

---

## Key Algorithms & Formulas

### 1. Route Sampling & GeoTIFF Raster Cell Lookup
Candidate route geometry is sampled at metric distance intervals defined by `ROUTE_SAMPLE_INTERVAL_M` (default 100 meters). Each sample point undergoes spatial raster lookup using the Digital Twin GeoTIFF's actual spatial metadata:
- **Coordinate Transformation**: Route sample coordinates are provided in `EPSG:4326` (WGS84) and transformed into the Digital Twin GeoTIFF's actual target CRS (e.g. `EPSG:4326`, `EPSG:3857`, or `EPSG:32643` UTM) using `pyproj.Transformer`.
- **Affine Indexing**: Transformed coordinates $(x_{\text{raster}}, y_{\text{raster}})$ are mapped to integer raster indices $(\text{col}, \text{row})$ using the GeoTIFF dataset's actual affine transform matrix ($\sim \text{transform}$).
- **Bounds Checking**: Validates $0 \le \text{row} < \text{height}$ and $0 \le \text{col} < \text{width}$. Out-of-bounds points are classified as `UNKNOWN` (cell_id `CELL_OUT_OF_BOUNDS`) and never converted to `DRY`.
- **Nodata Checking**: Cells containing explicit GeoTIFF nodata values (e.g. `-9999.0` or `NaN`) are preserved as `UNKNOWN` and never converted to `DRY`.
- **Stable Grid Identifier**: Valid cells map to stable grid cell IDs following the `CELL_R{row:04d}_C{col:04d}` convention.

### 2. Segment Severity Aggregation
For any route segment intersecting one or more valid Digital Twin cells:
$$\text{Segment Severity} = \max_{\text{cell} \in \text{intersected}} (\text{Modeled Cell Severity})$$
Severity ordering: `DRY` < `LOW` < `MODERATE` < `HIGH` < `SEVERE`. Missing or out-of-bounds cells are preserved as `UNKNOWN` and never silently converted to `DRY`.

### 3. Modeled Flood Onset
$$\text{Onset}_{\text{min}} = \min \{ t \in \{0, 30, 60, 90, 120, 150, 180\} \mid \text{Peak Severity}(t) \ge \text{ROUTE\_IMPACT\_SEVERITY} \}$$
Default `ROUTE_IMPACT_SEVERITY` is `HIGH`. If modeled severity never reaches the impact threshold during the 180-minute horizon, $\text{Onset}_{\text{min}} = \text{null}$ (`NO_MODELED_ONSET_WITHIN_HORIZON`).

### 4. Usable Travel Window Formula
$$\text{Usable Travel Window (min)} = \max\left(0, \lfloor \text{Onset}_{\text{min}} - \text{Estimated Travel Time}_{\text{min}} - \text{Safety Buffer}_{\text{min}} \rfloor\right)$$
where:
- $\text{Estimated Travel Time}_{\text{min}} = \frac{\text{OSRM Duration (seconds)}}{60}$
- $\text{Safety Buffer}_{\text{min}} = \text{ROUTE\_SAFETY\_BUFFER\_MIN}$ (default 15 min)

### 5. Travel Window Status Classification
- `SAFE_WINDOW`: $\text{Usable Window} \ge 30$ min
- `LIMITED_WINDOW`: $0 < \text{Usable Window} < 30$ min
- `NO_SAFE_WINDOW`: $\text{Usable Window} = 0$ min
- `NO_MODELED_ONSET_WITHIN_HORIZON`: No onset within 180 min horizon
- `UNKNOWN`: Insufficient flood data or $>50\%$ unknown raster cells

### 6. Recommendation Policy
- **GO_NOW**: Usable window is sufficient ($\ge 30$ min or no modeled onset) and current exposure is acceptable.
- **ALTERNATE_RECOMMENDED**: Primary route encounters flood impact, but an alternate candidate provides a materially larger usable window.
- **AVOID**: Primary route reaches `HIGH`/`SEVERE` hazard early, leaving 0 usable travel window.
- **UNKNOWN**: Unavailable Digital Twin or missing routing data.

---

## Configuration Settings

Additions in `backend/app/core/config.py`:
- `ROUTING_PROVIDER` (default `"SYNTHETIC"`, options `"OSRM"`, `"SYNTHETIC"`)
- `ROUTING_BASE_URL` (default `"http://localhost:5000"`)
- `ROUTING_TIMEOUT_SECONDS` (default `5.0`)
- `ROUTING_MAX_ALTERNATIVES` (default `3`)
- `ROUTE_SAMPLE_INTERVAL_M` (default `100.0`)
- `ROUTE_SAFETY_BUFFER_MIN` (default `15`)
- `ROUTE_IMPACT_SEVERITY` (default `"HIGH"`)
- `ROUTE_UNKNOWN_POLICY` (default `"PRESERVE_UNKNOWN"`)

---

## Data Provenance & Limitations
- **Pilot Area**: Mithi River Catchment (Kurla / Saki Naka / Kalina / Sion corridor), Mumbai, Maharashtra.
- **Estimated Travel Time**: Travel times from OSRM or synthetic routing are labeled as *estimated routing travel time* (not live traffic).
- **Synthetic Router**: When active, responses are explicitly tagged `provider_mode = SYNTHETIC` and `environment = DEVELOPMENT_ONLY`.
- **Prototype ML**: Machine learning calibration outputs remain labeled `PROTOTYPE_ONLY — not validated probability`.
- **Disclaimer**: All route travel windows and flood onset estimates reflect modeled physical engine scenarios and do **NOT** constitute official emergency traffic management instructions.
