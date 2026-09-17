# AQUORA — Phase 9 Digital Twin & Future Flood Map Specification

## 1. Overview & Core Architecture
Phase 9 connects the physical flood simulation pipeline into a time-indexed Digital Twin and exposes it through the Future Flood Map UI for the Mumbai Mithi River urban catchment pilot (Kurla / Saki Naka / Kalina / Sion corridor).

```
Phase 3 Rainfall/Forecast
           ↓
Phase 4 Terrain/Surface Flow
           ↓
Phase 5 Drainage Network
           ↓
Phase 6 Deterministic Flood Simulation Engine (PRIMARY PHYSICAL SOURCE)
           ↓
Phase 9 Digital Twin Orchestration Service
           ↓
Compact Map Raster Artifacts & Time-Slice Summaries
           ↓
FastAPI /api/v1/digital-twin Router
           ↓
Future Flood Map Frontend (React + MapLibre GL JS)
```

---

## 2. Scientific & Architectural Rules

1. **Primary Physical Source**: Phase 6 deterministic flood simulation is the single primary physical source. Phase 9 orchestrates Phase 6 outputs and does not duplicate hydrological solvers.
2. **Phase 8 ML Calibration Signal**: `prototype_ml_score` is strictly tagged as `PROTOTYPE_ONLY`. It is NOT a validated, operational, or emergency flood probability. The Digital Twin remains operational even if ML artifacts are omitted.
3. **Map Delivery Architecture**:
   - **OLD**: Per-cell GeoJSON files containing individual features for all 186k grid cells.
   - **NEW**: Compact file-backed GeoTIFF raster map artifacts (`map/slice_000.tif` ... `map/slice_180.tif`) and time-slice summary JSON files (`summary/slice_000.json` ... `summary/slice_180.json`).
4. **Resolution Semantics**: 30m is the projected spatial computational grid resolution for terrain/surface-flow analysis, NOT the native rainfall observation/forecast resolution.
5. **Honest Input Provenance**:
   - Rainfall: `SYNTHETIC_IMERG_PROTOTYPE (DEVELOPMENT SCENARIO)`
   - Forecast: `SYNTHETIC_0_3H_HORIZON (DEVELOPMENT FORECAST)`
   - Terrain: `FABDEM 30m (DEM-derived terrain)`
   - Drainage: `OSM Storm Drain Proxy (Non-authoritative municipal network proxy)`
   - Physical Engine: `Phase 6 Deterministic D8 Solver v1.0`
6. **Non-Authoritative Municipal Data**: OSM-derived stormwater drainage is a synthetic/spatial proxy and must not be presented as authoritative municipal drainage capacity.
7. **Severity Semantics**: Inundation severity thresholds (`DRY`, `LOW`, `MODERATE`, `HIGH`, `SEVERE`) are inherited directly from Phase 6. They are not official emergency warning levels.
8. **Operational Disclaimer**: The Digital Twin is modelled flood intelligence, NOT an official emergency warning system.
9. **Training Label Isolation**: Operational APIs and frontend inspection cards strictly omit Phase 7 target/label fields (`flood_label`, `label_status`, `evidence_source`, etc.).
10. **PostGIS Verification Status**: PostGIS runtime validation is `BLOCKED-EXTERNAL` due to Docker Hub TLS registry pull restrictions on the host environment; in-memory/file-backed SQLite/JSON persistence fallback is active and 100% verified.
