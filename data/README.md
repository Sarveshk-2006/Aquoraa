# Data Storage Directory

> **Phase 0 Status**: Real training, event, and GIS datasets are intentionally introduced in Phase 7. No real or synthetic flood dataset is stored here during Phase 0.

## Directory Layout
- `data/raw/`: Raw external API payloads, radar files, and unprojected DEM rasters.
- `data/processed/`: Normalized PostGIS-ready geometries, spatial grids, and feature arrays.
- `data/sample/`: Minimal non-production test fixtures strictly for automated test suites.
