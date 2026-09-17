# AQUORA — Phase 5 Drainage Network Engine

## Overview & Purpose

The **Drainage Network Engine** (Phase 5) models, validates, and analyzes urban drainage infrastructure within the AQUORA platform. 

While Phase 4 answers *"Where does water naturally want to move over terrain?"*, Phase 5 answers:
> **"What drainage infrastructure exists, what are its connections, and what infrastructure metadata is known?"**

### Mandatory Disclaimer Statements

> **IMPORTANT DISCLAIMERS**:
> - **Phase 5 represents and analyzes drainage infrastructure; it does not simulate hydraulic flooding.**
> - **DEM-derived surface drainage proxies are not municipal drainage infrastructure.**
> - **Missing infrastructure attributes remain UNKNOWN rather than being fabricated.**
> - **Unknown link direction is not silently inferred from geometry or terrain.**
> - **Phase 5 does not convert rainfall into runoff.**

---

## Architecture & Provider Abstraction

The drainage engine separates data ingestion, spatial/topological normalization, and graph traversal algorithms into modular components.

```text
Drainage Data Source (GeoPackage, GeoJSON, Shapefile, Synthetic)
            ↓
    BaseDrainageProvider
    ├── SyntheticDrainageProvider (TEST FIXTURE ONLY)
    └── LocalDrainageProvider (File-backed)
            ↓
    Drainage Processing Pipeline
    ├── Geometry Validation (Point nodes, LineString links)
    ├── Controlled Spatial Snapping (Metric Analysis CRS)
    ├── Topology Validation (Orphan, Self-Loop, Duplicate ID checks)
    ├── Directed Graph Construction (Adjacency & Reverse Adjacency)
    ├── Reachability & Component Analysis (Upstream, Downstream, Outfalls)
    └── Phase 4 Catchment Association (Proximity / Containment)
            ↓
    PostGIS Persistence & Provenance Metadata
```

---

## Canonical Data Model

### Node Model (`DrainageNode`)
- `node_id`: Unique identifier
- `node_type`: `INLET`, `CATCH_BASIN`, `MANHOLE`, `JUNCTION`, `OUTFALL`, `STORAGE`, `PUMP_STATION`, `OTHER`
- `geometry`: Point in `EPSG:4326`
- `elevation_m` / `invert_elevation_m` / `ground_elevation_m`: Known elevations in meters or `None`
- `confidence`: `AUTHORITATIVE`, `OFFICIAL_OPEN_DATA`, `VERIFIED_MAPPED`, `DERIVED`, `SYNTHETIC`, `UNKNOWN`
- `quality_flags`: List of quality tags (`VALID`, `ORPHAN`, `DISCONNECTED`, etc.)
- `provenance`: Ingestion and source lineage metadata

### Link Model (`DrainageLink`)
- `link_id`: Unique identifier
- `from_node_id` / `to_node_id`: Start and end node references
- `link_type`: `PIPE`, `CONDUIT`, `OPEN_CHANNEL`, `CULVERT`, `DITCH`, `OTHER`
- `geometry`: LineString in `EPSG:4326`
- `length_m`: Calculated horizontal metric length
- `diameter_m` / `width_m` / `height_m`: Physical dimensions in meters or `None`
- `capacity_m3s`: Known flow capacity ($m^3/s$) or `None` (`capacity_status = UNKNOWN`)
- `direction_status`: `KNOWN` or `UNKNOWN`
- `confidence` & `quality_flags`: Quality flags and provenance

---

## CRS Policy

1. **Canonical Storage CRS**: `EPSG:4326` (WGS84 lat/lon) for all database geometries.
2. **Display CRS**: `EPSG:3857` (Web Mercator) for client map visualization.
3. **Metric Analysis CRS**: `GEOSPATIAL_ANALYSIS_CRS` (e.g. `EPSG:32633` projected UTM). 
   - All spatial snapping tolerances (`DRAINAGE_SNAP_TOLERANCE_M`), link length calculations, metric distances, and catchment association tolerances (`DRAINAGE_CATCHMENT_ASSOCIATION_TOLERANCE_M`) use project metric coordinates.
   - **Never hard-coded**: `EPSG:32633` is a configurable default, not a universal physical assumption.

---

## Topology Validation & Controlled Spatial Snapping

### Spatial Snapping
- Snapping projects node and link endpoints into the metric Analysis CRS.
- Snaps node coordinates to candidate link endpoints within `DRAINAGE_SNAP_TOLERANCE_M` (default 5.0m).
- Snapping provenance records `original_geometry`, `snapped_geometry`, `snap_distance_m`, and `snap_status` (`SNAPPED`, `NOT_SNAPPED`, `NOT_SNAPPED_OUTSIDE_TOLERANCE`).

### Topology Validation
Validates network consistency and assigns quality flags:
- `MISSING_ENDPOINT`: Link references a non-existent node ID.
- `ORPHAN`: Asset has no valid topological connections.
- `SELF_LOOP`: Link starting and ending at the same node.
- `DISCONNECTED`: Asset belongs to an isolated network component.
- `UNKNOWN_DIRECTION`: Directionality unavailable in source data.
- `UNKNOWN_CAPACITY`: Hydraulic capacity unavailable in source data.

---

## Graph Traversal Algorithms

The internal directed graph maintains adjacency (`adj`) and reverse adjacency (`rev_adj`) lists:

1. **Downstream Traversal (`get_downstream_nodes`)**: Breadth-First Search (BFS) following directed links ($A \to B \to C$).
2. **Upstream Traversal (`get_upstream_nodes`)**: BFS following reverse adjacency to find contributing sub-networks.
3. **Outfall Reachability (`can_reach_outfall`)**: Checks if a node can reach an explicit `OUTFALL` node.
4. **Connected Components (`find_connected_components`)**: Discovers weakly connected network sub-graphs with deterministic ordering.

---

## Phase 4 Catchment Association

Associates Phase 4 terrain catchments with candidate drainage inlets:
1. Checks spatial containment (catchment polygon containing inlet point).
2. If uncontained, checks proximity within `DRAINAGE_CATCHMENT_ASSOCIATION_TOLERANCE_M` (default 200.0m).
3. If multiple equidistant nodes exist within tolerance, marks status as `AMBIGUOUS` rather than guessing.
4. If no candidate node exists within tolerance, leaves catchment as `UNASSOCIATED`.

---

## Scope Boundaries & Limitations

- **No Flood Solver**: Phase 5 does not compute water depth, surface pressure, 1D/2D hydrodynamic equations, or inundation.
- **No Hydrologic Runoff**: Phase 5 does not execute SCS-CN, infiltration, or hydrograph routing.
- **No Machine Learning**: No ML calibrations, XGBoost, or scikit-learn models.
- **No Ground-Truth / Alerts**: Citizen reports, CV, satellite imagery, and dispatch routing remain in future phases.
