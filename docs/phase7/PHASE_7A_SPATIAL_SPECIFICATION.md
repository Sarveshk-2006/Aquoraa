# Phase 7A — Spatial Domain & Coordinate System Specification

## Overview

This specification establishes the exact spatial acquisition envelopes, coordinate reference systems (CRS), master computational grid alignment, and spatial downscaling semantics for the **Aquora Urban Flood Intelligence & Response Platform** in Mumbai, Maharashtra, India.

---

## 1. Spatial Domain Definitions & Acquisition Envelopes

Aquora distinguishes between two related but distinct spatial concepts:

```text
+-----------------------------------------------------------------------+
|  MITHI CATCHMENT ACQUISITION ENVELOPE (~72.95 km²)                     |
|  Bounding Box: [72.8200°E, 19.0300°N, 72.9300°E, 19.1600°N]            |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  DECISION-DOMAIN ACQUISITION ENVELOPE (Kurla Corridor ~18.5 km²)|  |
|  |  Bounding Box: [72.8400°E, 19.0400°N, 72.9000°E, 19.1200°N]    |  |
|  |  - High-impact transport infrastructure (LBS Marg, Suburban Rail)|  |
|  |  - Densely populated settlements (Kurla, Saki Naka, Sion)       |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
```

> [!IMPORTANT]
> **Spatial Boundary Rule**: A rectangular bounding box MUST NOT be referred to as "the actual Mithi catchment." Bounding boxes are designated as **Acquisition Envelopes** used to filter remote sensing tiles and satellite scenes.

### 1.1 Mithi Catchment Acquisition Envelope (Physical / Hydrologic Domain)
- **Purpose**: Captures rainfall forcing, D8 terrain flow routing, surface storage, and river channel dynamics from upstream lakes down to Mahim Creek outfall.
- **Envelope Extent (WGS 84 / EPSG:4326)**:
  - `min_longitude`: `72.8200`
  - `min_latitude`: `19.0300`
  - `max_longitude`: `72.9300`
  - `max_latitude`: `19.1600`
- **Envelope WKT**: `POLYGON((72.8200 19.0300, 72.9300 19.0300, 72.9300 19.1600, 72.8200 19.1600, 72.8200 19.0300))`
- **Catchment Polygon Status**: `CATCHMENT_POLYGON = NEEDS_VERIFICATION`. The exact hydrologic catchment boundary polygon will be derived from Phase 4 DEM pour-point delineation or verified municipal GIS in Phase 7B.

### 1.2 Decision-Domain Acquisition Envelope (Impact & ML Focus)
- **Purpose**: Primary focus for flood impact prediction, road accessibility, building inundation, railway disruption, and ML ground-truth evaluation.
- **Envelope Extent (WGS 84 / EPSG:4326)**:
  - `min_longitude`: `72.8400`
  - `min_latitude`: `19.0400`
  - `max_longitude`: `72.9000`
  - `max_latitude`: `19.1200`
- **Envelope WKT**: `POLYGON((72.8400 19.0400, 72.9000 19.0400, 72.9000 19.1200, 72.8400 19.1200, 72.8400 19.0400))`

---

## 2. Coordinate Reference System (CRS) Architecture

All spatial operations adhere strictly to Aquora's Phase 2 multi-tier CRS standards:

| Role | CRS Identifier | Description & Enforcement |
| :--- | :--- | :--- |
| **Canonical Storage CRS** | `EPSG:4326` | WGS 84 Geographic Coordinates (Degrees). Database vector features, raw rasters, and APIs store geometries in EPSG:4326. |
| **Display CRS** | `EPSG:3857` | Web Mercator (Meters). Used exclusively for web frontend tile presentation. |
| **Analysis CRS** | `EPSG:32643` (`GEOSPATIAL_ANALYSIS_CRS`) | WGS 84 / UTM Zone 43N (Meters). All metric operations (area, slope, flow accumulation, distance metrics, SAR analysis) MUST use this projection. |

> [!CAUTION]
> **CRS Enforcement**: `EPSG:32643` is loaded via project configuration (`GEOSPATIAL_ANALYSIS_CRS`). Hardcoding `EPSG:32643` into reusable algorithms is prohibited, and `EPSG:32633` MUST NOT be reintroduced.

---

## 3. Master Computational Grid & Resampling Semantics

To perform multi-layer spatial joins across heterogeneous data sources, Phase 7 establishes a **Master 30 m × 30 m Computational Grid** in `EPSG:32643`:

1. **Master Computational Grid Size**: 30m x 30m uniform cells aligned with the Copernicus DEM GLO-30 raster transform.
2. **Source Resolution Honesty**: The 30m grid is a computational feature-alignment grid. Resampling coarse data (such as NASA IMERG ~10 km precipitation) onto this grid does **NOT** manufacture street-level rainfall observations.
3. **Layer Resampling Protocol**:
   - **Copernicus DEM (30 m)**: Native resolution; defines the master raster grid transform.
   - **NASA GPM IMERG (~10 km)**: Interpolated using bilinear interpolation onto the 30m computational grid. Metadata records `source_resolution = ~10 km`, `computational_resolution = 30 m`, and `resampling_method = BILINEAR_INTERPOLATION`.
   - **ESA WorldCover (10 m)**: Categorical nearest-neighbor / modal resampling to 30m grid. Output layer named `landcover_class` (Built-up fraction derived separately as `built_up_fraction`).
   - **Sentinel-1 SAR (10 m)**: SAR calibrated products ($\gamma^0$) undergo ground-truth detection before binary/quality masks are aggregated onto the 30m master grid.
   - **OpenStreetMap Vectors**: Rasterized onto the 30m grid as density and distance metrics (`road_density`, `distance_to_road`, `distance_to_mithi`).
