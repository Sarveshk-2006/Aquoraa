# Aquora Planned Data Sources Specification

> **Phase 0 Notice**: No real external data feeds or API keys are active in Phase 0. This document defines the data catalog for future phases.

---

## Data Categories & Sources Matrix

| Category | Primary Sources | Update Frequency | Purpose / Use Case | Phase Introduced |
| :--- | :--- | :--- | :--- | :--- |
| **Rainfall Observations** | NASA GPM IMERG V07B (Final/Late/Early) | 30 minutes | Precipitation observation / estimation (~0.1° resolution) | Phase 3 (Active) |
| **Rainfall Forecasts** | Short-Term NWP / Nowcast Provider | 15 - 30 minutes | 0–3 hour precipitation projection ($T_0, T_{valid}, \Delta t$) | Phase 3 (Active) |
| **Terrain & DEM** | Copernicus DEM / USGS 30m/10m | Static | Catchment delineation, surface slopes | Phase 2 (Active) |
| **Land Cover & Soil** | Copernicus / ESA WorldCover | Static | Infiltration rates, Curve Number (CN) | Phase 2 (Active) |
| **Road Networks** | OpenStreetMap (OSM) / Municipal GIS | Static / Periodic | Routing, travel window, critical access | Phase 2 (Active) |
| **Building Footprints** | OSM / Municipal Footprints | Static / Periodic | Building inundation risk & exposure | Phase 2 (Active) |
| **Drainage Network** | Municipal GIS Open Data | Static | Storm drain inlet, pipe capacity, surcharge | Phase 5 |
| **Satellite Imagery** | Sentinel-1 / Sentinel-2 | 5-day revisit | Flood extent calibration & verification | Phase 2/13 |
| **Community Observations** | Aquora Ground Truth App | Real-time | Photo verification, water level validation | Phase 13 |

---

## Ingestion & Processing Pipeline (Planned)

```text
External Provider API
       │
       ▼
Raw Data Ingestion (data/raw)
       │
       ▼
Spatial / Temporal Normalization (data/processed)
       │
       ▼
Engine Input Payload / PostGIS Storage
```
