# Aquora 18-Phase Implementation Roadmap

This document defines the strict phase boundaries and sequencing for the **Aquora — Urban Flood Intelligence & Response Platform**.

---

## Roadmap Matrix

| Phase | Title | Scope & Objectives | Status |
| :--- | :--- | :--- | :--- |
| **Phase 0** | **Engineering Foundation & Architecture Contract** | Repository setup, FastAPI, React/Vite, Docker, PostGIS, Redis, Audit schema, Provider/Engine interfaces, Docs, Tests. | **COMPLETED** |
| **Phase 1** | **Repository + Infrastructure Foundation** | Versioned API (/api/v1), Liveness/Readiness endpoints, Request ID correlation, Error handling, Query foundation, CI workflow. | **COMPLETED** |
| **Phase 2** | **Geospatial Data Foundation** | PostGIS spatial tables (study_areas, raster_metadata, vector_features), CRS strategy (Canonical 4326, Display 3857, Configurable Analysis CRS), PyProj/Shapely/Rasterio/GeoPandas utilities, Spatial provider contracts, Audit/Provenance metadata. | **COMPLETED** |
| **Phase 3** | **Rainfall + Forecast Data Pipeline** | Rainfall observation provider (NASA GPM IMERG V07B), forecast provider (0-3h lead time horizon), canonical accumulation vs intensity semantics, quality status flags (VALID, MISSING, INVALID, SUSPECT, NODATA), PostGIS tables (rainfall_observation_grids, rainfall_forecast_grids, ingestion_runs), Alembic migration 0003_phase3_rainfall.py, ingestion services, dev verification APIs. | **COMPLETED** |
| **Phase 4** | **Terrain / Catchment / Surface-Flow Engine** | Digital Elevation Model (DEM) validation, slope, aspect, D8 downslope flow direction, D8 flow accumulation, DEM-derived surface drainage proxy, pour-point catchment delineation, metric area calculation, processing runs audit. | **COMPLETED** |
| **Phase 5** | **Drainage Network Engine** | Base drainage provider, synthetic test fixtures, geometry validation, controlled spatial snapping, node/link domain models, topology validation (orphan/loop/missing endpoint detection), directed graph construction, upstream/downstream BFS traversals, outfall reachability, connected components discovery, capacity metadata (explicit UNKNOWN status), Phase 4 catchment association, PostGIS models/migrations, dev verification APIs. | **COMPLETED** |
| **Phase 6** | **Flood Simulation Engine** | Deterministic physical simulation engine (engines/flood/), rainfall-runoff generation, cell surface storage, Phase 4 D8 surface routing, Phase 5 municipal drainage coupling, known capacity bounds, unknown capacity/direction policies, mass balance conservation verification (Invariants 1-14), depth severity classification, onset & peak state trackers, input completeness metrics, PostGIS models/migrations, developer HTTP APIs. | **IMPLEMENTED — PENDING REVIEW** |
| **Phase 7A** | **MUMBAI EVENT + DATA ACQUISITION SPECIFICATION** | Historical Mumbai event evaluation, source catalog, spatial/temporal/label specifications, download manifest. | **IMPLEMENTED — PENDING REVIEW** |
| **Phase 7B** | **REAL DATA ACQUISITION + VERIFICATION** | Source verification, public data acquisition, cryptographic hash checking (SHA-256), provenance registration. | **IMPLEMENTED — PENDING REVIEW** |
| **Phase 8** | **ML Calibration + 0–3h Nowcast** | Physics-guided ML residual calibration, real-time nowcast engine. | Pending |
| **Phase 9** | **Flood Digital Twin + Future Flood Map** | Dynamic inundation visualization UI, 7 canonical slices (0, 30, 60, 90, 120, 150, 180 min), GeoTIFF map artifacts. | **COMPLETED** |
| **Phase 10** | **Flood-Aware Routing + Travel Window** | Dynamic safe route calculation, route exposure timeline, flood onset, travel window estimation. | **COMPLETED** |
| **Phase 11** | **Critical Access Guardian** | Hospital & critical facility accessibility monitoring, 7-slice loss-of-access timeline, alternate access selection. | **COMPLETED** |
| **Phase 12** | **Protect the City** | Decision support & intervention prioritization, controlled taxonomy, decomposable priority breakdown, cause-chain explanation. | **COMPLETED** |
| **Phase 13** | **Ground Truth + Photo Verification** | Citizen report submission UI, geotagged photo metadata validation, incident clustering, Digital Twin slice comparison, multi-source verification state rules. | **COMPLETED** |
| **Phase 14** | **Aquora Simulator** | Interactive what-if hydro-simulation sandbox, scenario taxonomy, baseline immutability, Phase 6 solver integration, delta comparisons, outcome classification, provenance audit. | **COMPLETED WITH LIMITATIONS** |
| **Phase 15** | **Alerts + Explainability + Audit** | Automated decision & notification layer, operational alert taxonomy, severity mapping, continuing-condition deduplication, structured cause-chain explainability, compact evidence references, lifecycle state audit trail. | **IMPLEMENTED — PENDING REVIEW** |
| **Phase 16** | **Testing + Validation** | End-to-end integration tests, hydrodynamic benchmarking, load testing. | Pending |
| **Phase 17** | **Production Deployment** | Cloud infrastructure provisioning, SSL/TLS, auto-scaling worker groups. | Pending |
| **Phase 18** | **Final Hackathon Demo / Polish** | Product demo video, presentation dashboard polish, final release build. | Pending |

---

## Strict Rule of Execution

> **No phase may be started out of order or bypass prior phase verification.**
