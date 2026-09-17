# AQUORA — TERRAIN / CATCHMENT / SURFACE-FLOW ENGINE (PHASE 4)

## 1. Executive Purpose
The **Terrain & Surface-Flow Engine** establishes the DEM-derived physical structure required for AQUORA's multi-scale urban flood modeling. It processes digital elevation models (DEM) into terrain derivatives, D8 flow direction, upstream flow accumulation, DEM-derived surface drainage proxies, and pour-point catchments.

---

## 2. Core AQUORA Scientific Principle & Hard Scope Boundary

> **Physics/GIS first → ML calibration second → ground-truth feedback third.**

Phase 4 operates strictly at the **PHYSICS / GIS FIRST** layer.

### Explicit Scope Boundaries & Disclaimers
- **Flow accumulation is NOT runoff or discharge.** Flow accumulation represents upstream contributing-cell count topology, NOT volumetric water flow ($m^3/s$) or surface runoff depth.
- **The DEM-derived surface drainage proxy is NOT a municipal drainage network.** It indicates terrain surface flow paths derived purely from elevation, NOT underground storm sewer pipes, culverts, or manholes.
- **A terrain-derived catchment is NOT automatically a municipal stormwater catchment.** It represents topographic upstream contributing area, NOT municipal sewer service districts or pipe network catchments.
- **Phase 4 does NOT calculate rainfall-runoff transformation.** Phase 4 does NOT use SCS Curve Number, green-ampt infiltration, or rainfall input.
- **Phase 4 does NOT compute flood depth or flood extent.** No 1D/2D shallow-water hydraulic simulation or ML flood NOWCAST predictions are executed in Phase 4.

---

## 3. Terrain Processing Pipeline Architecture

```text
DEM (Synthetic / Local GeoTIFF)
 ↓
DEM Validation & Metadata Extraction
 ↓
Projected Metric Analysis CRS Transformation (e.g., EPSG:32633)
 ↓
Terrain Derivatives
 ├── Slope (degrees [0, 90°])
 └── Aspect (compass degrees [0, 360°], flat = -1.0)
 ↓
D8 Flow Direction Algorithm (cardinal & diagonal slope distance weighting)
 ↓
D8 Flow Accumulation (topological upstream cell accumulation)
 ↓
DEM-Derived Surface Drainage Proxy (resolution-aware threshold area m2)
 ↓
Pour-Point Catchment Delineation (snapping & upstream cell tracing)
 ↓
Validated Vector Geometries & Audit Lineage Persistence
```

---

## 4. Terrain Algorithms & Semantics

### 4.1 Slope
- **Algorithm:** 2nd-order central finite-difference method (`np.gradient`).
- **Units:** Degrees $[0^\circ, 90^\circ]$.
- **Distance Rule:** Uses exact metric grid cell spacing ($dx, dy$) in projected Analysis CRS (meters). Geographic degree coordinates are NEVER used directly for metric distance calculations.

### 4.2 Aspect
- **Convention:** Compass orientation in degrees $[0^\circ, 360^\circ]$ clockwise from North ($0^\circ/360^\circ = \text{North}, 90^\circ = \text{East}, 180^\circ = \text{South}, 270^\circ = \text{West}$).
- **Flat Region Behavior:** Flat cells ($\nabla z = 0$) are assigned $-1.0$ (undefined aspect).

### 4.3 D8 Flow Direction
- **Encoding:** ESRI D8 standard directional bitmasks:
  - 1: East, 2: Southeast, 4: South, 8: Southwest, 16: West, 32: Northwest, 64: North, 128: Northeast.
- **Distance Handling:** Cardinal neighbor distance = $dx$, Diagonal neighbor distance = $\sqrt{dx^2 + dy^2}$.
- **Drop Rule:** Selects neighbor maximizing positive slope drop:
  $$\text{Drop} = \frac{z_{\text{center}} - z_{\text{neighbor}}}{\text{distance}}$$
- **Sinks / Flats:** Cells with no lower neighbor are assigned $0$ ($\text{SINK} / \text{NO\_FLOW}$).

### 4.4 Flow Accumulation
- **Meaning:** Upstream cell count accumulation (monotonically non-decreasing along valid downstream flow paths).
- **Execution:** Headwater queue topological sorting based on D8 flow direction topology.

### 4.5 Surface Drainage Proxy
- **Threshold Rule:** Derived cell threshold = $\lceil \text{threshold\_area\_m2} / (dx \times dy) \rceil$.
- **Configurable Settings:** `SURFACE_DRAINAGE_THRESHOLD_AREA_M2` (Default: $10,000\,\text{m}^2$).

### 4.6 Catchment Delineation
- **Pour-Point Snapping:** Optional snapping within radius `CATCHMENT_SNAP_TOLERANCE_M` (Default: $100\,\text{m}$) to cell of maximum flow accumulation.
- **Upstream Traversal:** BFS/DFS reverse D8 lookup.
- **Geometry Validation:** Polygonized via `rasterio.features.shapes` and validated via `ensure_valid_polygon`. Area computed in metric units ($m^2$).

---

## 5. System Configuration

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `GEOSPATIAL_ANALYSIS_CRS` | `str` | `"EPSG:32633"` | Projected metric Analysis CRS for planar spatial calculations |
| `DEM_RAW_DATA_PATH` | `str` | `"data/raw/dem"` | Storage path for raw DEM rasters |
| `DEM_PROCESSED_DATA_PATH` | `str` | `"data/processed/dem"` | Storage path for derivative raster artifacts |
| `SURFACE_DRAINAGE_THRESHOLD_AREA_M2` | `float` | `10000.0` | Threshold area ($m^2$) for surface drainage proxy extraction |
| `CATCHMENT_SNAP_TOLERANCE_M` | `float` | `100.0` | Pour-point snapping distance tolerance ($m$) |

---

## 6. Verification & Test Suite
- **Synthetic Fixtures:** Explicitly labeled `TEST FIXTURE ONLY` (`flat_plane`, `inclined_plane`, `v_valley`, `sink_depression`).
- **Tests:** 45 backend unit/integration tests passing (DEM validation, slope, aspect, D8 direction/accumulation, drainage proxy, catchment delineation, API endpoints, invariant boundary assertions).
- **Frontend Build:** `tsc --noEmit` and `vite build` clean passing.
