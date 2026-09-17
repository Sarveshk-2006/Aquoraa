# AQUORA — GEOSPATIAL DATA FOUNDATION ARCHITECTURE (PHASE 2)

## 1. Executive Summary

Phase 2 establishes the core spatial foundation for **AQUORA — Urban Flood Intelligence & Response Platform**.

The architecture establishes unified coordinate reference system (CRS) management, geometric validation, PostGIS spatial persistence models, vendor-neutral provider interfaces, and raster/vector utility modules.

Following the core AQUORA engineering philosophy:

> **Physics/GIS first → ML calibration second → ground-truth feedback third.**

Phase 2 provides pure spatial infrastructure without implementing flood-domain calculation logic, hydrology, DEM slope analysis, or external data downloads.

---

## 2. CRS Strategy & Architecture

Aquora enforces a strict three-role CRS strategy managed centrally by `app.geospatial.crs.CRSManager`:

```
   +--------------------------------------------------------+
   |                  CANONICAL CRS                         |
   |                   EPSG:4326                            |
   |    (Geographic Coordinate Interchange & Storage)       |
   +--------------------------------------------------------+
              ^                                  ^
              |                                  |
              v                                  v
+---------------------------+      +---------------------------+
|        DISPLAY CRS        |      |       ANALYSIS CRS        |
|         EPSG:3857         |      |       CONFIGURABLE        |
|    (Web Map Rendering)    |      | (e.g. EPSG:32633 for test)|
+---------------------------+      +---------------------------+
```

### 2.1 Canonical CRS (`EPSG:4326`)
- **Role**: Standard WGS 84 geographic coordinate system (latitude / longitude in degrees).
- **Usage**: External API interchange, GeoJSON formats, authoritative storage in PostGIS geometry columns.
- **Rule**: Direct spatial distance, area, slope, or volume calculations in `EPSG:4326` are strictly prohibited due to angular degree distortion.

### 2.2 Display CRS (`EPSG:3857`)
- **Role**: Web Mercator planar projection.
- **Usage**: Display rendering on web maps (Leaflet / Mapbox / OpenLayers UI clients).
- **Rule**: Must not be used for scientific analysis or hydraulic calculations due to severe area scale distortion near non-equatorial latitudes.

### 2.3 Analysis CRS (`GEOSPATIAL_ANALYSIS_CRS`) — Configurable
- **Role**: Projected metric CRS (Easting/Northing in meters).
- **Usage**: Scientific spatial analysis, distance buffering, cell resolution, and future hydraulic solver grids.
- **Critical Architectural Requirement**: `GEOSPATIAL_ANALYSIS_CRS` is **CONFIGURABLE** via environment configuration (`GEOSPATIAL_ANALYSIS_CRS`).
- **City-Agnostic Design**: `EPSG:32633` (UTM Zone 33N) is used ONLY as a development/test fixture default and is **NOT** a hard-coded project-wide pilot CRS.

---

## 3. PostGIS Schema & Persistence

Phase 2 introduces Alembic migration `0002_phase2_geospatial.py` creating PostGIS spatial tables:

### 3.1 `study_areas`
- **Purpose**: Defines spatial boundaries for study areas, cities, pilot zones, or catchments.
- **Columns**: `id` (UUID), `name`, `description`, `geom` (`Geometry(POLYGON, 4326)`), `srid`, `provenance` (`JSONB`), `created_at`, `updated_at`.
- **Index**: GiST spatial index `idx_study_areas_geom` on `geom`.

### 3.2 `raster_metadata`
- **Purpose**: Structural registry for future elevation (DEM), land-cover, and satellite rasters.
- **Columns**: `id`, `dataset_identifier`, `source`, `crs`, `geom_bounds` (`Geometry(POLYGON, 4326)`), `resolution_x`, `resolution_y`, `width`, `height`, `nodata`, `units`, `provenance` (`JSONB`), `storage_pointer`.
- **Index**: GiST spatial index `idx_raster_metadata_geom_bounds` on `geom_bounds`.

### 3.3 `vector_features`
- **Purpose**: Generic PostGIS store for urban vector infrastructure (roads, buildings, POIs).
- **Columns**: `id`, `category`, `geom` (`Geometry(GEOMETRY, 4326)`), `srid`, `feature_properties` (`JSONB`), `provenance` (`JSONB`), `created_at`.
- **Index**: GiST spatial index `idx_vector_features_geom` on `geom`.

---

## 4. Geospatial Utilities

- `app.geospatial.crs.CRSManager`: Centralized PyProj coordinate transformations and CRS validation.
- `app.geospatial.validation`: `validate_geometry`, `ensure_valid_polygon` (with controlled `make_valid` repair logging), `check_srid`, `validate_bbox`.
- `app.geospatial.vector`: Bounding box extraction, envelope generation, Shapely / GeoPandas reprojection, spatial intersection and containment.
- `app.geospatial.raster`: Rasterio metadata extraction, affine transform matrix handling, coordinate-to-pixel and pixel-to-coordinate calculations.

---

## 5. Vendor-Neutral Provider Contracts

Abstract interfaces defined in `app.providers.spatial`:
- `BaseTerrainProvider`: Contract for future DEM access (`get_metadata`, `check_coverage`).
- `BaseLandCoverProvider`: Contract for future surface roughness and imperviousness datasets.
- `BaseUrbanVectorProvider`: Contract for future urban vector datasets (roads, buildings, POIs).

**Rule**: No real external API requests (NASA, USGS, OSM, Copernicus) are connected in Phase 2.

---

## 6. OpenStreetMap (OSM) Licensing & Attribution Compliance

If OpenStreetMap data is integrated in future phases:
- Full compliance with the **Open Database License (ODbL)** must be enforced.
- Attribution (`© OpenStreetMap contributors`) must be displayed on UI map views.
- Authoritative municipal GIS datasets must remain supported as alternative vector providers.

---

## 7. Hard Scope Boundary Confirmation

Phase 2 explicitly **EXCLUDES**:
- NASA / IMERG / Real rainfall downloads or forecasts
- Kaggle datasets, ML model training, inference, or calibration
- SCS-CN runoff, hydrology, slope/aspect/flow accumulation calculations
- Catchment delineation, drainage hydraulic solvers, 2D shallow-water flood simulation
- Critical access routing, travel window calculations, citizen reports, computer vision, satellite flood detection, alerts, or simulator logic.
